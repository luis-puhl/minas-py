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
import kafka as kafkaPy

from minas.map_minas_support import *

def mkTestData(dim=2, classesLen=1000, examplesLen=200):
    np.random.seed(300)
    classes = [ mkClass(i, dim) for i in range(classesLen) ]
    clusters = sampleClusters(classes)
    inputStream = loopExamplesIter(classes)
    examples = list(zip(range(examplesLen), inputStream))

    centers = np.array([cl.center for cl in clusters])
    return dict(classes=classes, clusters=clusters, inputStream=inputStream, examples=examples, centers=centers)

def minDist(clusters, centers, item):
    dists = LA.norm(centers - item, axis=1)
    d = dists.min()
    cl = clusters[ dists.tolist().index(d) ]
    return d, cl

def minas_local(classes=[], clusters=[], inputStream=[], examples=[], centers=[]):
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
topic = 'minas-topic'

def minas_producer(classes=[], clusters=[], inputStream=[], examples=[], centers=[]):
    print('minas_producer')
    kprod = KafkaProducer(
        bootstrap_servers=kafkaConfig['bootstrap_servers'],
        value_serializer=value_serializer,
        key_serializer=key_serializer,
    )
    init = time.time()
    counter = 0
    futures = []
    for i, example in examples:
        example.timestamp = time.time_ns()
        value = {'example': example.__getstate__()}
        futureRecordMetadata = kprod.send(topic=topic, value=value, key=i)
        futures.append(futureRecordMetadata)
        counter += 1
    
    kprod.flush()
    topics = set()
    partitions = set()
    offsets = set()
    for future in futures:
        record_metadata = future.get()
        topics.add(record_metadata.topic)
        partitions.add(record_metadata.partition)
        offsets.add(record_metadata.offset)
    elapsed = time.time() - init
    print(f'minas producer {elapsed} seconds, produced {counter} items, {int(counter / elapsed)} i/s')
    resume = lambda x: f'{min(x)} to {max(x)} ({len(x)})'
    print(f'topics: {topics}\tpartitions: {resume(partitions)}\toffsets: {resume(offsets)}')

def consumeRecord(kafkaRecord, results, results_elapsed, classes=[], clusters=[], inputStream=[], examples=[], centers=[]):
    init = time.time()
    val = None
    if kafkaRecord and kafkaRecord.value:
        val = kafkaRecord.value
    if type(val) is bytes:
        try:
            val = json.loads(val.decode('utf-8'))
        except:
            print(val)
            return
    if not 'example' in val:
        print('not example in Record')
        return
    example = Example(**val['example'])
    processed = minDist(clusters, centers, example.item)
    # 
    timeDiff = time.time_ns() - example.timestamp
    results.append(processed)
    results_elapsed.append(timeDiff)
    value = {'d': processed[0], 'label': processed[1].label, 'elapsed': timeDiff}
    kprod.send(topic=topic+'_out', value=value)

def minas_consumer_kafka(topic, classes=[], clusters=[], inputStream=[], examples=[], centers=[], readyness=None, go=None):
    results = []
    counter = 0
    elapsed = 0
    results_elapsed = []
    kwargs = dict(
        classes=classes, clusters=clusters,
        inputStream=inputStream, examples=examples,
        centers=centers, results_elapsed=results_elapsed,
    )

    client_id = mk_client_id()
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=kafkaConfig['bootstrap_servers'],
        group_id=kafkaConfig['group_id'],
        client_id=client_id,
        value_deserializer=value_deserializer,
        # StopIteration if no message after 1 sec
        consumer_timeout_ms=1 * 1000,
        max_poll_records=10,
        auto_offset_reset='latest',
    )
    kprod = KafkaProducer(
        bootstrap_servers=kafkaConfig['bootstrap_servers'],
        value_serializer=value_serializer,
        key_serializer=key_serializer,
    )
    # 
    # if topic not in consumer.topics():
    #     raise Exception(f'Topic "{topic}" not found.')
    # topics = consumer.topics()
    # partitions = consumer.partitions_for_topic(topic)
    # assignment = consumer.assignment()
    # subscription = consumer.subscription()
    # topics = {}
    # try:
    #     topics = consumer.poll(timeout_ms=10, max_records=1)
    # except:
    #     pass
    # for topic, records in topics.items():
    #     for re in records:
    #         print(re)
    #         consumeRecord(re, results, **kwargs)
    print('ready')
    readyness.set()
    go.wait()

    totalTime = time.time()
    for kafkaRecord in consumer:
        consumeRecord(kafkaRecord, results, **kwargs)
        counter += 1
        elapsed += time.time() - init
    speed = counter // max(0.001, elapsed)
    elapsed = int(elapsed * 1000)
    print(f'consumer {client_id}: {elapsed} ms, consumed {counter} items, {speed} i/s', time.time() - totalTime)
    kprod.flush()

def minas_output_counter():
    client_id = mk_client_id()
    consumer = KafkaConsumer(
        f'{topic}_out',
        bootstrap_servers=kafkaConfig['bootstrap_servers'],
        group_id='minas_output_counter',
        # StopIteration if no message after 2 sec
        consumer_timeout_ms=2 * 1000,
        auto_offset_reset='latest',
    )
    
    counter = 0
    init = False
    for kafkaRecord in consumer:
        if not init:
            init = time.time()
        counter += 1
    if init:
        elapsed = time.time() - init
    else:
        elapsed = 0
    speed = counter // max(0.001, elapsed)
    elapsed = int(elapsed * 1000)
    print(f'output {client_id}: {elapsed} ms, {counter} items, {speed} i/s')

def main_line(consumersLen=None, **kwargs):
    print('main line')
    if consumersLen is None:
        consumersLen = os.cpu_count()
    consumers = []
    readynessProbes = []
    goProbes = []
    for i in range(consumersLen):
        kArgs = kwargs.copy()
        
        readyness = mp.Event()
        readynessProbes.append(readyness)
        kArgs['readyness'] = readyness
        
        go = mp.Event()
        goProbes.append(go)
        kArgs['go'] = go
        
        kArgs['topic'] = topic
        p = mp.Process(target=minas_consumer_kafka, kwargs=kArgs)
        consumers.append(p)
    # out = mp.Process(target=minas_output_counter)
    producer = mp.Process(target=minas_producer, kwargs=kwargs)
    # 
    for consumer in consumers:
        consumer.start()
    # out.start()
    for ready in readynessProbes:
        ready.wait()
    producer.start()
    for go in goProbes:
        go.set()
    
    producer.join()
    for consumer in consumers:
        consumer.join()
    # out.join()

if __name__ == '__main__':
    kwargs = mkTestData()
    minas_local(**kwargs)
    # 
    # for i in range(100, 10 * 100, 100):
    i = 3 * 100
    kwargs = mkTestData(dim=i, classesLen=i, examplesLen=i)
    # for consumersLen in range(1, os.cpu_count()):
    #     main_line(consumersLen=consumersLen, **kwargs)
    main_line(consumersLen=os.cpu_count()*2, **kwargs)
