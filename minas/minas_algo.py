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

from .example import Example, Vector
from .cluster import Cluster

@dataclasses.dataclass
class MinasConsts:
    k: int = 100
    radiusFactor: float = 1.1
    noveltyThr: int = 100
    ndProcedureThr: int = 2000
    windowSize: int = 2000 * 2
    representationThr: int = 1
    silhouetteThr: int = 0
    @classmethod
    def SETTINGS_1():
        SETTINGS_1 = MinasConsts()
        SETTINGS_1.k = 100
        SETTINGS_1.ndProcedureThr = 2000
        # representationThr #ExClu => #ExMem/K
        SETTINGS_1.representationThr = SETTINGS_1.ndProcedureThr / SETTINGS_1.k
        SETTINGS_1.windowSize = SETTINGS_1.ndProcedureThr * 2
        SETTINGS_1.radiusFactor = 1.1
    def __getstate__(self):
        return {
            'k': self.k,
            'radiusFactor': self.radiusFactor,
            'noveltyThr': self.noveltyThr,
            'windowSize': self.windowSize,
            'ndProcedureThr': self.ndProcedureThr,
            'representationThr': self.representationThr,
            'silhouetteThr': self.silhouetteThr,
        }

ClusterList = typing.List[Cluster]
ExampleList = typing.List[Example]

