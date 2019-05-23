def minDist(clusters, item):
    dists = map(lambda cl: (sum((cl.center - item) ** 2) ** (1/2), cl), clusters)
    d, cl = min(dists, key=lambda x: x[0])
    return d, cl

# %%time
import numpy as np
from minas.map_minas_support import *
np.random.seed(300)

# cria lista de meta-classes contendo etiqueta, centro e desvio padrão
classes = list(map(mkClass, range(1000)))

# a partir das classes, cria objetos <minas.Cluster>
clusters = sampleClusters(classes)

# a partir das classes, cria objetos <minas.Example>
inputStream = loopExamplesIter(classes)

# %%time
init = time.time()
counter = 0
while time.time() - init < 1.0:
    counter += 1
    example = next(inputStream)
    minDist(clusters, example.item)
elapsed = time.time() - init
print(f'minasOnline testSamples {elapsed} seconds, consumed {counter} items, {int(counter / elapsed)} i/s')

# %%time
examples = list(zip(range(200), inputStream))


# %%time
%%timeit
counter = 0
results = []
init = time.time()
for i, example in examples:
    counter += 1
    result = minDist(clusters, example.item)
    results.append(result)
elapsed = time.time() - init
len(results)
print(f'minasOnline testSamples {elapsed} seconds, consumed {counter} items, {int(counter / elapsed)} i/s')

# %%time
import dask.distributed
cli = dask.distributed.Client('tcp://192.168.15.14:8786', )
cli

# %%time
import dask
import dask.bag as db

@dask.delayed
def minDistDelayed(clusters, item):
    dists = map(lambda cl: (sum((cl[1] - item) ** 2) ** (1/2), cl[0]), clusters)
    d, cl = min(dists, key=lambda x: x[0])
    return d, cl
# init = time.time()
# counter = 0
# simpleClusters = [(id(cl), cl.center) for cl in clusters]
# simpleClusters = db.from_sequence(simpleClusters)
# cli.persist(simpleClusters)
# simpleClusters = cli.scatter(simpleClusters)
# results = []
# while time.time() - init < 1.0:
#     counter += 1
#     example = next(inputStream)
#     results.append(minDistDelayed(simpleClusters, example.item))
# dask.compute(results)
# elapsed = time.time() - init
# print(f'minasOnline testSamples {elapsed} seconds, consumed {counter} items, {int(counter / elapsed)} i/s')

# %%time
counter = 0
simpleClusters = [(id(cl), cl.center) for cl in clusters]
simpleClusters = db.from_sequence(simpleClusters)
cli.persist(simpleClusters)
simpleClusters = cli.scatter(simpleClusters)
results = []
init = time.time()
for i, example in examples:
    counter += 1
    result = minDistDelayed(simpleClusters, example.item)
    results.append(result)
elapsed = time.time() - init
print(f'loop {elapsed} seconds')
init = time.time()
dask.compute(results)
elapsed = time.time() - init
print(f'minasOnline testSamples {elapsed} seconds, consumed {counter} items, {int(counter / elapsed)} i/s')

# %%time
import dask
import dask.bag as db

def minDistSimple(clusters, item):
    dists = map(lambda cl: (sum((cl[1] - item) ** 2) ** (1/2), cl[0]), clusters)
    d, cl = min(dists, key=lambda x: x[0])
    return d, cl


# %%time
init = time.time()
counter = 0
simpleClusters = [(id(cl), cl.center) for cl in clusters]
simpleClusters = db.from_sequence(simpleClusters)
cli.persist(simpleClusters)
simpleClusters = cli.scatter(simpleClusters)
futures = []
while time.time() - init < 1.0:
    counter += 1
    example = next(inputStream)
    future = cli.submit(minDistSimple, simpleClusters, example.item)
    futures.append(future)

# %%time
results = cli.gather(futures)
elapsed = time.time() - init
print(f'minasOnline testSamples {elapsed} seconds, consumed {counter} items, {int(counter / elapsed)} i/s')

# %%time
import pandas as pd
from sklearn.datasets import fetch_covtype
covtype = fetch_covtype()
total = len(covtype.data)

zipToMap = lambda x: {'item': x[0], 'label': str(x[1])}
onePercent = int(total*0.01)
baseMap = map(zipToMap, zip(covtype.data[:onePercent], covtype.target[:onePercent]))
onPercentDataFrame = pd.DataFrame(baseMap)

clusters = minasOffline(onPercentDataFrame)
print(len(clusters))

# %%time
counter = 0
simpleClusters = [(id(cl), cl.center) for cl in clusters]
simpleClusters = db.from_sequence(simpleClusters)
cli.persist(simpleClusters)
simpleClusters = cli.scatter(simpleClusters)
futures = []
init = time.time()
for i, example in examples:
    counter += 1
    future = cli.submit(minDistSimple, simpleClusters, example.item)
    futures.append(future)
elapsed = time.time() - init
print(f'loop submit {elapsed} seconds')
init = time.time()
results = cli.gather(futures)
elapsed = time.time() - init
print(f'minasOnline submit {elapsed} seconds, consumed {counter} items, {int(counter / elapsed)} i/s')

# %%time
counter = 0
localClusters = [(id(cl), cl.center) for cl in clusters]
simpleClusters = db.from_sequence(localClusters)
cli.persist(simpleClusters)
simpleClusters = cli.scatter(simpleClusters)
futures = []
init = time.time()
for i, example in examples:
    counter += 1
    item = example.item
    #
    def d
    for cl in simpleClusters:
        for c, x in zip(cl[1], item):
            s = (c - x) ** 2
        d = s ** (1/2), cl[0]
        
    dists = cli.map(lambda cl: (), localClusters)
    future = cli.submit(min, dists, key=lambda x: x[0])
    #
    # future = cli.submit(minDistSimple, simpleClusters, example.item)
    futures.append(future)
elapsed = time.time() - init
print(f'loop submit {elapsed} seconds')
init = time.time()
results = cli.gather(futures)
elapsed = time.time() - init
print(f'minasOnline submit {elapsed} seconds, consumed {counter} items, {int(counter / elapsed)} i/s')

# %%time
from dask import delayed
@delayed
def sub(a, b):
    return a - b
@delayed
def sqr(a, b):
    return a ** b
@delayed
def summ(a, b):
    return a + b
@delayed
def extractI(x, i):
    return x[i]
#
localClusters = [(id(cl), cl.center) for cl in clusters]
dimentions = len(clusters[0].center)
scatterClusters = cli.scatter(localClusters)
k = None
result = None
for i, example in examples:
    scatterItem = cli.scatter(example.item)
    dists = []
    for cl in scatterClusters:
        c = []
#         for i in range(dimentions):
#             ci = extractI(extractI(cl, 1), i)
#             xi = extractI(scatterItem, i)
        a = sub(ci, xi)
        b = sqr(a, 2)
        c.append(b)
        s = delayed(sum)(c)
        d = (s ** (1/2), extractI(cl, 0))
        dists.append(d)
    result = delayed(min)(dists, key=lambda x: x[0])

# %%time

# %%time

# %%time

# %%time

# %%time

# %%time
