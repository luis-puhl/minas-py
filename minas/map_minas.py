import dataclasses
import typing
import time

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from .example import Example, Vector
from .cluster import Cluster

def mkClass(label): return dict(label=label, mu=np.random.random_sample((2,)), sigma=np.random.random_sample((2,)))
def nextExample(klass): return Example(label=klass['label'], item=np.random.normal(klass['mu'], klass['sigma']))


def sampleClasses():
    return list(map(mkClass, ['zero', 'one', 'duo', 'tri']))
def nextRandExample(classes=[]): return nextExample(np.random.choice(classes) )
def randExamplesIter(classes=[]):
    while True:
        yield nextRandExample(classes=[])
def loopExamplesIter(classes=[]):
    i = 0
    while True:
        yield nextExample(classes[i])
        i = (i + 1) % len(classes)
# 
def distKlass(ex, classes=[]): return map(lambda cl: (sum((cl['mu'] - ex.item) ** 2) ** 1/2, cl), classes)
def minDistKlass(ex, classes=[]): return min(distKlass(ex, classes), key=lambda x: x[0])


def dist(ex, clusters=[]):
    if len(clusters) == 0:
        return []
    return map(lambda cl: (sum((cl.center - ex.item) ** 2) ** 1/2, cl), clusters)

def minDist(ex, clusters=[]): return min(dist(ex, clusters), key=lambda x: x[0])

import itertools

from sklearn.cluster import KMeans
import numpy as np
import pandas as pd

def minDist(clusters, item):
    dists = map(lambda cl: (sum((cl.center - item) ** 2) ** (1/2), cl), clusters)
    d, cl = min(dists, key=lambda x: x[0])
    return d, cl
