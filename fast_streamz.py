import json
import time
import os
from multiprocessing import Process
import multiprocessing as mp

import numpy as np
from numpy import linalg as LA
import confluent_kafka
from streamz import Stream
from tornado.ioloop import IOLoop
from tornado import gen

from kafka import KafkaConsumer
from kafka import KafkaProducer
import confluent_kafka as ck

from minas.map_minas_support import *

np.random.seed(300)
classes = list(map(mkClass, range(1000)))
clusters = sampleClusters(classes)
inputStream = loopExamplesIter(classes)
examples = list(zip(range(20000), inputStream))

centers = np.array([cl.center for cl in clusters])

kafkaConfig = {'bootstrap.servers': 'localhost:9092', 'group.id': 'streamz-minas'}
topic = 'test'
doneFlag = b'done'

# kafkaConfig, topic, examples
def minas_producer():
    print('confluent_kafka.Producer()')
    kprod = confluent_kafka.Producer(kafkaConfig)
    print(kprod.list_topics().topics)
    init = time.time()
    counter = 0
    for i, example in examples:
        example.timestamp = time.time_ns()
        value = json.dumps({'example': example.__getstate__()})
        kprod.produce(topic=topic, value=value, key=str(i))
        counter += 1
        time.sleep(0.02377915382385254 / (200 + 100))
    elapsed = time.time() - init
    for i in range(100):
        kprod.produce(topic=topic, value=doneFlag, key=str(i))
        time.sleep(0.01)
    print(f'minas producer kafka {elapsed} seconds, produced {counter} items, {int(counter / elapsed)} i/s')


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

async def minas_consumer_streamz():
    kafkaSource = Stream.from_kafka([topic], consumer_params=kafkaConfig, start=True, asynchronous=False).buffer(5)
    kprod = confluent_kafka.Producer(kafkaConfig)
    
    def combinedMap(jsonItem):
        di = json.loads(jsonItem)
        if not 'example' in di:
            return
        example = Example(**di['example'])
        timeDiff = time.time_ns() - example.timestamp
        return (minDist(clusters, example.item), timeDiff)
    
    results = {}
    def asSink(name):
        results[name] = []
        results[name + 'timestamp'] = time.time_ns()
        results[name + 'elapsed'] = time.time_ns()
        def f(val):
            results[name].append(val)
            results[name + 'elapsed'] = time.time_ns() - results[name + 'timestamp']
            value = json.dumps({'d': val[0][0], 'label': val[0][1].label})
            kprod.produce(topic=topic+'_out', value=value)
            print(name, val)
        return f
    print('kafkaSource map')
    outStream = kafkaSource.map(combinedMap).sink(asSink('raw'))
    
    while True:
        await gen.sleep(1000)

async def minas_consumer_confluent_kafka():
    consumer = ck.Consumer(kafkaConfig)
    consumer.subscribe([topic])
    kprod = confluent_kafka.Producer(kafkaConfig)

    def combinedMap(jsonItem):
        di = json.loads(jsonItem)
        if not 'example' in di:
            return
        example = Example(**di['example'])
        timeDiff = time.time_ns() - example.timestamp
        return (minDist(clusters, example.item), timeDiff)
    results = {}
    def asSink(name):
        results[name] = []
        results[name + 'timestamp'] = time.time_ns()
        results[name + 'elapsed'] = time.time_ns()
        def f(val):
            results[name].append(val)
            results[name + 'elapsed'] = time.time_ns() - results[name + 'timestamp']
            value = json.dumps({'d': val[0][0], 'label': val[0][1].label})
            kprod.produce(topic=topic+'_out', value=value)
            print(name, val)
        return f
    print('kafkaSource map')
    # outStream = kafkaSource.map(combinedMap).sink(asSink('raw'))
    sink = asSink('raw')

    stopped = False
    count = 0
    while not stopped:
        # val = self.do_poll()
        val = None
        if consumer is not None:
            print('kafka pool')
            msg = consumer.poll(0)
            if msg and msg.value():
                val = msg.value()
        if val:
            # yield self._emit(val)
            processed = combinedMap(val)
            sink(processed)
            count += 1
            if count > 100:
                stopped = True
        else:
            await gen.sleep(0.1)
    consumer.unsubscribe()
    consumer.close()


