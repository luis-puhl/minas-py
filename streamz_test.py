import time
import json

import confluent_kafka
from streamz import Stream
from tornado.ioloop import IOLoop
from tornado import gen

from minas.map_minas_support import *

kafkaConfig = {'bootstrap.servers': 'localhost:9092', 'group.id': 'streamz-minas'}
topic = 'test'

np.random.seed(300)
classes = list(map(mkClass, range(1000)))
clusters = sampleClusters(classes)
inputStream = loopExamplesIter(classes)
examples = list(zip(range(200), inputStream))

kprod = confluent_kafka.Producer(kafkaConfig)

def minDist(clusters, item):
    dists = map(lambda cl: (sum((cl.center - item) ** 2) ** (1/2), cl), clusters)
    d, cl = min(dists, key=lambda x: x[0])
    return d, cl

timeDiffs = []
def combinedMap(jsonItem):
    if jsonItem is None:
        return ((0, 0), 0)
    di = json.loads(jsonItem)
    if not 'example' in di:
        return ((0, 0), 0)
    example = Example(**di['example'])
    timeDiff = time.time_ns() - example.timestamp
    item = example.item
    dists = map(lambda cl: (sum((cl.center - item) ** 2) ** (1/2), cl), clusters)
    d, cl = min(dists, key=lambda x: x[0])
    timeDiffs.append(timeDiff)
    result = { 'minDist': d, 'cluster': cl, 'timeDiff': timeDiff }
    value = json.dumps({ 'minDist': d, 'cluster': cl.__getstate__(), 'timeDiff': timeDiff })
    kprod.produce(topic=topic+'_result', value=value, key=str(example.timestamp))
    return result

def increment(x):
    time.sleep(0.1)
    return x + 1

async def write(x):
    await gen.sleep(0.2)
    print(x)

async def f():
    # source = Stream(asynchronous=True)
    # source.rate_limit(0.500).sink(write)

    # for x in range(10):
    #     await source.emit(x)

    kafkaConfig = {'bootstrap.servers': 'localhost:9092', 'group.id': 'streamz-minas'}
    topic = 'test'
    kafkaSource = Stream.from_kafka([topic], kafkaConfig, start=True, asynchronous=True)
    
    results = {}
    def asSink(name):
        results[name] = []
        results[name + 'timestamp'] = time.time_ns()
        results[name + 'elapsed'] = time.time_ns()
        def f(val):
            results[name].append(val)
            results[name + 'elapsed'] = time.time_ns() - results[name + 'timestamp']
            print(name, val)
        return f
    print('kafkaSource map')
    kafkaSource.map(combinedMap).sink(asSink('raw'))

    kafkaSource.visualize()
    while len(results['raw']) < 200:
        print('len(results[raw])', len(results['raw']))
        await gen.sleep(1)
    print(results)
    avg = (sum(timeDiffs) / len(timeDiffs)) * 10**(-9)
    print(avg, 'avgs', 1/avg, 'item/s')

IOLoop().run_sync(f)