def clustering(unknownBuffer, label=None, MAX_K_CLUSTERS=100, REPR_TRESHOLD=20):
    df = pd.DataFrame([ex.item for ex in unknownBuffer])
    n_clusters = min(MAX_K_CLUSTERS, len(unknownBuffer) // ( 3 * REPR_TRESHOLD))
    kmeans = KMeans(n_clusters=n_clusters)
    kmeans.fit(df)
    newClusters = [Cluster(center=centroid, label=label, n=0, maxDistance=0, latest=0) for centroid in kmeans.cluster_centers_]
    return newClusters

def minasOnline(exampleSource, inClusters=[], minDist=minDist, clustering=clustering):
    RADIUS_FACTOR = 1.1
    BUFF_FULL = 100
    MAX_K_CLUSTERS = 100
    REPR_TRESHOLD = 20
    CLEANUP_WINDOW = 100
    #
    unknownBuffer = []
    clusters=[cl for cl in inClusters]
    sleepClusters = []
    counter = 0
    noveltyIndex = 0
    sentinel = object()
    while True:
        example = next(exampleSource, sentinel)
        if example is sentinel:
            yield 'done'
            return
        example = Example(item=example.item)
        counter += 1
        example.timestamp = time.time_ns()
        example.n = counter
        # dists = map(lambda cl: (sum((cl.center - example.item) ** 2) ** 1/2, cl), clusters)
        # d, cl = min(dists, key=lambda x: x[0])
        d, cl = minDist(clusters, example.item)
        if d / cl.maxDistance <= RADIUS_FACTOR:
            cl.maxDistance = max(cl.maxDistance, d)
            cl.latest = counter
            cl.n += 1
            yield f"[CLASSIFIED] {example.n}: {cl.label}"
        else:
            unknownBuffer.append(example)
            yield f"[UNKNOWN] {example.n}: {example.item}"
            if len(unknownBuffer) > BUFF_FULL:
                if len(sleepClusters) > 0:
                    yield f'[recurenceDetection] unk={len(unknownBuffer)}, sleep={len(sleepClusters)}'
                    # recurenceDetection
                    for sleepExample in unknownBuffer:
                        # sleepDists = list(map(lambda cl: (sum((cl.center - sleepExample.item) ** 2) ** 1/2, cl), sleepClusters))
                        # d, cl = min(sleepDists, key=lambda x: x[0])
                        d, cl = minDist(sleepClusters, sleepExample.item)
                        if d / cl.maxDistance <= 1.1:
                            cl.maxDistance = max(cl.maxDistance, d)
                            cl.latest = counter
                            unknownBuffer.remove(sleepExample)
                            yield f"[CLASSIFIED] {sleepExample.n}: {cl.label}"
                            if cl in sleepClusters:
                                clusters.append(cl)
                                sleepClusters.remove(cl)
                                yield f"[Recurence] {cl.label}"
                if len(unknownBuffer) % (BUFF_FULL // 10) == 0:
                    yield '[noveltyDetection]'
                    # noveltyDetection
                    # df = pd.DataFrame([ex.item for ex in unknownBuffer])
                    # n_clusters = min(MAX_K_CLUSTERS, len(unknownBuffer) // ( 3 * REPR_TRESHOLD))
                    # kmeans = KMeans(n_clusters=n_clusters)
                    # kmeans.fit(df)
                    # newClusters = [Cluster(center=centroid, label=None, n=0, maxDistance=0, latest=0) for centroid in kmeans.cluster_centers_]
                    newClusters = clustering(unknownBuffer)
                    temp_examples = {cl: [] for cl in newClusters}
                    for sleepExample in unknownBuffer:
                        # dists = map(lambda cl: (sum((cl.center - sleepExample.item) ** 2) ** 1/2, cl), newClusters)
                        # d, cl = min(dists, key=lambda x: x[0])
                        d, cl = minDist(newClusters, sleepExample.item)
                        cl.maxDistance = max(cl.maxDistance, d)
                        cl.latest = counter
                        cl.n += 1
                        temp_examples[cl].append((sleepExample, d))
                    for ncl in newClusters:
                        if ncl.n < 2: continue
                        distances = [ d for ex, d in temp_examples[ncl] ]
                        if len(distances) == 0: continue
                        # distsCl2Cl = map(lambda cl: (sum((cl.center - ncl.center) ** 2) ** 1/2, cl), clusters + sleepClusters)
                        # distCl2Cl, nearCl2Cl = min(distsCl2Cl, key=lambda x: x[0])
                        distCl2Cl, nearCl2Cl = minDist(clusters + sleepClusters, ncl.center)
                        #
                        mean = sum(distances) / len(distances)
                        devianceSqrSum = sum([(d - mean) **2 for d in distances])
                        var = devianceSqrSum / len(distances)
                        stdDevDistance = var **0.5
                        silhouetteFn = lambda a, b: (b - a) / max([a, b])
                        silhouette = silhouetteFn(stdDevDistance, distCl2Cl)
                        if silhouette < 0: continue
                        # 
                        sameLabel = [ cl for cl in clusters + sleepClusters if cl.label ==  nearCl2Cl.label ]
                        sameLabelDists = [ sum((cl1.center - cl2.center) ** 2) ** (1/2) for cl1, cl2 in itertools.combinations(sameLabel, 2) ]
                        #
                        if distCl2Cl / nearCl2Cl.maxDistance < 1.1 or distCl2Cl / max(sameLabelDists) < 2:
                            yield f'Extention {nearCl2Cl.label}'
                            ncl.label = nearCl2Cl.label
                        else:
                            label = 'Novelty {}'.format(noveltyIndex)
                            ncl.label = label
                            yield label
                            noveltyIndex += 1
                        clusters.append(ncl)
                        for ex, d in temp_examples[ncl]:
                            if ex in unknownBuffer:
                                yield f"[CLASSIFIED] {ex.n}: {ncl.label}"
                                unknownBuffer.remove(ex)
        if counter % CLEANUP_WINDOW == 0:
            yield '[cleanup]'
            for ex in unknownBuffer:
                if counter - ex.n < 3 * CLEANUP_WINDOW:
                    unknownBuffer.remove(ex)
            for cl in clusters:
                if counter - cl.latest < 2 * CLEANUP_WINDOW:
                    sleepClusters.append(cl)
                    clusters.remove(cl)
            if len(clusters) == 0:
                yield f'[fallback] {len(sleepClusters)} => clusters'
                # fallback 
                clusters.extend(sleepClusters)
                sleepClusters.clear()
            #
        #
    #
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

def minasOffline(examplesDf):
    RADIUS_FACTOR = 1.1
    BUFF_FULL = 100
    MAX_K_CLUSTERS = 100
    REPR_TRESHOLD = 20
    #
    clusters = []
    groupSize = MAX_K_CLUSTERS * REPR_TRESHOLD
    for label, group in examplesDf.groupby('label'):
        for chunk in range(0, len(group), groupSize):
            subgroup = group[chunk:chunk + groupSize]
            unknownBuffer = list(subgroup['item'])
            df = pd.DataFrame(unknownBuffer)
            n_clusters = min(MAX_K_CLUSTERS, len(unknownBuffer) // ( 3 * REPR_TRESHOLD))
            kmeans = KMeans(n_clusters=n_clusters)
            kmeans.fit(df)
            newClusters = [Cluster(center=centroid, label=label, n=0, maxDistance=0, latest=0) for centroid in kmeans.cluster_centers_]
            temp_examples = {cl: [] for cl in newClusters}
            for sleepExample in unknownBuffer:
                dists = map(lambda cl: (sum((cl.center - sleepExample) ** 2) ** 1/2, cl), newClusters)
                d, cl = min(dists, key=lambda x: x[0])
                cl.maxDistance = max(cl.maxDistance, d)
                cl.n += 1
                temp_examples[cl].append((sleepExample, d))
            for ncl in newClusters:
                if ncl.n < 2: continue
                #
                clusters.append(ncl)
    return clusters
# 
