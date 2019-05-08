import time
import dataclasses
import typing
import types
import os
import inspect

import yaml
import pandas as pd
import numpy as np
import scipy
from sklearn.externals import joblib
from sklearn.cluster import KMeans
from sklearn.datasets import fetch_covtype
from dask import delayed
from dask.distributed import Client

from timed import Timed
from example import Example, Vector
from minas_algo import MinasAlgorith, ClusterList, ExampleList
from minas import Minas

tm = Timed()
timed = tm.timed
TimedMinasAlgorith = tm.timedClass(MinasAlgorith)

class NoDealayed(Minas):
    @timed
    def NDoffline(self, examplesDf):
        @timed
        def NDclosestCluster(item, clusters):
            dist, nearCl = min( ((cl.dist(item), cl) for cl in clusters), key=lambda x: x[0])
            return dist, nearCl
        @timed
        def NDclustering(examples, label=None):
            kmeans = KMeans( n_clusters = min(CONSTS.k, int(len(examples) / (3 * CONSTS.representationThr))), n_jobs=-1)
            kmeans.fit(examples)
            return [Cluster(center=centroid, label=label) for centroid in kmeans.cluster_centers_]
        @timed
        def NDtrainGroup(label, group):
            clusters = NDclustering(group, label)
            for ex in group:
                dist, nearCl = NDclosestCluster(ex, clusters)
                nearCl += Example(ex)
            return [cluster for cluster in clusters if cluster.n > CONSTS.representationThr]
        #
        clusters = []
        for label, group in examplesDf.groupby('label'):
            clusters += NDtrainGroup(label, pd.DataFrame(iter(group['item'])))
        self.clusters.extend(clusters)
        return clusters
#

dataset = fetch_covtype()

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
total = len(dataset.data)
print('sizeof dataset', sizeof_fmt(dataset.data.nbytes), 'len', total)
print('dataset', dataset.data[0], dataset.target[0])

onePercent = int(total*0.01)
onPercentDataFrame = pd.DataFrame(map(lambda x: {'item': x[0], 'label': x[1]}, zip(dataset.data[:onePercent], dataset.target[:onePercent])))
tenPercent = int(total*0.10)
tenPercentDataFrame = pd.DataFrame(map(lambda x: {'item': x[0], 'label': x[1]}, zip(dataset.data[:tenPercent], dataset.target[:tenPercent])))
fivePercent = int(total*0.05)
fivePercentDataIterator = zip(dataset.data[onePercent+1:fivePercent], dataset.target[onePercent+1:fivePercent])
allDataIterator = zip(dataset.data, dataset.target)

def testRun(model, trainingSet, testSet):
    model.offline(trainingSet)
    i, pos, neg, unk = 0, 0, 0, 0
    outStream = []
    for x, target in testSet:
        example, isClassified, cluster, dist = model.onlineProcessExample(x, outStream)
        i += 1
        if not isClassified:
            unk += 1
            continue
        if example.label == target:
            pos += 1
        else:
            neg += 1
    statisticSummary = tm.statisticSummary()
    return model, statisticSummary, pos, neg, unk, i, outStream
#

def terminalRun(modelI, trainSet, testSet):
    print('\nterminalRun')
    init = time.time()
    model, statisticSummary, pos, neg, unk, i, outStream = testRun(modelI, trainSet, testSet)
    i = max(i, 1)
    print(outStream)
    print('positive: {p}({pp:.2%}), negative: {n}({nn:.2%}), unknown: {u}({uu:.2%})\n'.format(p=pos, pp=pos/i, n=neg, nn=neg/i, u=unk, uu=unk/i))
    print(f'testRun(({modelI.__name__}) allDataIterator ', time.time() - init, 's')
    print('statisticSummary', statisticSummary.describe())

# client = Client('tcp://localhost:8786')
client = Client()
trainSet, testSet = (onPercentDataFrame, fivePercentDataIterator)
for i in range(3):
    for modelI in [Minas(minasAlgorith=TimedMinasAlgorith(), daskClient=client), NoDealayed()]:
        try:
            terminalRun(modelI, trainSet, testSet)
        except Exception as ex:
            pass
# 
# client.close()

def heavyTest():
    trainSet, testSet = (tenPercentDataFrame, allDataIterator)
    for i in range(3):
        for modelI in [Minas, NoDealayed]:
            terminalRun(modelI, trainSet, testSet)
