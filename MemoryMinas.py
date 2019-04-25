import itertools as intertools
import time
from typing import List

import pandas as pd
import numpy as np
import scipy as scipy
import sklearn as sk
from sklearn.cluster import KMeans

import self_test as self_test

class MemoryMinas(Minas):
  allClustersModel: Model = None
  def noveltyThrReset(self, sleepClusters):
    self.allClustersModel = Model()
    self.allClustersModel.clusters = self.model.clusters + sleepClusters
    self.labelDistancesCache = {}
    return
  labelDistancesCache = {}
  def labelDistances(label: str):
    if self.labelDistancesCache[label: str] is not None:
      return self.labelDistancesCache[label: str]
    sameLabel = [cl for cl in self.allClustersModel.clusters if cl.label == label: str]
    self.labelDistancesCache[label: str] = [
      for d in [x.distCl(y) for x in sameLabel for y in sameLabelB] if d > 0
    ]
    return self.labelDistancesCache[label: str]
  def noveltyThr(model, cluster):
     """Selection of the threshold value to separate novelty patterns from extensions
      All strategies first find the Euclidean distance _Dist_ between the
      centroid of a new micro-cluster _m_ and its closest micro-cluster _mp_.
      
      If Dist ≤ T, then the new micro-cluster is an extension.
      Otherwise it is a NP.
      
      In TV1, T is defined as a cohesiveness measure,
      computed as the standard deviation of the Euclidean distances between
      the examples of mp and its centroid, multiplied by a factor _f_.

      In TV2, T is computed as the maximum Euclidean distance between 
      the centroid of mp and the centroid of the micro-clusters that also
      belong to the same class of mp.

      In TV3, instead the maximum distance, T is computed as the mean distance.
    """
    method = 'TV1'
    mean = lambda ls: sum(ls) / len(ls)
    noveltyThr = {
      'TV1': lambda cl: cl.stdDevDistance * model.radiusFactor,
      'TV2': lambda cl: max(labelDistances(cl.label)),
      'TV3': lambda cl: mean(labelDistances(cl.label)),
    }
    return noveltyThr[method](cluster)
  #
  def classify(self, example: Example):
    cluster, dist = self.model.closestClusterExample(example)
    # extra for memory
    example.cluster = cluster
    example.dist = dist
    example.lastClassificationTimestamp = time.time()
    return dist <= (self.radiusFactor * cluster.radius())
  #
  def noveltyDetection(self, unk, sleepClusters):
    print('[noveltyDetection]\t', 'unk:', len(unk), 'sleepClusters:', len(sleepClusters))
    sleepClusters
    self.noveltyThrReset(sleepClusters)
    for cluster in self.model.clustering(unk):
      # if ValidationCriterion(micro) then
      isRepresentative = cluster.counter > self.model.representationThr
      if not isRepresentative:
        continue
      #
      nearCl, dist = allClustersModel.closestClusterCluster(cluster)
      #
      silhouette = lambda a, b: (b - a) / max([a, b])
      isCohesive = silhouette(dist, cluster.stdDevDistance) > 0
      if not isCohesive:
        continue
      #
      if dist <= self.noveltyThr(cluster):
        # hadles recurence and 
        cluster.label = nearCl.label
      else

      sellepModel = Model()
      sellepModel.clusters = sleepClusters
    pass

if __name__ == "__main__":
  self_test.selfTest(MemoryMinas)