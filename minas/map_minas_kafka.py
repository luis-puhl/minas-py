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

def _kafka_generator(consumer, ):
    for kafkaRecord in consumer:
        val = None
        if kafkaRecord and kafkaRecord.value:
            val = kafkaRecord.value
        if type(val) is bytes:
            val = json.loads(val.decode('utf-8'))
        if not 'example' in val:
            print('not example in Record')
            return
        example = Example(item=val)
        yield example


def map_minas_kafka(topic = 'minas-topic'):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        group_id='map_minas_kafka',
        client_id=f'client_{os.uname().machine}_{hex(os.getpid())}',
        # value_deserializer=value_deserializer,
        # StopIteration if no message after 1 sec
        consumer_timeout_ms=1 * 1000,
        max_poll_records=10,
        auto_offset_reset='latest',
    )
    kprod = KafkaProducer(
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        # value_serializer=value_serializer,
        # key_serializer=key_serializer,
    )
    # 
    if topic not in consumer.topics():
        raise Exception(f'Topic "{topic}" not found.')
    print('ready')
    gen = _kafka_generator(consumer)
    counter = 0
    for processed in minasOnline(gen):
        value = {'minas_out': processed }
        kprod.send(topic=topic+'_out', value=value)
        counter += 1
        elapsed += time.time() - init
    speed = counter // max(0.001, elapsed)
    elapsed = int(elapsed * 1000)
    print(f'consumer {client_id}: {elapsed} ms, consumed {counter} items, {speed} i/s', time.time() - totalTime)
    kprod.flush()

def minas_workers(**kwargs):
    consumersLen = os.cpu_count()
    consumers = []
    for i in range(consumersLen):
        p = mp.Process(target=map_minas_kafka, kwargs=kwargs)
        consumers.append(p)
    for consumer in consumers:
        consumer.start()
    for consumer in consumers:
        consumer.join()
