import itertools as intertools
import time

import pandas as pd
import numpy as np
import scipy as scipy
import sklearn as sk
from sklearn.cluster import KMeans

import self_test as self_test

class Example:
  __slots__ = ['label', 'item', 'timestamp']
  def __init__(self, label=None, item=[]):
    self.label = label
    self.item = item
    self.timestamp = time.time()

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
      r=self.maxDistance
    )
  def dist(self, example):
    return scipy.spatial.distance.euclidean(self.center, example.item)
  def addExample(self, example):
    self.counter += 1
    self.lastExapleTMS = example.timestamp
    distance = self.dist(example)
    self.sumDistance += distance
    self.meanDistance = self.sumDistance / self.counter
    if distance > self.maxDistance:
      self.maxDistance = distance
    if distance < self.minDistance:
      self.maxDistance = distance

class Model:
  k = 100
  clusters = []
  radiusFactor = 1.1
  noveltyThr = 100
  lastExapleTMS = -float("inf")
  lastCleaningCycle = -float("inf")
  windowTimeSize = 10000
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
  # ------------------------------------------------------------------------------------------------
  def __str__(self):
    return 'Model(k={k}, clusters={ncls})({cls}\n)'.format(
      k=self.k,
      ncls=len(self.clusters),
      cls=''.join(['\n\t' + str(c) for c in self.clusters])
    )
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
  def closerCluster(self, example):
    """Returns the nearest cluster and its distance"""
    dist = float("inf")
    nearCl = None
    for cl in self.clusters:
      d = cl.dist(example)
      if d < dist:
        dist = d
        nearCl = cl
    return nearCl, dist

class Minas(Model):
  model = None
  unk = []
  sleepClusters = []
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
    print(self.model)
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
    for ex in stream:
      example = Example(item=ex)
      self.model.lastExapleTMS = example.timestamp
      cluster, dist = self.model.closerCluster(example)
      if dist <= (self.model.radiusFactor * cluster.meanDistance):
        example.label = cluster.label
        cluster.addExample(example)
      else:
        # None is unknown class
        self.unk.append(example)
        if len(self.unk) > self.model.ndProcedureThr:
          self.noveltyDetection(self.unk, self.sleepClusters)
      #
      if (example.timestamp - self.model.lastCleaningCycle) > self.model.windowTimeSize:
        # Model ← move-sleepMem(Model, SleepMem, CurrentTime, windowSize)
        newSleepClusters = [cl for cl in self.model.clusters if cl.lastExapleTMS < self.model.lastCleaningCycle]
        self.sleepClusters.extend(newSleepClusters)
        self.model.clusters = [cl for cl in self.model.clusters if cl.lastExapleTMS >= self.model.lastCleaningCycle]
        self.model.lastCleaningCycle = example.timestamp
        # ShortMem ← remove-oldExamples(ShortMem, windowsize)
        ogLen = len(self.unk)
        self.unk = [ex for ex in self.unk if ex.timestamp >= self.model.lastCleaningCycle]
        print('Discarting {n} examples'.format(n=ogLen - len(self.unk)))
    #
    return self

  def noveltyDetection(self, parameter_list):
    """
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
    pass

if __name__ == "__main__":
  self_test.selfTest()