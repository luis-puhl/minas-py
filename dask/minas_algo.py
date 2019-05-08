import time
import os
import typing
import dataclasses

import yaml
import pandas as pd
from sklearn.externals import joblib
from sklearn.cluster import KMeans
import dask
from dask.distributed import Client

from example import Example, Vector
from cluster import Cluster

@dataclasses.dataclass
class MinasConsts:
    k: int = 100
    radiusFactor: float = 1.1
    noveltyThr: int = 100
    windowSize: int = 100
    ndProcedureThr: int = 2000
    representationThr: int = 3
    silhouetteThr: int = 0

ClusterList = typing.List[Cluster]
ExampleList = typing.List[Example]

@dataclasses.dataclass
class MinasAlgorith:
    CONSTS: MinasConsts = MinasConsts()
    def closestCluster(self, item, clusters):
        if len(clusters) == 0:
            return float('inf'), None
        dist, nearCl = min( ((cl.dist(item), cl) for cl in clusters), key=lambda x: x[0])
        return dist, nearCl
    def clustering(self, examples, label=None):
        kmeans = KMeans( n_clusters=min(self.CONSTS.k, int(len(examples) / (3 * self.CONSTS.representationThr))), n_jobs=-1 )
        with joblib.parallel_backend('dask', scatter[examples]):
            kmeans.fit(examples)
        return [Cluster(center=centroid, label=label) for centroid in kmeans.cluster_centers_]
    @dask.delayed
    def trainGroup(self, label, group):
        clusters = self.clustering(group, label)
        for ex in group:
            dist, nearCl = self.closestCluster(ex, clusters)
            nearCl += Example(ex)
        return [cluster for cluster in clusters if cluster.n > self.CONSTS.representationThr]
    def training(self, examplesDf, daskClient: Client = None):
        clusters = []
        groupSize = self.CONSTS.k * self.CONSTS.representationThr
        for label, group in examplesDf.groupby('label'):
            for chunk in range(0, len(group), groupSize):
                subgroup = group[chunk:chunk + groupSize]
                subgroupDf = pd.DataFrame(iter(subgroup['item']))
                try:
                    if daskClient:
                        pass
                        # daskClient.scatter(subgroupDf)
                except Exception as ex:
                    pass
                clusters += self.trainGroup(label, subgroupDf)
        return clusters
    def offline(self, examplesDf):
        newClusters = self.training(examplesDf).compute()
        self.clusters.extend(newClusters)
    #
    def online(self, stream):
        for example in stream:
            if example is None:
                break
            self.processExample(example) # custo 1000 -> 10
        return self
    def classify(self, example: Example, clusters: ClusterList = []) -> (bool, Cluster, float, Example):
        example.tries += 1
        dist, nearCl = self.closestCluster(example.item, clusters)
        isClassified = dist <= (self.CONSTS.radiusFactor * nearCl.radius())
        return isClassified, nearCl, dist, example
    def processExample(
        self, item: Vector, clusters: ClusterList, sleepClusters: ClusterList, unknownBuffer: ExampleList, 
        knownCount = 0, noveltyIndex = 0, lastCleaningCycle = 0, outStream = []
    ):
        isClassified, cluster, dist, example = self.classify(Example(item=item), clusters)
        if isClassified:
            example.label = cluster.label
            cluster += example
            knownCount += 1
        else:
            unknownBuffer.append(example)
        # ------------------------------------------------------
        
        # ------------------------------------------------------
        if len(unknownBuffer) > self.CONSTS.ndProcedureThr:
            init = time.time_ns()
            outStream.append('bufferFull')
            knownCount = self.recurenceDetection(clusters, sleepClusters, unknownBuffer, knownCount, outStream)
            knownCount, noveltyIndex = self.noveltyDetection(clusters, sleepClusters, unknownBuffer, lastCleaningCycle, noveltyIndex, outStream)
            self.cleanupCycle(clusters, sleepClusters, unknownBuffer, knownCount)
            lastCleaningCycle = time.time_ns()
            outStream.append('bufferFull done {}ns'.format(time.time_ns() - init))
        return example, isClassified, cluster, dist, knownCount, noveltyIndex, lastCleaningCycle
    #
    def recurenceDetection(self, clusters: ClusterList, sleepClusters: ClusterList, unknownBuffer: ExampleList, knownCount: int, outStream: list):
        allClusters = clusters + sleepClusters
        for sleepExample in unknownBuffer:
            isClassified, cluster, dist, example = self.classify(sleepExample, allClusters)
            if isClassified:
                sleepExample.label = cluster.label
                cluster.addExample(sleepExample)
                unknownBuffer.remove(sleepExample)
                if cluster in sleepClusters:
                    outStream.append('Recurence {}'.format(cluster.label))
                    clusters.append(cluster)
                    sleepClusters.remove(cluster)
                    knownCount += 1
        return knownCount
    def cleanupCycle(self, clusters: ClusterList, sleepClusters: ClusterList, unknownBuffer: ExampleList, lastCleaningCycle: int):
        # Model ← move-sleepMem(Model, SleepMem, CurrentTime, windowSize)
        for cluster in clusters:
            if cluster.lastExapleTMS < lastCleaningCycle:
                sleepClusters.append(cluster)
                clusters.remove(cluster)
        if len(clusters) == 0:
            clusters.extend(sleepClusters)
            sleepClusters.clear()
        # ShortMem ← remove-oldExamples(ShortMem, windowsize)
        for ex in unknownBuffer:
            if ex.tries >= 3:
                unknownBuffer.remove(ex)
    def noveltyDetection(self, clusters: ClusterList, sleepClusters: ClusterList, unknownBuffer: ExampleList, knownCount: int, noveltyIndex: int, outStream: list):
        newClusters = self.clustering([ex.item for ex in unknownBuffer])
        
        # fill in cluster radius
        for ex in unknownBuffer:
            dist, nearCl = self.closestCluster(ex.item, newClusters)
            if nearCl.temp_examples is None:
                nearCl.temp_examples = []
            nearCl.addExample(ex, dist=dist)
        
        newValidClusters = []
        for cluster in newClusters:
            # ---------------------------------------------------------------------------------------------------
            # validationCriterion = isRepresentative and isCohesive
            # if not validationCriterion:
                # continue
            isRepresentative = cluster.n > self.CONSTS.representationThr
            if not isRepresentative:
                continue
            isCohesive = cluster.silhouette() >= self.CONSTS.silhouetteThr
            if not isCohesive:
                continue
            # ---------------------------------------------------------------------------------------------------
            distCl2Cl, nearCl2Cl = self.closestCluster(cluster.center, clusters + sleepClusters)
            if distCl2Cl <= self.CONSTS.noveltyThr:
                outStream.append('Extention {}'.format(nearCl2Cl.label))
                cluster.label = nearCl2Cl.label
            else:
                noveltyIndex += 1
                label = 'Novelty {}'.format(noveltyIndex)
                outStream.append(label)
                cluster.label = label
            newValidClusters.append(cluster)
        # 
        clusters.extend(newValidClusters)

        if len(newValidClusters) > 0:
            for ex in unknownBuffer:
                isClassified, nearCl, dist, example = self.classify(ex, newValidClusters)
                if isClassified:
                    unknownBuffer.remove(ex)
                    knownCount += 1

        return knownCount, noveltyIndex