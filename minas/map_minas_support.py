import dataclasses
import typing
import time

import numpy as np
import pandas as pd
from numba import jit
from sklearn.cluster import KMeans
from sklearn.externals import joblib
import dask
import dask.dataframe as dd

from .example import Example, Vector
from .cluster import Cluster

def mkClass(label):
    return dict(label=label, mu=np.random.random_sample((2,)), sigma=np.random.random_sample((2,)))
def nextExample(klass):
    return Example(label=klass['label'], item=np.random.normal(klass['mu'], klass['sigma']))

def sampleClasses():
    return list(map(mkClass, ['zero', 'one', 'duo', 'tri']))
def sampleClusters(classes):
    clusters = []
    for cl in classes:
        dist = sum(cl['sigma'])
        cluster = Cluster(
            center=cl['mu'],
            label=cl['label'],
            latest=0,
            n=1,
            meanDistance=dist,
            sumDistance=dist,
            rolingVarianceSum=dist,
            stdDev=dist,
        )
        clusters.append(cluster)
    return clusters
def nextRandExample(classes=[]):
    return nextExample(np.random.choice(classes) )
def randExamplesIter(classes=[]):
    while True:
        yield nextRandExample(classes=[])
def loopExamplesIter(classes=[]):
    i = 0
    while len(classes) > 0:
        yield nextExample(classes[i])
        i = (i + 1) % len(classes)
#

def metaMinas(minasMaping):
    status = dict(
        known = 0,
        unknown = 0,
        cleanup = 0,
        fallback = 0,
        recurenceDetection = 0,
        recurence = 0,
        noveltyDetection = 0,
    )
    sentinel = object()
    while minasMaping:
        o = next(minasMaping, sentinel)
        if o == sentinel:
            break
        if '[CLASSIFIED]' in o:
            status['known'] += 1
        elif '[UNKNOWN]' in o:
            status['unknown'] += 1
        elif '[cleanup]' in o:
            status['cleanup'] += 1
        elif '[fallback]' in o:
            status['fallback'] += 1
        elif '[recurenceDetection]' in o:
            status['recurenceDetection'] += 1
        elif '[noveltyDetection]' in o:
            status['noveltyDetection'] += 1
        elif '[Recurence]' in o:
            status['recurence'] += 1
        else: 
            yield o
    else:
        yield 'Stream Done'
    print(status)
#


@jit(nopython=True)
def minDistJit(zip_centers_ids, item):
    minD: float = 0.0
    clId: int = 0
    for center, _id in zip_centers_ids:
        d = np.sum((center - item) ** 2) ** (1/2)
        if minD == 0 or minD > d:
            minD, clId = d, _id
    return minD, clId
def minDistNumba(clusters, item: Vector):
    centers = [ (cl.center, id(cl)) for cl in clusters ]
    d, clId = minDistJit(centers, item)
    for cl in clusters:
        if id(cl) == clId:
            return d, cl

# def clusteringDask(unknownBuffer, label=None, MAX_K_CLUSTERS=100, REPR_TRESHOLD=20):
#     df = pd.DataFrame(unknownBuffer).drop_duplicates()
#     if len(df) == 0:
#         return []
#     n_clusters = min(MAX_K_CLUSTERS, len(unknownBuffer) // ( 3 * REPR_TRESHOLD))
#     if n_clusters == 0:
#         n_clusters = len(unknownBuffer)
#     ddf = dd.from_pandas(df, npartitions=8)
#     with joblib.parallel_backend('dask'):
#         kmeans = KMeans(n_clusters=n_clusters)
#         kmeans.fit(df)
#     newClusters = [Cluster(center=centroid, label=label, n=0, maxDistance=0, latest=0) for centroid in kmeans.cluster_centers_]
#     return newClusters