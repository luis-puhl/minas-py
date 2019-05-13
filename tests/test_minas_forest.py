import unittest
import logging
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
from minas.minas_dask import MinasAlgorithJoblib, MinasAlgorithDaskKmeans, MinasAlgorithDaskKmeansScatter

from .plots import *

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

class MinasForestCoverDataSetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # setupLog()
        with open('logging.conf.yaml', 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        logging.config.dictConfig(config)

        dataset = fetch_covtype()
        cls.dataset = dataset

        total = len(dataset.data)
        print('sizeof dataset', sizeof_fmt(dataset.data.nbytes), 'len', total)
        print('dataset', dataset.data[0], dataset.target[0])

        zipToMap = lambda x: {'item': x[0], 'label': str(x[1])}

        onePercent = int(total*0.01)
        baseMap = map(zipToMap, zip(dataset.data[:onePercent], dataset.target[:onePercent]))
        cls.onPercentDataFrame = pd.DataFrame(baseMap)
        fivePercent = int(total*0.05)
        fivePercentZip = zip(dataset.data[onePercent+1:fivePercent], map(str, dataset.target[onePercent+1:fivePercent]))
        cls.fivePercentDataIterator = list(fivePercentZip)

        tenPercent = int(total*0.10)
        baseMap = map(zipToMap, zip(dataset.data[:tenPercent], dataset.target[:tenPercent]))
        cls.tenPercentDataFrame = pd.DataFrame(baseMap)
        cls.allDataIterator = list(zip(dataset.data, map(str, dataset.target)))
    def setUp(self):
        self.timed = Timed()
        self.TimedMinasAlgorith = self.timed.timedClass(MinasAlgorith)
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
        filename = 'run/forest-cover-type-dataset/store-test.yaml'
        minas = MinasBase(minasAlgorith=self.TimedMinasAlgorith())
        minas.offline(self.onPercentDataFrame)
        
        clusters = len(minas.clusters)
        sleepClusters = len(minas.sleepClusters)
        unknownBuffer = len(minas.unknownBuffer)
        minas.storeToFile(filename)
        minas.restoreFromFile(filename)
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
        minas.storeToFile(filename)
        minas.restoreFromFile(filename)
        self.assertEqual(clusters, len(minas.clusters))
        self.assertEqual(sleepClusters, len(minas.sleepClusters))
        self.assertEqual(unknownBuffer, len(minas.unknownBuffer))

    def test_small_dataset(self):
        minas = MinasBase(minasAlgorith=self.TimedMinasAlgorith())
        kwargs = {
            'name': 'test_small_dataset',
            'trainSet': self.onPercentDataFrame,
            'testSet': self.fivePercentDataIterator,
            'minas': minas
        }
        self.runDataset(**kwargs)
    def test_small_dataset_MinasAlgorithJoblib(self):
        TimedMinasAlgorith = self.timed.timedClass(MinasAlgorithJoblib)
        minas = MinasBase(minasAlgorith=self.TimedMinasAlgorith())
        kwargs = {
            'name': 'test_small_dataset_MinasAlgorithJoblib',
            'trainSet': self.onPercentDataFrame,
            'testSet': self.fivePercentDataIterator,
            'minas': minas
        }
        self.runDataset(**kwargs)
    def test_small_dataset_MinasAlgorithDaskKmeans(self):
        TimedMinasAlgorith = self.timed.timedClass(MinasAlgorithDaskKmeans)
        minas = MinasBase(minasAlgorith=self.TimedMinasAlgorith())
        kwargs = {
            'name': 'test_small_dataset_MinasAlgorithDaskKmeans',
            'trainSet': self.onPercentDataFrame,
            'testSet': self.fivePercentDataIterator,
            'minas': minas
        }
        self.runDataset(**kwargs)
    def test_small_dataset_MinasAlgorithDaskKmeansScatter(self):
        TimedMinasAlgorith = self.timed.timedClass(MinasAlgorithDaskKmeansScatter)
        minas = MinasBase(minasAlgorith=self.TimedMinasAlgorith())
        kwargs = {
            'name': 'test_small_dataset_MinasAlgorithDaskKmeansScatter',
            'trainSet': self.onPercentDataFrame,
            'testSet': self.fivePercentDataIterator,
            'minas': minas
        }
        self.runDataset(**kwargs)
    def test_zz_big_dataset(self):
        minas = MinasBase(minasAlgorith=self.TimedMinasAlgorith())
        kwargs = {
            'name': 'test_zz_big_dataset',
            'trainSet': self.tenPercentDataFrame,
            'testSet': self.allDataIterator,
            'minas': minas
        }
        self.runDataset(**kwargs)
    def runDataset(self, name, trainSet, testSet, minas):
        print(f"\n{20*'='} {name} {20*'='}")
        directory = 'run/forest-cover-type-dataset/' + name + '/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        rootLogger = logging.getLogger()
        logHandler = logging.FileHandler(directory + 'run.log')
        logHandler.formatter = rootLogger.handlers[0].formatter
        rootLogger.addHandler(logHandler)
        elapsed = []
        plotSet = map(lambda x: Example(item=x[0][:2], label=x[1]), trainSet[:min(1000, int(len(trainSet)*0.1))])
        plotExamples2D(directory, '1-training_set', plotSet, [])
        for _ in range(3):
            i, pos, neg, unk = 0, 0, 0, 0
            init = time.time()
            
            minas.offline(trainSet)
            plotExamples2D(directory, '2-offline_clusters', [], minas.clusters)
            
            minas.storeToFile(directory + 'minas_offline.yaml')
            logging.info('Loading model')
            minas.restoreFromFile(directory + 'minas_offline.yaml')
            logging.info(str(minas))
            minas.minasAlgorith.checkTraining(trainSet, minas.clusters)
            
            outStream = []
            events = []
            plotSet = []
            for x, target in testSet:
                eventInit = time.time_ns()
                example, isClassified, cluster, dist = minas.onlineProcessExample(x, outStream)
                events.append(time.time_ns() - eventInit)
                i += 1
                if not isClassified:
                    unk += 1
                    example.label = 'unk'
                elif example.label == target:
                    pos += 1
                    example.label = 'pos'
                else:
                    neg += 1
                    example.label = 'neg'
                if len(plotSet) <= 1000:
                    plotSet.append(example)
            el = time.time() - init
            elapsed.append(el)
            
            minas.storeToFile(directory + 'minas_online.yaml')
            plotExamples2D(directory, '5-online_clusters', [], minas.clusters)
            plotExamples2D(directory, '6-online_resutls', plotSet, minas.clusters)
            
            self.assertEqual(pos + neg + unk, i, 'Every sample must have a result')
            i = max(i, 1)
            resultMsg = 'positive: {p}({pp:.2%}), negative: {n}({nn:.2%}), unknown: {u}({uu:.2%}) {el:.3f}s'
            resultMsgVals = dict(p=pos, pp=pos/i, n=neg, nn=neg/i, u=unk, uu=unk/i, el=el)
            print(resultMsg.format_map(resultMsgVals))
        avg = sum(elapsed) / max(len(elapsed), 1)
        print(name, map(lambda el:'{:.3f}s'.format(el), elapsed), '{:.3f}s'.format(avg))
        statisticSummary = self.timed.statisticSummary()
        logging.info(f'=========== Timed Functions Summary {name} ===========\n{statisticSummary.describe()}')
        fig, ax = self.timed.mkTimedResumePlot()
        plt.savefig(directory + 'timed_run.png')
        plt.close(fig)

if __name__ == '__main__':
    unittest.main()
