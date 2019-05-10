import unittest
import time
# import os

import pandas as pd
# import numpy as np
from sklearn.datasets import fetch_covtype
from dask.distributed import Client

from minas.timed import Timed
from minas.example import Example
from minas.cluster import Cluster
from minas.minas_base import MinasAlgorith, MinasBase

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

class MinasForestCoverDataSetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dataset = fetch_covtype()
        cls.dataset = dataset

        total = len(dataset.data)
        print('sizeof dataset', sizeof_fmt(dataset.data.nbytes), 'len', total)
        print('dataset', dataset.data[0], dataset.target[0])

        onePercent = int(total*0.01)
        cls.onPercentDataFrame = pd.DataFrame(map(lambda x: {'item': x[0], 'label': x[1]}, zip(dataset.data[:onePercent], dataset.target[:onePercent])))
        fivePercent = int(total*0.05)
        cls.fivePercentDataIterator = list(zip(dataset.data[onePercent+1:fivePercent], dataset.target[onePercent+1:fivePercent]))

        tenPercent = int(total*0.10)
        cls.tenPercentDataFrame = pd.DataFrame(map(lambda x: {'item': x[0], 'label': x[1]}, zip(dataset.data[:tenPercent], dataset.target[:tenPercent])))
        cls.allDataIterator = list(zip(dataset.data, dataset.target))
    def setUp(self):
        self.tm = Timed()
        self.TimedMinasAlgorith = self.tm.timedClass(MinasAlgorith)
        self.minas = MinasBase(minasAlgorith=self.TimedMinasAlgorith())
        self.i, self.pos, self.neg, self.unk = 0, 0, 0, 0
    def tearDown(self):
        pass

    def test_process_example(self):
        minas = MinasBase(minasAlgorith=self.TimedMinasAlgorith())
        minas.offline(self.onPercentDataFrame)
        for x, target in self.fivePercentDataIterator:
            example, isClassified, cluster, dist = minas.onlineProcessExample(x, [])
            self.assertIsInstance(dist, float)
            self.assertIsInstance(cluster, Cluster)
            self.assertIsInstance(isClassified, bool)
            self.assertIsInstance(example, Example)
            break
    def test_store(self):
        minas = MinasBase(minasAlgorith=self.TimedMinasAlgorith())
        minas.offline(self.onPercentDataFrame)
        
        clusters = len(minas.clusters)
        sleepClusters = len(minas.sleepClusters)
        unknownBuffer = len(minas.unknownBuffer)
        minas.storeToFile('run/forest')
        minas.restoreFromFile('run/forest')
        self.assertEqual(clusters, len(minas.clusters))
        self.assertEqual(sleepClusters, len(minas.sleepClusters))
        self.assertEqual(unknownBuffer, len(minas.unknownBuffer))

        for x, target in self.fivePercentDataIterator:
            example, isClassified, cluster, dist = minas.onlineProcessExample(x, [])
            self.assertIsInstance(dist, float)
            self.assertIsInstance(cluster, Cluster)
            self.assertIsInstance(isClassified, bool)
            self.assertIsInstance(example, Example)
        
        clusters = len(minas.clusters)
        sleepClusters = len(minas.sleepClusters)
        unknownBuffer = len(minas.unknownBuffer)
        minas.storeToFile('run/forest')
        minas.restoreFromFile('run/forest')
        self.assertEqual(clusters, len(minas.clusters))
        self.assertEqual(sleepClusters, len(minas.sleepClusters))
        self.assertEqual(unknownBuffer, len(minas.unknownBuffer))

    def test_small_dataset(self):
        self.runDataset(name='test_small_dataset', trainSet=self.onPercentDataFrame, testSet=self.fivePercentDataIterator)
    def test_zz_big_dataset(self):
        self.runDataset(name='test_zz_big_dataset', trainSet=self.tenPercentDataFrame, testSet=self.allDataIterator)
    def runDataset(self, name, trainSet, testSet):
        print(f"\n{20*'='} {name} {20*'='}")
        minas = MinasBase(minasAlgorith=self.TimedMinasAlgorith())
        elapsed = []
        for _ in range(3):
            i, pos, neg, unk = 0, 0, 0, 0
            init = time.time()
            minas.offline(trainSet)
            outStream = []
            events = []
            for x, target in testSet:
                eventInit = time.time_ns()
                example, isClassified, cluster, dist = minas.onlineProcessExample(x, outStream)
                events.append(time.time_ns() - eventInit)
                self.assertIsInstance(dist, float)
                self.assertIsInstance(cluster, Cluster)
                self.assertIsInstance(isClassified, bool)
                i += 1
                if not isClassified:
                    unk += 1
                    continue
                if example.label == target:
                    pos += 1
                else:
                    neg += 1
            el = time.time() - init
            elapsed.append(el)
            self.assertEqual(pos + neg + unk, i, 'Every sample must have a result')
            i = max(i, 1)
            print('positive: {p}({pp:.2%}), negative: {n}({nn:.2%}), unknown: {u}({uu:.2%}) {el:.3f}s'.format(p=pos, pp=pos/i, n=neg, nn=neg/i, u=unk, uu=unk/i, el=el))
        avg = sum(elapsed) / max(len(elapsed), 1)
        print(name, map(lambda el:'{:.3f}s'.format(el), elapsed), '{:.3f}s'.format(avg))
        statisticSummary = self.tm.statisticSummary()
        print('statisticSummary', statisticSummary.describe())


if __name__ == '__main__':
    unittest.main()