def consumeSingleRecord(kafkaRecord, results, kprod):
    if kafkaRecord and kafkaRecord.value:
        val = kafkaRecord.value
    if val and val == doneFlag:
        raise StopIteration
    di = json.loads(val)
    if not 'example' in di:
        return
    example = Example(**di['example'])
    timeDiff = time.time_ns() - example.timestamp
    processed = (minDist(clusters, centers, example.item), timeDiff)
    # sink(processed)
    name = 'raw'
    results[name].append(processed)
    results[name + 'elapsed'] = time.time_ns() - results[name + 'timestamp']
    value = {'d': processed[0][0], 'label': processed[0][1].label, 'elapsed': results[name + 'elapsed']}
    kprod.send(topic=topic+'_out', value=value)
    # print(name, {'d': processed[0][0], 'label': processed[0][1].label})
    return processed

async def minas_consumer_kafka():
    client_id = kafkaConfig['group.id'] + '_' + hex(os.getpid()) + '_' + os.uname().machine
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=kafkaConfig['bootstrap.servers'],
        group_id=kafkaConfig['group.id'],
        client_id=client_id,
        # value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        consumer_timeout_ms=1000,
        max_poll_records=1,
    )
    kprod = KafkaProducer(
        bootstrap_servers=kafkaConfig['bootstrap.servers'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    )

    results = {}
    name = 'raw'
    results[name] = []
    results[name + 'timestamp'] = time.time_ns()
    results[name + 'elapsed'] = time.time_ns()
    print('kafkaSource map', client_id)

    counter = 0
    init = time.time()
    for msg in consumer:
        # print(msg)
        # ConsumerRecord(
        #   topic='test', partition=0, offset=776, timestamp=1558975029387, 
        #   timestamp_type=0, key=b'56', 
        #   value=b'{"example": {
        #           "item": [-0.7728796336332862, 0.7378384291353625], "label": 56, 
        #           "timestamp": 1558975029387282914, "tries": 0}}',
        #   headers=[], checksum=None, serialized_key_size=2, serialized_value_size=123,
        #   serialized_header_size=-1
        # )
        # print('kafka pool', counter)
        try:
            consumeSingleRecord(msg, results, kprod)
        except StopIteration:
            break
        counter += 1
        if counter >= len(examples):
            break
    elapsed = time.time() - init
    kprod.flush()
    print(f'minas_consumer_kafka {elapsed} seconds, consumed {counter} items, {int(counter / elapsed)} i/s')

def minas_consumer_entrypoint():
    try:
        IOLoop().run_sync(minas_consumer_kafka)
    except KeyboardInterrupt:
        pass

def minas_consumer_kafka_mp():
    client_id = kafkaConfig['group.id'] + '_' + hex(os.getpid()) + '_' + os.uname().machine
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=kafkaConfig['bootstrap.servers'],
        group_id=kafkaConfig['group.id'],
        client_id=client_id,
        # value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        consumer_timeout_ms=1000,
        max_poll_records=1,
    )
    kprod = KafkaProducer(
        bootstrap_servers=kafkaConfig['bootstrap.servers'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    )

    results = {}
    name = 'raw'
    results[name] = []
    results[name + 'timestamp'] = time.time_ns()
    results[name + 'elapsed'] = time.time_ns()
    print('kafkaSource map', client_id)

    counter = 0
    init = time.time()
    for msg in consumer:
        try:
            consumeSingleRecord(msg, results, kprod)
        except StopIteration:
            break
        counter += 1
        if counter >= len(examples):
            break
    elapsed = time.time() - init
    kprod.flush()
    print(f'minas_consumer_kafka {elapsed} seconds, consumed {counter} items, {int(counter / elapsed)} i/s')


if __name__ == '__main__':
    print('main line')
    minas_local()
    producer = Process(target=minas_producer)
    consumer = Process(target=minas_consumer_entrypoint)
    # consumers = [ Process(target=minas_consumer_entrypoint) for i in range(os.cpu_count() -1) ]
    # 
    # for consumer in consumers:
    consumer.start()
    producer.start()
    
    time.sleep(1)
    
    producer.join()
    # for p in consumers:
    consumer.join()
