import time
import traceback
import os

import numpy as np
from kafka import KafkaConsumer
from kafka import KafkaProducer
import msgpack

from ..example import Example, Vector
from ..cluster import Cluster
from ..map_minas import *

def classifier():
    consumer = KafkaConsumer(
        'items', 'clusters',
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        group_id='map_minas_kafka',
        client_id=f'client_{os.uname().machine}_{hex(os.getpid())}',
        value_deserializer=msgpack.unpackb,
        key_deserializer=msgpack.unpackb,
        # StopIteration if no message after 1 sec
        # consumer_timeout_ms=1 * 1000,
        # max_poll_records=10,
        auto_offset_reset='latest',
    )
    kprod = KafkaProducer(
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        value_serializer=msgpack.packb,
        key_serializer=msgpack.packb,
    )
    # 
    RADIUS_FACTOR = 1.1
    EXTENTION_FACTOR = 3
    BUFF_FULL = 100
    MAX_K_CLUSTERS = 100
    REPR_TRESHOLD = 20
    CLEANUP_WINDOW = 100
    # 
    clusters = None
    centers = None
    example_buffer = []
    classe_contagem = {}
    counter = 0
    print('classifier ready')
    try:
        for message in consumer:
            # message{ topic, partition, offset, key, value }
            # print(message)
            if message.topic == 'clusters':
                clusters = message.value
                centers = mkCenters(clusters)
                continue
            if message.topic == 'items':
                example = Example(item=message.value)
                # print(example)
            if clusters is None:
                continue
            counter += 1
            init = time.time()
            example = Example(item=message.value)
            example.n = counter
            d, cl = minDist(clusters, centers, example.item)
            if (d / max(1.0, cl.maxDistance)) <= RADIUS_FACTOR:
                cl.maxDistance = max(cl.maxDistance, d)
                cl.latest = counter
                cl.n += 1
                # yield f"[CLASSIFIED] {example.n}: {cl.label}"
                print(f"[CLASSIFIED] {example.n}: {cl.label}")
                if not cl.label in classe_contagem:
                    classe_contagem[cl.label] = 0
                classe_contagem[cl.label] += 1
                example_buffer.append(example)
                if len(example_buffer) > CLEANUP_WINDOW:
                    kprod.send(topic='classe-contagem', value=classe_contagem, key=message.key)
                    print(f"[CLASSE_CONTAGEM] {classe_contagem}")
                    classe_contagem = {}
            else:
                # yield f"[UNKNOWN] {example.n}: {example.item}"
                print(f"[UNKNOWN] {example.n}: {example.item}")
                kprod.send(topic='desconhecidos', value={'example': example.__getstate__()}, key=message.key)
            elapsed += time.time() - init
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        traceback.print_exc()
        print('Exception', ex)
        raise
    finally:
        speed = counter // max(0.001, elapsed)
        elapsed = int(elapsed * 1000)
        print(f'consumer {client_id}: {elapsed} ms, consumed {counter} items, {speed} i/s', time.time() - totalTime)
        kprod.flush()
