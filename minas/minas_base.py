import time
import dataclasses
import typing
import os

import yaml
from dask.distributed import Client

from .timed import Timed
from .cluster import Cluster
from .example import Example, Vector
from .minas_algo import MinasAlgorith, ClusterList, ExampleList

@dataclasses.dataclass
class MinasBase:
    exampleCount: int = 0
    knownCount: int = 0
    noveltyIndex: int = 0
    lastExapleTMS: int = 0
    lastCleaningCycle: int = 0
    clusters: ClusterList = dataclasses.field(repr=False, default=None)
    sleepClusters: ClusterList = dataclasses.field(repr=False, default=None)
    unknownBuffer: ExampleList = dataclasses.field(repr=False, default=None)
    minasAlgorith: MinasAlgorith = MinasAlgorith()
    daskClient: typing.Union[Client, None] = None
    def asDict(self):
        return self.__getstate__()
    def __getstate__(self):
        asDictMap = lambda l: [x.__getstate__() for x in l]
        return {
            'exampleCount': self.exampleCount, 'knownCount': self.knownCount, 'diff': self.exampleCount - self.knownCount,
            'noveltyIndex': self.noveltyIndex,
            'lastExapleTMS': self.lastExapleTMS, 'lastCleaningCycle': self.lastCleaningCycle,
            'clusters': asDictMap(self.clusters), 'sleepClusters': asDictMap(self.sleepClusters),
            'unknownBuffer': asDictMap(self.unknownBuffer), 'CONSTS': self.minasAlgorith.CONSTS.__getstate__()}
    def __str__(self):
        toStr = lambda items: ( '\n\t' + ',\n\t'.join(map(lambda x: str(x), items[:10])) + '\n' if len(items) != 0 else '' )
        return (
            repr(self)[:-1]
            + f', clustersLen={len(self.clusters)}, clusters=[{toStr(self.clusters)}]'
            + f', sleepClustersLen={len(self.sleepClusters)}, sleepClusters=[{toStr(self.sleepClusters)}]'
            + f', unknownBufferLen={len(self.unknownBuffer)}, unknownBuffer=[{toStr(self.unknownBuffer)}]'
            + ')'
        )
    def storeToFile(self, filename: str):
        directory = os.path.dirname(filename)
        if len(directory) > 0 and not os.path.exists(directory):
            os.makedirs(directory)
        with open(filename, 'w') as f:
            f.write(yaml.dump(self.asDict()))
        return self
    def restoreFromFile(self, filename: str):
        with open(filename, 'r') as f:
            dic = yaml.load(f, Loader=yaml.SafeLoader)
            self.exampleCount = dic.get('exampleCount', self.exampleCount)
            self.knownCount = dic.get('knownCount', self.knownCount)
            self.noveltyIndex = dic.get('noveltyIndex', self.noveltyIndex)
            self.lastExapleTMS = dic.get('lastExapleTMS', self.lastExapleTMS)
            self.lastCleaningCycle = dic.get('lastCleaningCycle', self.lastCleaningCycle)
            if 'clusters' in dic.keys():
                self.clusters = [Cluster(**cl) for cl in dic['clusters']]
            if 'sleepClusters' in dic.keys():
                self.sleepClusters = [Cluster(**cl) for cl in dic['sleepClusters']]
            if 'unknownBuffer' in dic.keys():
                self.unknownBuffer = [Example(**ex) for ex in dic['unknownBuffer']]
        return self
    #
    def offline(self, examplesDf):
        self.clusters = self.minasAlgorith.training(examplesDf)
        self.sleepClusters = []
        self.unknownBuffer = []
    #
    def classify(self, ex: Example, clusters = None) -> (bool,Cluster,float,Example):
        if clusters is None:
            clusters = self.clusters + self.sleepClusters
        return self.minasAlgorith.classify(ex, clusters)
    def online(self, stream, outStream = []):
        self.minasAlgorith.online(stream, clusters=self.clusters, sleepClusters=self.sleepClusters,
            unknownBuffer=self.unknownBuffer, knownCount=self.knownCount, noveltyIndex=self.noveltyIndex, outStream=outStream)
        return self
    def onlineProcessExample(self, item, outStream = []):
        assert len(self.clusters) > 0, 'Minas is not trained yet'
        self.exampleCount += 1
        self.lastExapleTMS = time.time_ns()
        processed = self.minasAlgorith.processExample(
            index=self.exampleCount, item=item, clusters=self.clusters, sleepClusters=self.sleepClusters,
            unknownBuffer=self.unknownBuffer, knownCount=self.knownCount, noveltyIndex=self.noveltyIndex,
            outStream=outStream
        )
        example, isClassified, cluster, dist, self.knownCount, self.noveltyIndex, self.lastCleaningCycle = processed
        return example, isClassified, cluster, dist
