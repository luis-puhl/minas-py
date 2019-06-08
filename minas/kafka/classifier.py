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
        group_id='classifier',
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
    CLEANUP_WINDOW = 500
    # 
    clusters = []
    centers = []
    example_buffer = []
    classe_contagem = {}
    counter = 0
    elapsed = 0
    print('classifier READY')
    try:
        for message in consumer:
            # message{ topic, partition, offset, key, value }
            if message.topic == 'clusters' and message.value[b'source'] != b'classifier':
                clusters = []
                for c in message.value[b'clusters']:
                    c_decoded = { k.decode(encoding="utf-8"): v for k, v in c.items() }
                    c_decoded['center'] = np.array(c_decoded['center'])
                    c_decoded['label'] = c_decoded['label'].decode(encoding="utf-8")
                    clusters.append(Cluster(**c_decoded))
                centers = mkCenters(clusters)
                print('Classifier got clusters', len(clusters))
                continue
            if message.topic == 'items':
                example = Example(item=message.value, n=message.key)
                # print(example)
            if len(clusters) == 0:
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
                # print(f"[CLASSIFIED] {example.n}: {cl.label}")
                if not cl.label in classe_contagem:
                    classe_contagem[cl.label] = 0
                classe_contagem[cl.label] += 1
                example_buffer.append(example)
                if len(example_buffer) > CLEANUP_WINDOW:
                    sortedKeys = sorted(classe_contagem, key=lambda x: x if type(x) == str else '')
                    classe_contagem = { k: classe_contagem[k] for k in sortedKeys }
                    kprod.send(topic='classe-contagem', value=classe_contagem, key=message.key)
                    # print(f"[CLASSE_CONTAGEM] {classe_contagem}")
                    example_buffer = []
                    classe_contagem = {}
            else:
                if not None in classe_contagem:
                    classe_contagem[None] = 0
                    classe_contagem[None] += 1
                # yield f"[UNKNOWN] {example.n}: {example.item}"
                # print(f"[UNKNOWN] {example.n}: {example.item}")
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
