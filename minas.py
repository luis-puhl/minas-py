import itertools as intertools
import time
from typing import List
from copy import deepcopy

import pandas as pd
import numpy as np
import scipy as scipy
import sklearn as sk
from sklearn.cluster import KMeans

import self_test as self_test

class Example:
  __slots__ = ['label', 'item', 'timestamp', 'classificationTries']
  def __init__(self, label=None, item=[]):
    self.label = label
    self.item = item
    self.timestamp = time.time()
    self.classificationTries = 0

class Cluster:
  """
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
  counter = 0
  # statistic summary
  sumDistance = 0.0
  meanDistance = 0.0
  maxDistance = 0.0
  minDistance = 0.0
  stdDevDistance = 0.0
  # centroid
  center = np.array([])
  label = ''
  #
  lastExapleTMS = -float("inf")
  def __str__(self):
    return '[{label}]\tn={count}\tc={c},\tr={r:2.2f}'.format(
      label=self.label,
      count=self.counter,
      c=', '.join(['{:2.2f}'.format(c) for c in self.center]),
      r=self.radius()
    )
  def __repr__(self):
    return self.__str__()
  def radius(self):
    return self.maxDistance
  def dist(self, example):
    return scipy.spatial.distance.euclidean(self.center, example.item)
  def distCl(self, other):
    return scipy.spatial.distance.euclidean(self.center, other.center)
  def addExample(self, example):
    self.counter += 1
    self.lastExapleTMS = example.timestamp
    distance = self.dist(example)
    self.sumDistance += distance
    self.meanDistance = self.sumDistance / self.counter
    if distance > self.maxDistance:
      self.maxDistance = distance
    if distance < self.minDistance:
      self.minDistance = distance

class Model:
  k = 100
  clusters: List[Cluster] = []
  radiusFactor = 1.1
  noveltyThr = 100
  lastExapleTMS = -float("inf")
  lastCleaningCycle = -float("inf")
  windowTimeSize = 100
  # ------------------------------------------------------------------------------------------------
  # actions Thresholds
  #ExND
  ndProcedureThr = 2000
  def ndProcedureThrFn(self):
    return self.representationThr * self.k
  #ExClu
  representationThr = 3
  def representationThrFn(self):
    return len(self.unknownBuffer) / self.k
  # Window size to forget outdated data
  forgetThr = 1000
  def forgetThrFn(self):
    return 2 * self.ndProcedureThr
  def noveltyThrFn(cluster):
    return cluster.stdDevDistance * self.radiusFactor,
  # ------------------------------------------------------------------------------------------------
  unk: List[Example] = []
  sleepClusters: List[Cluster] = []
  noveltyIndex = 0
  counter = 0
  # ------------------------------------------------------------------------------------------------
  def __str__(self):
    return 'Model(k={k}, clusters={ncls})({cls}\n)'.format(
      k=self.k,
      ncls=len(self.clusters),
      cls=''.join(['\n\t' + str(c) for c in self.clusters])
    )
  def __repr__(self):
    return self.__str__()
  def clustering(self, examples):
    """
    After the execution of the clustering algorithm, each micro-cluster is represented
    by four components (N, LS, SS and T).
    """
    assert len(examples) > 0
    
    n_samples = len(examples)
    n_clusters = self.k
    if n_samples < n_clusters:
      n_clusters = int(n_samples / 10)
    assert n_samples >= n_clusters
    df = pd.DataFrame(data=[ex.item for ex in examples])
    kmeans = KMeans(n_clusters=n_clusters).fit(df)
    centroids = kmeans.cluster_centers_

    clusters = []
    for centroid in kmeans.cluster_centers_:
      c = Cluster()
      c.center = centroid
      clusters.append(c)
    for ex in examples:
      dist = float("inf")
      nearCl = None
      for cl in clusters:
        d = cl.dist(ex)
        if d < dist:
          dist = d
          nearCl = cl
      if nearCl:
        nearCl.addExample(ex)
    return clusters
  def closestClusterExample(self, example: Example) -> (Cluster, float):
    """Returns the nearest cluster and its distance (nearCl, dist)"""
    dist = float("inf")
    nearCl = None
    for cl in self.clusters:
      d = cl.dist(example)
      if d < dist:
        dist = d
        nearCl = cl
    return nearCl, dist
  # 
  def closestClusterCluster(self, other: Cluster) -> (Cluster, float):
    """Returns the nearest cluster and its distance (nearCl, dist)"""
    dist = float("inf")
    nearCl = None
    for cl in self.clusters:
      d = cl.distCl(other)
      if d < dist:
        dist = d
        nearCl = cl
    return nearCl, dist
  # 
  def classify(self, example: Example):
    cluster, dist = self.closestClusterExample(example)
    return (dist <= (self.radiusFactor * cluster.radius()), cluster, dist)

class Minas:
  model = None
  def __init__(self, model=Model()):
    self.model = model
  
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
    training_set = sorted(training_set, key=keyfunc)
    for label, examples in intertools.groupby(training_set, keyfunc):
      clusters = self.model.clustering(list(examples))
      # add labels
      for cluster in clusters:
        cluster.label = label
      self.model.clusters.extend(clusters)
    self.model.ndProcedureThr = len(training_set)
    return self
  
  # should be async
  def online(self, stream):
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
    ranNoveltyDetection = False
    globalCount = 0
    discarted = 0
    activeClusters = 0
    for ex in stream:
      globalCount += 1
      example = Example(item=ex)
      self.model.lastExapleTMS = example.timestamp
      if activeClusters != len(self.model.clusters):
        print('Active Clusters', len(self.model.clusters))
      activeClusters = len(self.model.clusters)
      cluster, dist = self.model.closestClusterExample(example)
      if dist <= (self.model.radiusFactor * cluster.radius()):
        example.label = cluster.label
        cluster.addExample(example)
        self.model.counter += 1
      else:
        # None is unknown class
        self.model.unk.append(example)
        if len(self.model.unk) > self.model.ndProcedureThr:
          ranNoveltyDetection = True
          self.model = self.noveltyDetection(self.model)
      #
      if (example.timestamp - self.model.lastCleaningCycle) > self.model.windowTimeSize or ranNoveltyDetection:
        print('known={c}\tunkown={u}\ttotal={t}\tdiff={d}\tdiscarted={dis}'.format(
          c=self.model.counter, u=len(self.model.unk), t=globalCount, d=globalCount-self.model.counter, dis=discarted
        ))
        ranNoveltyDetection = False
        # Model ← move-sleepMem(Model, SleepMem, CurrentTime, windowSize)
        newSleepClusters = [cl for cl in self.model.clusters if cl.lastExapleTMS < self.model.lastCleaningCycle]
        print('Sleep', len(newSleepClusters))
        self.model.sleepClusters.extend(newSleepClusters)
        self.model.clusters = [cl for cl in self.model.clusters if cl.lastExapleTMS >= self.model.lastCleaningCycle]
        self.model.lastCleaningCycle = example.timestamp
        # ShortMem ← remove-oldExamples(ShortMem, windowsize)
        ogLen = len(self.model.unk)
        self.model.unk = []
        for ex in self.model.unk:
          if ex.timestamp >= self.model.lastCleaningCycle:
            ex.classificationTries += 1
            self.model.unk.append(ex)
        discarted += ogLen - len(self.model.unk)
        print('[Cleaning Cycle]\tDiscarting {n} examples'.format(n=ogLen - len(self.model.unk)))
    #
    return self

  #
  def noveltyDetection(self, model: Model) -> Model:
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
    unk: List[Example] = model.unk
    sleepClusters: List[Cluster] = model.sleepClusters
    print('[noveltyDetection]\t', 'unk:', len(unk), 'sleepClusters:', len(sleepClusters))
    def ValidationCriterion(cluster):
      isRepresentative = cluster.counter > model.representationThr
      near, dist = model.closestClusterCluster(cluster)
      silhouette = lambda a, b: (b - a) / max([a, b])
      isCohesive = silhouette(dist, cluster.stdDevDistance) > 0
      return isRepresentative and isCohesive
    sleepModel = Model()
    sleepModel.clusters = sleepClusters
    #
    newModel = deepcopy(model)
    newModel.clusters = deepcopy(model.clusters)
    newModel.sleepClusters = deepcopy(model.sleepClusters)
    for cluster in newModel.clustering(unk):
      T = newModel.noveltyThr
      # T = newModel.noveltyThrFn(cluster)
      if ValidationCriterion(cluster):
        near, dist = newModel.closestClusterCluster(cluster)
        if dist <= T:
          cluster.label = near.label
        else:
          near, dist = sleepModel.closestClusterCluster(cluster)
          if dist <= T:
            cluster.label = near.label
            # wakeup
            print('wakeup')
            newModel.clusters.append(near)
            newModel.sleepClusters.remove(near)
          else:
            newModel.noveltyIndex += 1
            cluster.label = 'Novelty ' + str(newModel.noveltyIndex)
            print(cluster.label)
            newModel.clusters.append(cluster)
    return newModel

if __name__ == "__main__":
  self_test.selfTest(Minas)