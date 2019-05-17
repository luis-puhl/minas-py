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
