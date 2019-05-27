import numpy as np
from minas.map_minas_support import *
np.random.seed(300)
classes = list(map(mkClass, range(1000)))
clusters = sampleClusters(classes)
inputStream = loopExamplesIter(classes)
examples = list(zip(range(200), inputStream))

def minDist(clusters, item):
    dists = map(lambda cl: (sum((cl.center - item) ** 2) ** (1/2), cl), clusters)
    d, cl = min(dists, key=lambda x: x[0])
    return d, cl
counter = 0
results = []
init = time.time()
for i, example in examples:
    counter += 1
    result = minDist(clusters, example.item)
    results.append(result)
elapsed = time.time() - init
len(results)
print(f'dist sq, sum, pqw\t{elapsed} seconds, consumed {counter} items, {int(counter / elapsed)} i/s')

# ----------------------------------------------------------------------------------------------------------
def minDist(clusters, item):
    dists = map(lambda cl: (np.linalg.norm(cl.center - item), cl), clusters)
    d, cl = min(dists, key=lambda x: x[0])
    return d, cl
counter = 0
results = []
init = time.time()
for i, example in examples:
    counter += 1
    result = minDist(clusters, example.item)
    results.append(result)
elapsed = time.time() - init
len(results)
print(f'dist linalg.norm\t{elapsed} seconds, consumed {counter} items, {int(counter / elapsed)} i/s')

# ----------------------------------------------------------------------------------------------------------
from numpy import linalg as LA

centers = np.array([cl.center for cl in clusters])
counter = 0
results = []
init = time.time()
for i, example in examples:
    counter += 1
    dists = LA.norm(centers - example.item, axis=1)
    d = dists.min()
    cl = clusters[ dists.tolist().index(d) ]
    result = (d, cl)
    results.append(result)
elapsed = time.time() - init
len(results)
print(f'dist vector.norm\t{elapsed} seconds, consumed {counter} items, {int(counter / elapsed)} i/s')


# $ python vector_minas.py
# dist sq, sum, pqw       1.135091781616211 seconds, consumed 200 items, 176 i/s
# dist linalg.norm        1.743095874786377 seconds, consumed 200 items, 114 i/s
# dist vector.norm        0.025014877319335938 seconds, consumed 200 items, 7995 i/s