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
print(f'minasOnline testSamples {elapsed} seconds, consumed {counter} items, {int(counter / elapsed)} i/s')

import confluent_kafka
from streamz import Stream
import json
from tornado import gen
from tornado.ioloop import IOLoop
# from dask.distributed import Client
# client = Client('tcp://192.168.15.14:8786', processes=False, asynchronous=True)
# client = Client('tcp://192.168.15.14:8786')

async def main():
# def main():
    kafkaConfig = {'bootstrap.servers': 'localhost:9092', 'group.id': 'streamz-minas'}
    topic = 'test'
    # kafkaSource = Stream.from_kafka([topic], kafkaConfig, start=True, asynchronous=True, loop=client.loop).map(print)
    # kafkaSource = Stream.from_kafka([topic], kafkaConfig, start=True).map(print)
    kafkaSource = Stream.from_kafka([topic], kafkaConfig, start=True, asynchronous=True).map(print).buffer(5)
    
    def exampleMap(di):
        if 'example' in di:
            return Example(**di['example'])
        return di
    def minDistMap(example):
        return minDist(clusters, example.item)
    def combinedMap(jsonItem):
        di = json.loads(jsonItem)
        example = exampleMap(di)
        timeDiff = time.time_ns() - example.timestamp
        return (minDistMap(example), timeDiff)
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
    # kafkaSource.scatter(asynchronous=True, loop=client.loop).map(combinedMap).buffer(5).gather().sink(asSink('dask'))
    # kafkaSource.scatter().map(combinedMap).buffer(5).gather().sink(asSink('dask'))

    print('confluent_kafka.Producer()')
    kprod = confluent_kafka.Producer(kafkaConfig)
    print(kprod.list_topics().topics)
    init = time.time()
    counter = 0
    for i, example in examples:
        # value = repr(example)[:-1] + ', item=' + repr(example.item) + ')'
        example.timestamp = time.time_ns()
        value = json.dumps({'example': example.__getstate__()})
        kprod.produce(topic=topic, value=value, key=str(i))
        counter += 1
    elapsed = time.time() - init
    print(f'kafka produce {elapsed} seconds, consumed {counter} items, {int(counter / elapsed)} i/s')

    kafkaSource.visualize()
    while len(examples) != len(results['raw']):
        print('len(examples)', len(examples), 'len(results[raw])', len(results['raw']))
        await gen.sleep(1)
    print(results)


# client.loop.run_sync(main)
# main()
IOLoop().run_sync(main)