import itertools, time, sys, traceback, asyncio, logging, yaml
from typing import List

import pandas as pd
import numpy as np
import scipy as scipy
import sklearn as sk
from sklearn.cluster import KMeans
from sklearn.externals import joblib

import dask
from dask import delayed

import self_test
from timed import timed

class Example:
  """Holds an example
  label:      if already classified (or for training)
  item:       the precise example itself, a float list
  timestamp:  created time (used for garbage colletion)
  tries:      in how many classification tries it was used (used for garbage colletion)
  """
  __slots__ = ['label', 'item', 'timestamp', 'tries']
  def __init__(self, label=None, item: List[float]=[]):
    self.label = label
    self.item = [float(i) for i in item]
    self.timestamp = time.time()
    self.tries = 0
  def __repr__(self):
    dic = {
      'len': len(self.item),
      'timestamp': self.timestamp,
      'tries': self.tries,
    }
    return 'Example({l}, ) # ${dic!r}'.format(l=self.label, i=self.item, len=len(self.item), dic=dic)
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
  __slots__ = [ 'label', 'center', 'n', 'lastExapleTMS', 'sumDistance', 'maxDistance', ]
  def __init__(self, label='', center=[], n=0, sumDistance=0.0, maxDistance=0.0):
    self.label = label
    self.center = center
    self.n = n
    self.sumDistance = sumDistance
    self.maxDistance = maxDistance
    self.lastExapleTMS = -float("inf")
  def __str__(self):
    return '[{label}]\tn={count}\tc={c},\tr={r:2.2f}'.format(
      label=self.label,
      count=self.n,
      c=', '.join(['{:2.2f}'.format(c) for c in self.center]),
      r=self.radius()
    )
  def __repr__(self):
    return 'Cluster(label={l},\tn={co},\tsum={sum:2.2f},\tmax={max:2.2f},\tcenter=[{ce}])'.format(
      l=self.label, ce=', '.join(['{:2.2f}'.format(c) for c in self.center]), co=self.n, sum=self.sumDistance, max=self.maxDistance,
    )
  def meanDistance(self):
    return self.sumDistance /self.n if self.n > 0 else 0
  def asDic(self):
    return {k: getattr(self, k) for k in self.__slots__}
  def radius(self):
    return self.maxDistance
  
  def dist(self, vec: List[float] = []):
    # assert type(vec) is list, 'dist takes only lists'
    assert len(vec) == len(self.center), 'dist can only compare same-dimetion vectors'
    try:
      return scipy.spatial.distance.euclidean(self.center, vec)
    except:
      return float('inf')
  
  @timed
  def addExample(self, example, distance=None):
    self.n += 1
    if example.timestamp > self.lastExapleTMS:
      self.lastExapleTMS = example.timestamp
    if distance == None:
      distance = self.dist(example.item)
    self.sumDistance += distance
    if distance > self.maxDistance:
      self.maxDistance = distance

@delayed(pure=True)
@timed
def closestClusterDelayedPure(vec: List[float], clusters = List[Cluster]) -> (Cluster, float):
  """Returns the nearest cluster and its distance (nearCl, dist)"""
  dist = float("inf")
  nearCl = None
  for cl in clusters:
    d = scipy.spatial.distance.euclidean(cl.center, vec)
    if d < dist:
      dist = d
      nearCl = cl
  return nearCl, dist
  # 

