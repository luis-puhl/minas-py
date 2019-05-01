import itertools as intertools
import time, sys, traceback
from typing import List

import pandas as pd
import numpy as np
import scipy as scipy
import sklearn as sk
from sklearn.cluster import KMeans
from sklearn.externals import joblib

import self_test as self_test

from inspect import currentframe

def get_linenumber():
  cf = currentframe()
  return cf.f_back.f_lineno
def print_log(*args, **kwargs):
  line = currentframe().f_back.f_lineno
  args = ('{file}:{line}'.format(file=__file__, line=line), ) + args
  print(*args, **kwargs)

class Example:
  __slots__ = ['label', 'item', 'timestamp', 'classificationTries']
  def __init__(self, label=None, item: List[float]=[]):
    self.label = label
    self.item = item
    self.timestamp = time.time()
    self.classificationTries = 0
  def asDict(self):
    return {
      'label': self.label,
      'len': len(self.item),
      # 'item': self.item,
      'timestamp': self.timestamp,
      'classificationTries': self.classificationTries,
    }
  def __str__(self):
    return '[Ex]' + '\t'.join('{k}: {v}'.format(k=k, v=v) for k, v in self.asDict().items())
  def __repr__(self):
    return self.__str__()
  def __len__(self):
    return len(self.item)

class Cluster:
  """Cluster class holds and updates
    From \cite{Faria2015}:
    > Each micro-cluster is composed of four components:
    >   N number of examples,
    >   LS linear sum of the examples,
    >   SS squared sum of the elements and[,]
    >   T timestamp of the arrival of the last example classified in this micro-cluster.
    > Using these measures it is possible to calculate the centroid and radio of a micro-cluster (Zhang et al. 1996).
    > [...]
    > each micro-cluster is represented by four components (N, LS, SS and T).
    > Each micro-cluster is labeled to indicate to which class it belongs.
    > Thus, the decision boundary of each class is defined by the union of its k micro-cluster.
    > The initial decision model is composed of the union of the k micro-clusters obtained for each class.

    From MINAS-SourceCode, `Cluster.java` is a bag:
    ```java
    public class Cluster {
      private double meanDistance;
      private double[] center;
      private double size;
      private double radius;
      private String lblClasse;
      private String category;
      private int time;
    ```
    Also, from `KMeansMOAModified.java`:
    ```java
    // centers = cm.kMeans2(initialCenters, elemList, soma, clusterSize, elemCluster, radius, meanDistance);
    public Clustering kMeans2(
      Cluster[] centers, List<? extends Cluster> data, double soma[],
      ArrayList<Integer> clusterSize, int elemCluster[], ArrayList<Double> maxDistance,
      ArrayList<Double> meanDistance) {
    ```
    So, radius is renamed as maxDistance.
  """
  # ------------------------------------------------------------------------------------------------
  # N number of examples,
  label = ''
  center = np.array([])
  counter = 0
  lastExapleTMS = -float("inf")
  # statistic summary
  sumDistance = 0.0
  meanDistance = 0.0
  maxDistance = 0.0
  def __init(self):
    self.label = ''
    self.center = np.array([])
    self.counter = 0
    self.lastExapleTMS = -float("inf")
    self.sumDistance = 0.0
    self.meanDistance = 0.0
    self.maxDistance = 0.0
  def __str__(self):
    return '[{label}]\tn={count}\tc={c},\tr={r:2.2f}'.format(
      label=self.label,
      count=self.counter,
      c=', '.join(['{:2.2f}'.format(c) for c in self.center]),
      r=self.radius()
    )
  def __repr__(self):
    return self.__str__()
  def asDic(self):
    return {k: getattr(self, k) for k in self.__slots__}
  def radius(self):
    return self.maxDistance
  def dist(self, vec: List[float] = []):
    return scipy.spatial.distance.euclidean(self.center, vec)
  def addExample(self, example, distance=None):
    self.counter += 1
    if example.timestamp > self.lastExapleTMS:
      self.lastExapleTMS = example.timestamp
    if distance == None:
      distance = self.dist(example.item)
    self.sumDistance += distance
    self.meanDistance = self.sumDistance / self.counter
    if distance > self.maxDistance:
      self.maxDistance = distance

