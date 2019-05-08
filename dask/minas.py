import time
import dataclasses
import typing
import os

import yaml
from dask.distributed import Client

from timed import Timed
from example import Example, Vector
from minas_algo import MinasAlgorith, ClusterList, ExampleList

@dataclasses.dataclass
class Minas:
    exampleCount: int = 0
    knownCount: int = 0
    noveltyIndex: int = 0
    lastExapleTMS: int = 0
    lastCleaningCycle: int = 0
    clusters: ClusterList = None
    sleepClusters: ClusterList = None
    unknownBuffer: ExampleList = None
    minasAlgorith: MinasAlgorith = MinasAlgorith()
    daskClient: typing.Union[Client, None] = None
    def asDict(self):
        asDictMap = lambda l: [x.asDict for x in l]
        return {
            'exampleCount': self.exampleCount, 'knownCount': self.knownCount, 'diff': self.exampleCount - self.knownCount,
            'noveltyIndex': self.noveltyIndex,
            'lastExapleTMS': self.lastExapleTMS, 'lastCleaningCycle': self.lastCleaningCycle,
            'clusters': asDictMap(self.clusters), 'sleepClusters': asDictMap(self.sleepClusters),
            'unknownBuffer': asDictMap(self.unknownBuffer),}
    def __repr__(self):
        return 'Minas({!r})'.format(self.asDict())
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
        self.clusters = self.minasAlgorith.training(examplesDf, daskClient=self.daskClient).compute()
        self.sleepClusters = []
        self.unknownBuffer = []
    #
    def online(self, stream):
        for example in stream:
            if example is None:
                break
            self.onlineProcessExample(example) # custo 1000 -> 10
        return self
    def onlineProcessExample(self, item, outStream = []):
        assert len(self.clusters) > 0, 'Minas is not trained yet'
        self.exampleCount += 1
        self.lastExapleTMS = time.time_ns()
        example, isClassified, cluster, dist, knownCount, noveltyIndex, lastCleaningCycle = self.minasAlgorith.processExample(
            item=item, clusters=self.clusters, sleepClusters=self.sleepClusters,
            unknownBuffer=self.unknownBuffer, knownCount=self.knownCount, noveltyIndex=self.noveltyIndex,
            outStream=outStream
        )
        self.knownCount = knownCount
        self.noveltyIndex = noveltyIndex
        self.lastCleaningCycle = lastCleaningCycle
        return example, isClassified, cluster, dist
