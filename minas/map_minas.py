import dataclasses
import typing
import time
import itertools

import numpy as np
from numpy import linalg as LA
import pandas as pd
from sklearn.cluster import KMeans

from .example import Example, Vector
from .cluster import Cluster

def minDist(clusters, centers, item):
    assert type(clusters) is list or len(clusters) > 0, f'Expected clusters to be non empty list. Got {type(clusters)} => {clusters}'
    assert type(centers) is not list or type(centers) is np.array or len(clusters) > 0, f'Expected centers to be non empty numpy array. Got {type(centers)} => {centers}'
    assert type(item) is np.array or len(item) > 0, f'Expected item to be non empty numpy array. Got {type(item)} => {item}'
    assert type(clusters[0]) is Cluster, f'Expected clusters to be non empty Cluster list'
    try:
        assert hasattr(centers, 'shape') is not None, f'Expected centers to have shape. Got centers={centers}.'
        assert hasattr(item, 'shape') is not None, f'Expected item to have shape. Got item={item}.'
        assert centers.shape is not None, f'Expected centers to have shape. Got centers={centers}.'
        assert item.shape is not None, f'Expected item to have shape. Got item={item}.'
        assert centers.shape[1] == item.shape[0], f'Expected centers and item to have equivalent shape. Got centers={centers.shape}, item={item.shape}.'
    except Exception as ex:
        print('\n\nMin Dist ERROR', centers, item, '\n\n')
        raise Exception('Min Dist ERROR') from ex
    dists = LA.norm(centers - item, axis=1)
    d = dists.min()
    cl = clusters[ dists.tolist().index(d) ]
    return d, cl
def mkCenters(clusters):
    return np.array([cl.center for cl in clusters])

def clustering(unknownBuffer, label=None, MAX_K_CLUSTERS=100, REPR_TRESHOLD=20):
    df = pd.DataFrame(unknownBuffer).drop_duplicates()
    if len(df) == 0:
        return []
    n_samples = len(df)
    n_clusters = min(MAX_K_CLUSTERS, n_samples // REPR_TRESHOLD)
    if n_clusters < n_samples:
        n_clusters = n_samples
    kmeans = KMeans(n_clusters=n_clusters)
    kmeans.fit(df)
    newClusters = [Cluster(center=centroid, label=label, n=0, maxDistance=0, latest=0) for centroid in kmeans.cluster_centers_]
    return newClusters

def minasOnline(exampleSource, inClusters=[]):
    RADIUS_FACTOR = 1.1
    EXTENTION_FACTOR = 3
    BUFF_FULL = 100
    MAX_K_CLUSTERS = 100
    REPR_TRESHOLD = 20
    CLEANUP_WINDOW = 100
    #
    unknownBuffer = []
    clusters=[cl for cl in inClusters]
    centers = mkCenters(clusters)
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
        d, cl = minDist(clusters, centers, example.item)
        if (d / max(1.0, cl.maxDistance)) <= RADIUS_FACTOR:
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
                    for sleepExample in unknownBuffer:
                        d, cl = minDist(sleepClusters, centers, sleepExample.item)
                        if (d / max(1.0, cl.maxDistance)) <= RADIUS_FACTOR:
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
                    newClusters = clustering([ ex.item for ex in unknownBuffer ])
                    temp_examples = {cl: [] for cl in newClusters}
                    for sleepExample in unknownBuffer:
                        d, cl = minDist(newClusters, sleepExample.item)
                        cl.maxDistance = max(cl.maxDistance, d)
                        cl.latest = counter
                        cl.n += 1
                        temp_examples[cl].append((sleepExample, d))
                    for ncl in newClusters:
                        if ncl.n < 2: continue
                        distances = [ d for ex, d in temp_examples[ncl] ]
                        if len(distances) == 0: continue
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
                        if distCl2Cl / max(1.0, nearCl2Cl.maxDistance) < EXTENTION_FACTOR or distCl2Cl / max(sameLabelDists) < 2:
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

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        end = i + n
        if end + i > len(l):
            end = len(l)
            yield l[i:end]
            break
        if end > len(l):
            break
        yield l[i:end]

def minasOffline(examplesDf):
    RADIUS_FACTOR = 1.1
    MAX_K_CLUSTERS = 50
    REPR_TRESHOLD = 5
    #
    clusters = []
    groupSize = MAX_K_CLUSTERS * REPR_TRESHOLD
    for label, group in examplesDf.groupby('label'):
        group = list(group['item'])
        # print('grouped', label, len(group), 'groupSize', groupSize)
        for chunk in chunks(group, groupSize):
            unknownBuffer = chunk
            # print('grouped', label, len(group), len(unknownBuffer))
            newClusters = clustering(unknownBuffer, label=label)
            temp_examples = {cl: [] for cl in newClusters}
            for sleepExample in unknownBuffer:
                centers = mkCenters(newClusters)
                d, cl = minDist(newClusters, centers, sleepExample)
                cl.maxDistance = max(cl.maxDistance, d)
                cl.n += 1
                temp_examples[cl].append((sleepExample, d))
            for ncl in newClusters:
                if ncl.n < 2 or cl.maxDistance <= 0:
                    continue
                #
                clusters.append(ncl)
            # 
        # 
    return clusters
# 
