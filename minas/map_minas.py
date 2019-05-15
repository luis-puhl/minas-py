import dataclasses
import typing
import time

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

Vector = typing.Union[list, np.ndarray, typing.Any, None]

@dataclasses.dataclass(eq=False)
class Example():
    item: Vector = dataclasses.field(repr=False)
    label: typing.Union[str, None] = None
    timestamp: int = time.time_ns()
    tries: int = 0

@dataclasses.dataclass
class Cluster():
    center: Vector = dataclasses.field(repr=False)
    latest: int = 0
    label: typing.Union[str, None] = None
    n: int = 0
    maxDist: float = 0.0
    temp_examples=[]
    def __eq__(self, other):
        return self.temp_examples == other.temp_examples

def mkClass(label): return dict(label=label, mu=np.random.random_sample((2,)), sigma=np.random.random_sample((2,)))
def nextExample(klass): return Example(label=klass['label'], item=np.random.normal(klass['mu'], klass['sigma']))


def sampleClasses():
    return list(map(mkClass, ['zero', 'one', 'duo', 'tri']))
def nextRandExample(classes=classes): return nextExample(np.random.choice(classes) )
def randExamplesIter(classes=classes):
    while True:
        yield nextRandExample(classes=classes)
def loopExamplesIter(classes=classes):
    i = 0
    while True:
        yield nextExample(classes[i])
        i = (i + 1) % len(classes)

def minasOnline(exampleSource, inClusters=[]):
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
        dists = map(lambda cl: (sum((cl.center - example.item) ** 2) ** 1/2, cl), clusters)
        d, cl = min(dists, key=lambda x: x[0])
        if d / cl.maxDist <= RADIUS_FACTOR:
            cl.maxDist = max(cl.maxDist, d)
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
                        sleepDists = list(map(lambda cl: (sum((cl.center - sleepExample.item) ** 2) ** 1/2, cl), sleepClusters))
                        if len(sleepDists) == 0: continue
                        d, cl = min(sleepDists, key=lambda x: x[0])
                        if d / cl.maxDist <= 1.1:
                            cl.maxDist = max(cl.maxDist, d)
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
                    df = pd.DataFrame([ex.item for ex in unknownBuffer])
                    n_clusters = min(MAX_K_CLUSTERS, len(unknownBuffer) // ( 3 * REPR_TRESHOLD))
                    kmeans = KMeans(n_clusters=n_clusters)
                    kmeans.fit(df)
                    newClusters = [Cluster(center=centroid, label=None, n=0, maxDist=0, latest=0) for centroid in kmeans.cluster_centers_]
                    temp_examples = {cl: [] for cl in newClusters}
                    for sleepExample in unknownBuffer:
                        dists = map(lambda cl: (sum((cl.center - sleepExample.item) ** 2) ** 1/2, cl), newClusters)
                        d, cl = min(dists, key=lambda x: x[0])
                        cl.maxDist = max(cl.maxDist, d)
                        cl.latest = counter
                        cl.n += 1
                        temp_examples[cl].append((sleepExample, d))
                    for ncl in newClusters:
                        if ncl.n < 2: continue
                        distances = [ d for ex, d in temp_examples[ncl] ]
                        if len(distances) == 0: continue
                        distsCl2Cl = map(lambda cl: (sum((cl.center - ncl.center) ** 2) ** 1/2, cl), clusters + sleepClusters)
                        distCl2Cl, nearCl2Cl = min(distsCl2Cl, key=lambda x: x[0])
                        #
                        mean = sum(distances) / len(distances)
                        devianceSqrSum = sum([(d - mean) **2 for d in distances])
                        var = devianceSqrSum / len(distances)
                        stdDevDistance = var **0.5
                        silhouetteFn = lambda a, b: (b - a) / max([a, b])
                        silhouette = silhouetteFn(stdDevDistance, distCl2Cl)
                        if silhouette < 0: continue
                        # 
                        if distCl2Cl / nearCl2Cl.maxDist < 10:
                            yield f'Extention {nearCl2Cl.label}'
                            ncl.label = nearCl2Cl.label
                        else:
                            label = 'Novelty {}'.format(noveltyIndex)
                            ncl.label = label
                            yield label
                            noveltyIndex += 1
                        clusters.append(ncl)
                        for ex, d in temp_examples[ncl]:
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
