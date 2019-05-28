import json
import time
import os
import sys
import multiprocessing as mp

import numpy as np
from numpy import linalg as LA
from tornado.ioloop import IOLoop
from tornado import gen

from kafka import KafkaConsumer
from kafka import KafkaProducer

from minas.map_minas_support import *

np.random.seed(300)
classes = list(map(mkClass, range(1000)))
clusters = sampleClusters(classes)
inputStream = loopExamplesIter(classes)
examples = list(zip(range(200), inputStream))

centers = np.array([cl.center for cl in clusters])

def minDist(clusters, centers, item):
    dists = LA.norm(centers - item, axis=1)
    d = dists.min()
    cl = clusters[ dists.tolist().index(d) ]
    return d, cl

def minas_local():
    counter = 0
    results = []
    init = time.time()
    for i, example in examples:
        counter += 1
        result = minDist(clusters, centers, example.item)
        results.append(result)
    elapsed = time.time() - init
    len(results)
    print(f'minas_local {elapsed} seconds, consumed {counter} items, {int(counter / elapsed)} i/s')

# -----------------------------------------------------------------------------------------------------------

def value_serializer(value):
    if type(value) is bytes:
        return value
    return json.dumps(value).encode('utf-8')
def value_deserializer(value):
    try:
        json.loads(value.decode('utf-8'))
    except:
        pass
    return value
def key_serializer(key):
    if type(key) is bytes:
        return key
    if type(key) is int:
        return key.to_bytes(64, sys.byteorder)
    if type(key) is str:
        return key.encode('utf-8')
    return json.dumps(key).encode('utf-8')
def mk_client_id():
    return f'client_{os.uname().machine}_{hex(os.getpid())}'

kafkaConfig = dict(
    bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
    value_serializer=value_serializer,
    value_deserializer=value_deserializer,
    key_serializer=key_serializer,
    group_id='stream_share',
)
topic = 'my-failsafe-topic'
doneFlag = b'done'

def minas_producer():
    print('minas_producer')
    kprod = KafkaProducer(
        bootstrap_servers=kafkaConfig['bootstrap_servers'],
        value_serializer=value_serializer,
        key_serializer=key_serializer,
    )
    init = time.time()
    counter = 0
    for i, example in examples:
        example.timestamp = time.time_ns()
        value = {'example': example.__getstate__()}
        kprod.send(topic=topic, value=value, key=i)
        counter += 1
    elapsed = time.time() - init
    print(f'minas producer {elapsed} seconds, produced {counter} items, {int(counter / elapsed)} i/s')
    # print(kprod.metrics())

def minas_consumer_kafka():
    client_id = mk_client_id()
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=kafkaConfig['bootstrap_servers'],
        # group_id=kafkaConfig['group_id'],
        # client_id=client_id,
        value_deserializer=value_deserializer,
        consumer_timeout_ms=1000,
        # max_poll_records=1,
    )
    kprod = KafkaProducer(
        bootstrap_servers=kafkaConfig['bootstrap_servers'],
        value_serializer=value_serializer,
        key_serializer=key_serializer,
    )

    print('ready', client_id, consumer.assignment(), consumer.partitions_for_topic(topic), consumer.subscription())

    results = []
    results_elapsed = []
    counter = 0
    elapsed = 0
    totalTime = time.time()
    for kafkaRecord in consumer:
        init = time.time()
        val = None
        if kafkaRecord and kafkaRecord.value:
            val = kafkaRecord.value
        if type(val) is bytes:
            val = json.loads(val.decode('utf-8'))
        if not 'example' in val:
            print('not example in Record')
            continue
        example = Example(**val['example'])
        processed = minDist(clusters, centers, example.item)
        # 
        timeDiff = time.time_ns() - example.timestamp
        results.append(processed)
        results_elapsed.append(timeDiff)
        value = {'d': processed[0], 'label': processed[1].label, 'elapsed': timeDiff}
        kprod.send(topic=topic+'_out', value=value)
        # 
        counter += 1
        elapsed += time.time() - init
    speed = int(counter / elapsed)
    print(f'consumer {client_id}: {(elapsed * 1000) //1} ms, consumed {counter} items, {speed} i/s', time.time() - totalTime)
    # print('done', client_id, consumer.metrics())
    kprod.flush()

def minas_consumer_entrypoint():
    try:
        IOLoop().run_sync(minas_consumer_kafka)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    print('main line')
    minas_local()
    producer = mp.Process(target=minas_producer)
    consumers = [ mp.Process(target=minas_consumer_kafka) for i in range(os.cpu_count() -1) ]
    # 
    for consumer in consumers:
        consumer.start()
    time.sleep(1)
    producer.start()
    
    producer.join()
    for consumer in consumers:
        consumer.join()