class Minas:
  # CONSTS
  __slots__ = [
    'k', 'radiusFactor', 'noveltyThr', 'windowTimeSize', 'ndProcedureThr', 'representationThr', 'globalCount',
    'lastExapleTMS', 'lastCleaningCycle', 'clusters', 'sleepClusters', 'counter', 'unknownBuffer', 'noveltyIndex',
    'daskEnableKmeans', 'daskEnableDist',
  ]
  def __init__(self, daskEnableKmeans=False, daskEnableDist=False):
    self.daskEnableKmeans = daskEnableKmeans
    self.daskEnableDist = daskEnableDist
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
      'counter': self.counter,
      'noveltyIndex': self.noveltyIndex,
      'clusters': self.clusters,
      'sleepClusters': self.sleepClusters,
      'unknownBuffer': self.unknownBuffer,
      'diff': self.globalCount-self.counter,
      'known': self.counter,
    }
  def store(self):
    selfDict = self.asDict()
    # selfDict['clusters'] = len(self.clusters)
    # selfDict['sleepers'] = len(self.sleepClusters)
    # selfDict['unknownBuffer'] = len(self.unknownBuffer)
    return selfDict
  def storeToFile(self, filename: str):
    with open(filename, 'w') as f:
      f.write(yaml.dump(self.store()))
  def restoreFromFile(self, filename: str):
    with open(filename, 'r') as f:
      config = yaml.load(f, Loader=yaml.SafeLoader)
      self.restore(config)
  def restore(self, dic: dict):
    self.k = dic.get('k', self.k)
    self.radiusFactor = dic.get('radiusFactor', self.radiusFactor)
    self.noveltyThr = dic.get('noveltyThr', self.noveltyThr)
    self.windowTimeSize = dic.get('windowTimeSize', self.windowTimeSize)
    self.ndProcedureThr = dic.get('ndProcedureThr', self.ndProcedureThr)
    self.representationThr = dic.get('representationThr', self.representationThr)
    self.globalCount = dic.get('globalCount', self.globalCount)
    self.lastExapleTMS = dic.get('lastExapleTMS', self.lastExapleTMS)
    self.lastCleaningCycle = dic.get('lastCleaningCycle', self.lastCleaningCycle)
    self.clusters = dic.get('clusters', self.clusters)
    self.sleepClusters = dic.get('sleepClusters', self.sleepClusters)
    self.counter = dic.get('counter', self.counter)
    self.unknownBuffer = dic.get('unknownBuffer', self.unknownBuffer)
    self.noveltyIndex = dic.get('noveltyIndex', self.noveltyIndex)
  
  # 
  def __repr__(self):
    selfDict = self.asDict()
    selfDict['clusters'] = len(self.clusters)
    selfDict['sleepers'] = len(self.sleepClusters)
    selfDict['unknownBuffer'] = len(self.unknownBuffer)
    return '# {status}\nMinas({cls!r}\n{clusters}\n)'.format(
      status=str(self),
      cls=selfDict,
      clusters='\t'+'\n\t'.join([repr(c) for c in self.clusters])
    )
    
  def __str__(self):
    return '<Model Status clusters: {clusters}, sleepers: {sleepers}, known: {known}, unkown: {u} ({diff}), total: {globalCount}>'.format(
      clusters=len(self.clusters), sleepers=len(self.sleepClusters),
      known=self.counter, u=len(self.unknownBuffer), diff=self.globalCount-self.counter, globalCount=self.globalCount
    )
  
  @timed
  def clustering(self, examples):
    """
    After the execution of the clustering algorithm, each micro-cluster is represented
    by four components (N, LS, SS and T).
    """
    logging.info('clustering {}, {}'.format(len(examples), examples[0]))
    assert len(examples) > 0
    
    n_samples = len(examples)
    n_clusters = min(self.k, int(n_samples / (3 * self.representationThr)))
    assert n_samples >= n_clusters
    df = pd.DataFrame(data=[ex.item for ex in examples])
    kmeans = KMeans(n_clusters=n_clusters)
    if self.daskEnableKmeans:
      with joblib.parallel_backend('dask'):
        kmeans.fit(df)
    else:
      kmeans.fit(df)

    clusters = []
    for centroid in kmeans.cluster_centers_:
      c = Cluster()
      c.center = centroid
      clusters.append(c)
    # Add examples to its cluster
    for ex in examples:
      nearCl, dist = self.closestCluster(ex.item, clusters)
      try:
        nearCl.addExample(ex)
      except:
        pass
    return clusters

  @timed
  def closestCluster(self, vec: List[float], clusters = None) -> (Cluster, float):
    """Returns the nearest cluster and its distance (nearCl, dist)"""
    if clusters == None:
      clusters = self.clusters
    if self.daskEnableDist:
      return closestClusterDelayedPure(vec, clusters).compute()
    dist = float("inf")
    nearCl = None
    for cl in clusters:
      d = cl.dist(vec)
      if d < dist:
        dist = d
        nearCl = cl
    return nearCl, dist

  @timed
  def validationCriterion(self, cluster: Cluster, unknownBuffer):
    isRepresentative = cluster.n > self.representationThr
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
  
  @timed
  def classify(self, example: Example):
    cluster, dist = self.closestCluster(example.item)
    clusterSleep, distSleep = self.closestCluster(example.item, self.sleepClusters)
    if distSleep < dist:
      cluster = clusterSleep
      dist = distSleep
    return (dist <= (self.radiusFactor * cluster.radius()), cluster, dist)
  
  # ----------------------------------------------------------------------------------------------------------------
  
  @timed
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
    if hasattr(training_set, '__len__') and len(training_set) <= 0:
      raise Exception('offline training set must have len > 0')
    # training_set = Example[]
    keyfunc = lambda x: x.label
    self.clusters = []
    training_set = sorted(training_set, key=keyfunc)
    for label, examples in itertools.groupby(training_set, keyfunc):
      clusters = self.clustering(list(examples))
      # add labels
      for cluster in clusters:
        isRepresentative = cluster.n > self.representationThr
        if isRepresentative:
          cluster.label = label
          self.clusters.append(cluster)
    self.ndProcedureThr = len(training_set)
    logging.info('[offline end]')
    # store self to a file
    return self
  
  @timed
  def online(self, stream):
    for example in stream:
      if example is None:
        break
      self.onlineProcessExample(example)
    return self
  
  @timed
  def onlineProcessExample(self, item: List[float]):
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
    example = Example(item=item)
    self.lastExapleTMS = example.timestamp
    cluster, dist = self.closestCluster(example.item)
    example.tries += 1
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

  @timed
  def bufferFull(self):
    logging.info('bufferFull, {}'.format(self))
    for sleepExample in self.unknownBuffer:
      cluster, dist = self.closestCluster(sleepExample.item, self.sleepClusters)
      sleepExample.tries += 1
      if cluster and dist <= (self.radiusFactor * cluster.radius()):
        sleepExample.label = cluster.label
        cluster.addExample(sleepExample)
        self.unknownBuffer.remove(sleepExample)
        # wakeup
        logging.info('wakeup')
        self.clusters.append(cluster)
        self.sleepClusters.remove(cluster)
        self.counter += 1
    logging.info('[after sleep check]' + str(self))
    # 
    self = self.noveltyDetection()
    logging.info('[after novelty Detection]' + str(self))
    # Model ← move-sleepMem(Model, SleepMem, CurrentTime, windowSize)
    newSleepClusters = []
    newClusters = []
    for cl in self.clusters:
      if cl.lastExapleTMS < self.lastCleaningCycle:
        newSleepClusters.append(cl)
      if cl.lastExapleTMS >= self.lastCleaningCycle:
        newClusters.append(cl)
    #
    logging.info('Sleep {}'.format(len(newSleepClusters)))
    self.sleepClusters.extend(newSleepClusters)
    self.clusters = newClusters
    self.lastCleaningCycle = time.time()
    logging.info('[after Sleep Clean] {}'.format(self))
    # ShortMem ← remove-oldExamples(ShortMem, windowsize)
    ogLen = len(self.unknownBuffer)
    self.unknownBuffer = []
    for ex in self.unknownBuffer:
      if ex.tries >= 3:
        self.unknownBuffer.append(ex)
    logging.info('[Cleaning Cycle]\tDiscarting {n} examples'.format(n=ogLen - len(self.unknownBuffer)))
    logging.info('[after Unkown Clean] {}'.format(self))
    return self

  @timed
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
    logging.info('[noveltyDetection]\t unknownBuffer: {u}, sleepClusters: {s}'.format(u=len(self.unknownBuffer), s=len(self.sleepClusters)))
    for cluster in self.clustering(self.unknownBuffer):
      if self.validationCriterion(cluster, self.unknownBuffer):
        near, dist = self.closestCluster(cluster.center)
        if dist <= self.noveltyThr:
          cluster.label = near.label
        else:
          near, dist = self.closestCluster(cluster.center, self.sleepClusters)
          if dist <= self.noveltyThr:
            cluster.label = near.label
            # wakeup
            logging.info('wakeup')
            self.clusters.append(near)
            self.sleepClusters.remove(near)
          else:
            self.noveltyIndex += 1
            cluster.label = 'Novelty ' + str(self.noveltyIndex)
            logging.info(cluster.label)
            self.clusters.append(cluster)
    return self

if __name__ == "__main__":
  self_test.selfTest(Minas)