@dataclasses.dataclass
class MinasAlgorith:
    CONSTS: MinasConsts = MinasConsts()
    def closestCluster(self, item: Vector, clusters: ClusterList) -> (float, Cluster):
        msg = 'Item and cluster dimentions must be the same. Got {} and {}.'
        assert len(item) == len(clusters[0].center), msg.format(len(item), len(clusters[0].center))
        return min( ((cl.dist(item), cl) for cl in clusters), key=lambda x: x[0])
    def clustering(self, examples: typing.List[Vector], label: str = None) -> ClusterList:
        n_samples = len(examples)
        # n_clusters = min(self.CONSTS.k, int(n_samples / (self.CONSTS.representationThr + 1)))
        n_clusters = min(self.CONSTS.k, int(n_samples / ( 3 * self.CONSTS.representationThr)))
        assert n_samples >= n_clusters
        df = pd.DataFrame(examples)
        kmeans = KMeans(n_clusters=n_clusters)
        kmeans.fit(df)
        clusters = [Cluster(center=centroid, label=label) for centroid in kmeans.cluster_centers_]
        for ex in examples:
            dist, nearCl = self.closestCluster(ex, clusters)
            nearCl.addExample(Example(ex), dist)
        return clusters
    def trainGroup(self, group: list, label: str = None):
        clusters = self.clustering(group, label)
        for ex in group:
            dist, nearCl = self.closestCluster(ex, clusters)
            nearCl.addExample(Example(ex), dist)
        validClusters = []
        for cluster in clusters:
            if cluster.n >= self.CONSTS.representationThr and cluster.maxDistance > 0:
                validClusters.append(Cluster(center=cluster.center, label=label))
        # move all examples to nearest valid cluster
        for ex in group:
            dist, nearCl = self.closestCluster(ex, validClusters)
            nearCl.addExample(Example(ex), dist)
        return validClusters
    def training(self, examplesDf):
        clusters = []
        groupSize = self.CONSTS.k * self.CONSTS.representationThr
        for label, group in examplesDf.groupby('label'):
            clusters += self.trainGroup(list(group['item']), label)
        return clusters
    def checkTraining(self, examplesDf, clusters):
        assert sum(map(lambda x: x.n, clusters)) == len(examplesDf), 'Not all training examples were consumed'
        notClassified = 0
        wrongClassification = 0
        for index, row in examplesDf.iterrows():
            isClassified, nearCl, dist, example = self.classify(Example(item=row['item']), clusters)
            if not isClassified:
                notClassified += 1
            if not nearCl.label == row['label']:
                wrongClassification += 1
        print(f'notClassified = {notClassified}, wrongClassification = {wrongClassification},')
        return clusters
    #
    def online(self, stream,
        clusters: ClusterList, sleepClusters: ClusterList, unknownBuffer: ExampleList, 
        knownCount = 0, noveltyIndex = 0, lastCleaningCycle = 0, outStream = []
    ):
        i = 0
        for example in stream:
            if example is None:
                break
            i += 1
            # custo 1000 -> 10
            kwargs = dict(
                index=i, item=example, clusters=clusters, sleepClusters=sleepClusters,
                unknownBuffer=unknownBuffer, knownCount=knownCount, noveltyIndex=noveltyIndex,
                lastCleaningCycle=lastCleaningCycle, outStream=outStream
            )
            processed = self.processExample(**kwargs)
            example, isClassified, cluster, dist, knownCount, noveltyIndex, lastCleaningCycle = processed
        return self
    def classify(self, example: Example, clusters: ClusterList = []) -> (bool, Cluster, float, Example):
        # dist, nearCl = self.closestCluster(example.item, clusters)
        distances = []
        for cl in clusters:
            dist = cl.dist(example.item)
            relativeDist = dist / cl.radius()
            isClassified = dist <= (self.CONSTS.radiusFactor * cl.radius())
            distances.append( (dist, relativeDist, isClassified, cl) )
        minDist = min(distances, default=None, key=lambda d: d[0])
        # minRelDist = min(distances, default=None, key=lambda d: d[1])
        minClassDist = min(filter(lambda d: d[2], distances), default=None, key=lambda d: d[0])
        # minClassRelDist = min(filter(lambda d: d[2], distances), default=None, key=lambda d: d[1])
        # if minClassDist and minClassRelDist and minClassDist[0] < minClassRelDist[0] and minClassDist[3].label != minClassRelDist[3].label:
        #     self.diffDistAndRelative()
        # if minClassRelDist:
        #     return True, minClassRelDist[3], minClassRelDist[0], example
        if minClassDist:
            return True, minClassDist[3], minClassDist[0], example
        return False, minDist[3], minDist[0], example
    def diffDistAndRelative(self):
        # print('WARN diff dist and rel dist: ', minClassDist[0] - minClassRelDist[0], minClassDist[3].label, minClassRelDist[3].label)
        return
    def processExample(
        self, index, item: Vector, clusters: ClusterList, sleepClusters: ClusterList, unknownBuffer: ExampleList, 
        knownCount = 0, noveltyIndex = 0, lastCleaningCycle = 0, outStream = []
    ):
        isClassified, cluster, dist, example = self.classify(Example(item=item), clusters)
        example.tries += 1
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
            knownCount += self.recurenceDetection(clusters=clusters, sleepClusters=sleepClusters, unknownBuffer=unknownBuffer, outStream=outStream)
            knownCount, noveltyIndex = self.noveltyDetection(
                clusters=clusters,
                sleepClusters=sleepClusters,
                unknownBuffer=unknownBuffer,
                knownCount=knownCount,
                noveltyIndex=noveltyIndex,
                outStream=outStream,
            )
            outStream.append('bufferFull done {}ns'.format(time.time_ns() - init))
            # self.cleanupCycle(clusters, sleepClusters, unknownBuffer, knownCount)
        if index % self.CONSTS.windowSize == 0:
            for cluster in clusters:
                if cluster.lastExapleTMS < lastCleaningCycle:
                    sleepClusters.append(cluster)
                    clusters.remove(cluster)
            if len(clusters) == 0:
                # fallback 
                clusters.extend(sleepClusters)
                sleepClusters.clear()
            for ex in unknownBuffer:
                if ex.tries >= 3:
                    unknownBuffer.remove(ex)
            lastCleaningCycle = time.time_ns()
        return example, isClassified, cluster, dist, knownCount, noveltyIndex, lastCleaningCycle
    def recurenceDetection(self, clusters: ClusterList, sleepClusters: ClusterList, unknownBuffer: ExampleList, outStream: list):
        knownCount = 0
        allClusters = clusters + sleepClusters
        for sleepExample in unknownBuffer:
            sleepExample.tries += 1
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
    def noveltyDetection(self, clusters: ClusterList, sleepClusters: ClusterList, unknownBuffer: ExampleList, knownCount: int, noveltyIndex: int, outStream: list):
        df = pd.DataFrame([ex.item for ex in unknownBuffer])
        newClusters = self.clustering(df)
        # fill in cluster radius
        for ex in unknownBuffer:
            dist, nearCl = self.closestCluster(ex.item, newClusters)
            if not hasattr(nearCl, 'temp_examples'):
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
                label = 'Novelty {}'.format(noveltyIndex)
                outStream.append(label)
                noveltyIndex += 1
                cluster.label = label
            newValidClusters.append(cluster)
        # 
        clusters.extend(newValidClusters)

        if len(newValidClusters) > 0:
            for ex in unknownBuffer:
                ex.tries += 1
                isClassified, nearCl, dist, example = self.classify(ex, newValidClusters)
                if isClassified:
                    unknownBuffer.remove(ex)
                    knownCount += 1

        return knownCount, noveltyIndex