class Minas:
  # CONSTS
  k = 100
  radiusFactor = 1.1
  noveltyThr = 100
  windowTimeSize = 100
  ndProcedureThr = 2000
  representationThr = 3
  globalCount = 0
  lastExapleTMS = -float("inf")
  lastCleaningCycle = -float("inf")
  clusters: List[Cluster] = []
  sleepClusters: List[Cluster] = []
  counter = 0
  unknownBuffer: List[Example] = []
  noveltyIndex = 0
  def __init__(self):
    self.k = 100
    self.radiusFactor = 1.1
    self.noveltyThr = 100
    self.windowTimeSize = 100
    self.ndProcedureThr = 2000
    self.representationThr = 3
    self.globalCount = 0
    self.lastExapleTMS = -float("inf")
    self.lastCleaningCycle = -float("inf")
    self.clusters = []
    self.sleepClusters = []
    self.counter = 0
    self.unknownBuffer = []
    self.noveltyIndex = 0
    print_log('Model.__init__', self)
  # ------------------------------------------------------------------------------------------------
  def asDict(self):
    return {
      'k': self.k,
      'radiusFactor': self.radiusFactor,
      'noveltyThr': self.noveltyThr,
      'windowTimeSize': self.windowTimeSize,
      'ndProcedureThr': self.ndProcedureThr,
      'representationThr': self.representationThr,
      'globalCount': self.globalCount,
      'lastExapleTMS': self.lastExapleTMS,
      'lastCleaningCycle': self.lastCleaningCycle,
      'clusters': self.clusters,
      'sleepClusters': self.sleepClusters,
      'counter': self.counter,
      'unknownBuffer': self.unknownBuffer,
      'noveltyIndex': self.noveltyIndex,
      'clusters': len(self.clusters),
      'sleepers': len(self.sleepClusters),
      'u': len(self.unknownBuffer),
      'diff': self.globalCount-self.counter,
      'known': self.counter,
    }
  def __str__(self):
    constants = ', '.join([str(k) + ': ' + str(v) for k, v in self.asDict().items()])
    return 'Model({constants} => {model})({cls}\n)'.format(
      constants=constants,
      model=self.statusStr(),
      ncls=len(self.clusters),
      cls=''.join(['\n\t' + str(c) for c in self.clusters])
    )
  def __repr__(self):
    return self.__str__()
  def statusStr(self):
    return 'clusters: {clusters}, sleepers: {sleepers}, known: {known}, unkown: {u} ({diff}), total={globalCount}'.format(
      clusters=len(self.clusters), sleepers=len(self.sleepClusters),
      known=self.counter, u=len(self.unknownBuffer), diff=self.globalCount-self.counter, globalCount=self.globalCount
    )
  def clustering(self, examples):
    """
    After the execution of the clustering algorithm, each micro-cluster is represented
    by four components (N, LS, SS and T).
    """
    print_log('clustering', len(examples), examples[0])
    assert len(examples) > 0
    
    n_samples = len(examples)
    n_clusters = min(self.k, int(n_samples / (3 * self.representationThr)))
    # by 2, so at least 2 examples per cluster
    # if n_samples < n_clusters / 2:
    #   n_clusters = int(n_samples / 10)
    assert n_samples >= n_clusters
    df = pd.DataFrame(data=[ex.item for ex in examples])
    kmeans = KMeans(n_clusters=n_clusters)
    try:
      with joblib.parallel_backend('dask'):
        kmeans.fit(df)
    except Exception as exc:
      print_log('\n------------------------ Exception ------------------------')
      print_log(exc)
      print_log(df)
      raise RuntimeError('Minas Clustering Error') from exc

    clusters = []
    for centroid in kmeans.cluster_centers_:
      c = Cluster()
      c.center = centroid
      clusters.append(c)
    # Add examples to its cluster
    for ex in examples:
      dist = float("inf")
      nearCl = None
      for cl in clusters:
        d = cl.dist(ex.item)
        if d < dist:
          dist = d
          nearCl = cl
      if nearCl:
        nearCl.addExample(ex)
    return clusters
  #
  def validationCriterion(self, cluster: Cluster, unknownBuffer):
    isRepresentative = cluster.counter > self.representationThr
    # 
    near, dist = self.closestCluster(cluster.center)
    silhouette = lambda a, b: (b - a) / max([a, b])
    distances = []
    for ex in unknownBuffer:
      d = cluster.dist(ex.item)
      if d <= (self.radiusFactor * cluster.radius()):
        distances.append(d)
    mean = sum(distances) / len(distances)
    devianceSqrSum = sum([(d - mean) **2 for d in distances])
    var = devianceSqrSum / len(distances)
    stdDevDistance = var **0.5
    # 
    isCohesive = silhouette(dist, stdDevDistance) > 0
    return isRepresentative and isCohesive
  #
  def closestCluster(self, vec: List[float], clusters = None) -> (Cluster, float):
    """Returns the nearest cluster and its distance (nearCl, dist)"""
    dist = float("inf")
    nearCl = None
    if clusters == None:
      clusters = self.clusters
    for cl in clusters:
      d = cl.dist(vec)
      if d < dist:
        dist = d
        nearCl = cl
    return nearCl, dist
  # 
  def classify(self, example: Example):
    cluster, dist = self.closestCluster(example.item)
    return (dist <= (self.radiusFactor * cluster.radius()), cluster, dist)
  
  # ----------------------------------------------------------------------------------------------------------------
  
  def offline(self, training_set=[]):
    """
      Require:
        k: number of micro-clusters,
        alg: clustering algorithm,
        S: Training Set
      
      Model ← ∅
      for all (class Ci in S) do
        ModelTmp ← Clustering(SClass=Ci, k, alg)
        for all (micro-cluster micro in ModelTmp) do
          micro.label ← Ci ;
        end for
        Model ← Model ∪ ModelTmp;
      end for
      return Model
    """
    assert len(training_set) > 0
    # training_set = Example[]
    keyfunc = lambda x: x.label
    self.clusters = []
    training_set = sorted(training_set, key=keyfunc)
    for label, examples in intertools.groupby(training_set, keyfunc):
      clusters = self.clustering(list(examples))
      # add labels
      for cluster in clusters:
        isRepresentative = cluster.counter > self.representationThr
        if isRepresentative:
          cluster.label = label
          self.clusters.append(cluster)
    self.ndProcedureThr = len(training_set)
    print_log('[offline end]')
    # store self to a file
    return self
  
  # should be async
  def online(self, stream):
    while True:
      example = stream.get()
      if example is None:
        break
      # print_log('Online', example)
      self.onlineProcessExample(example)
      # stream.task_done()
    return self
  
  def onlineProcessExample(self, example):
    """
      Require:
        Model: decision model from initial training phase,
        DS: data stream,
        T: threshold,
        NumExamples: minimal number of examples to execute a ND procedure,
        windowsize: size of a data window,
        alg: clustering algorithm
      
      ShortMem ← ∅
      SleepMem ← ∅
      
      for all (example ex in DS) do
        (Dist, micro) ← closer-micro(ex,Model)
        if (Dist ≤ radius(micro) then
          ex.class ← micro.label
          update-micro(micro,ex)
        else
          ex.class ← unknown
          ShortMem ← ShortMem ∪ ex
          if (|ShortMem| ≥ NumExamples) then
            Model ← novelty-detection(Model, ShortMem, SleepMem, T, alg)
          end if
        end if
        CurrentTime ← ex.time
        if (CurrentTime mod windowSize == 0) then
          Model ← move-sleepMem(Model, SleepMem, CurrentTime, windowSize)
          ShortMem ← remove-oldExamples(ShortMem, windowsize)
        end if
      end for
    """
    # example = Example(item=await stream.read())
    # for ex in stream:
    self.globalCount += 1
    example = Example(item=example)
    self.lastExapleTMS = example.timestamp
    cluster, dist = self.closestCluster(example.item)
    example.classificationTries += 1
    if dist <= (self.radiusFactor * cluster.radius()):
      example.label = cluster.label
      cluster.addExample(example)
      self.counter += 1
    else:
      # None is unknown class
      self.unknownBuffer.append(example)
    #
    if len(self.unknownBuffer) > self.ndProcedureThr:
      self.bufferFull()
    return self

  def bufferFull(self):
    print_log('bufferFull', self.statusStr())
    for sleepExample in self.unknownBuffer:
      cluster, dist = self.closestCluster(sleepExample.item, self.sleepClusters)
      sleepExample.classificationTries += 1
      if cluster and dist <= (self.radiusFactor * cluster.radius()):
        sleepExample.label = cluster.label
        cluster.addExample(sleepExample)
        self.unknownBuffer.remove(sleepExample)
        # wakeup
        print_log('wakeup')
        self.clusters.append(cluster)
        self.sleepClusters.remove(cluster)
        self.counter += 1
    print_log('[after sleep check]', self.statusStr())
    # 
    self = self.noveltyDetection()
    print_log('[after novelty Detection]', self.statusStr())
    # Model ← move-sleepMem(Model, SleepMem, CurrentTime, windowSize)
    newSleepClusters = []
    newClusters = []
    for cl in self.clusters:
      if cl.lastExapleTMS < self.lastCleaningCycle:
        newSleepClusters.append(cl)
      if cl.lastExapleTMS >= self.lastCleaningCycle:
        newClusters.append(cl)
    #
    print_log('Sleep', len(newSleepClusters))
    self.sleepClusters.extend(newSleepClusters)
    self.clusters = newClusters
    self.lastCleaningCycle = time.time()
    print_log('[after Sleep Clean]', self.statusStr())
    # ShortMem ← remove-oldExamples(ShortMem, windowsize)
    ogLen = len(self.unknownBuffer)
    self.unknownBuffer = []
    for ex in self.unknownBuffer:
      if ex.classificationTries >= 3:
        self.unknownBuffer.append(ex)
    print_log('[Cleaning Cycle]\tDiscarting {n} examples'.format(n=ogLen - len(self.unknownBuffer)))
    print_log('[after Unkown Clean]', self.statusStr())
    return self

  #
  def noveltyDetection(self):
    """noveltyDetection
      Require:
        Model: current decision model,
        ShortMem: short-term memory,
        SleepMem: sleep memory,
        T: threshold,
        alg: clustering algorithm
      
      ModelTmp ← Clustering(ShortMem, k, alg)
      for all (micro-grupo micro in ModelTemp) do
        if ValidationCriterion(micro) then
          (Dist, microM) ← closest-micro(micro,Model)
          if Dist ≤ T then
            micro.label ← microM.label
          else
            (Dist, microS) ← closest-micro(micro,SleepMem)
            if Dist ≤ T then
              micro.label ← microS.label
            else
              micro.label ← new label
            end if
          end if
          Model ← Model ∪ micro
        end if
      end for
      return Model
    """
    print_log('[noveltyDetection]\t', 'unknownBuffer:', len(self.unknownBuffer), 'sleepClusters:', len(self.sleepClusters))
    for cluster in self.clustering(self.unknownBuffer):
      T = self.noveltyThr
      # T = self.noveltyThrFn(cluster)
      if self.validationCriterion(cluster, self.unknownBuffer):
        near, dist = self.closestCluster(cluster.center)
        if dist <= T:
          cluster.label = near.label
        else:
          near, dist = self.closestCluster(cluster.center, self.sleepClusters)
          if dist <= T:
            cluster.label = near.label
            # wakeup
            print_log('wakeup')
            self.clusters.append(near)
            self.sleepClusters.remove(near)
          else:
            self.noveltyIndex += 1
            cluster.label = 'Novelty ' + str(self.noveltyIndex)
            print_log(cluster.label)
            self.clusters.append(cluster)
    return self

if __name__ == "__main__":
  self_test.selfTest(Minas)