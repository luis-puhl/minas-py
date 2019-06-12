import time
import traceback
import os
import logging

import numpy as np
from kafka import KafkaConsumer
from kafka import KafkaProducer
import msgpack

from ..example import Example, Vector
from ..cluster import Cluster
from ..map_minas import *

def classifier_imp(log, time_window=1, size_window=500):
    client_id = f'client_{os.uname().machine}_{hex(os.getpid())}'
    consumer = KafkaConsumer(
        'items', 'clusters',
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        group_id='classifier',
        client_id=client_id,
        value_deserializer=msgpack.unpackb,
        key_deserializer=msgpack.unpackb,
        # StopIteration if no message after 1 sec
        consumer_timeout_ms=10 * 1000,
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
    CLEANUP_WINDOW = size_window
    # 
    clusters = []
    centers = []
    example_buffer = []
    classe_contagem = {}
    counter = 0
    elapsed = 0
    last_clean_time = time.time()
    try:
        while len(clusters) == 0:
            log.info(f'WAIT ON CLUSTERS {client_id}')
            for message in consumer:
                if message.topic == 'clusters' and message.value[b'source'] == b'offline':
                    for c in message.value[b'clusters']:
                        c_decoded = { k.decode(encoding="utf-8"): v for k, v in c.items() }
                        c_decoded['center'] = np.array(c_decoded['center'])
                        c_decoded['label'] = c_decoded['label'].decode(encoding="utf-8")
                        clusters.append(Cluster(**c_decoded))
                    centers = mkCenters(clusters)
                    log.info(f'Classifier got clusters {len(clusters)}')
                    break
        log.info(f'READY {client_id}')
        kprod.send(topic='control-bus', value={'classifier': 'ready'})
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
                log.info(f'Classifier got clusters {len(clusters)}')
                continue
            if message.topic != 'items':
                log.info('item unkown')
                log.info(message.value)
                continue
            if len(clusters) == 0:
                continue
            counter += 1
            init = time.time()
            example = Example(item=np.array(message.value), n=message.key)
            example.n = counter
            d, cl = minDist(clusters, centers, example.item)
            if (d / max(1.0, cl.maxDistance)) <= RADIUS_FACTOR:
                cl.maxDistance = max(cl.maxDistance, d)
                cl.latest = counter
                cl.n += 1
                # yield f"[CLASSIFIED] {example.n}: {cl.label}"
                # log.info(f"[CLASSIFIED] {example.n}: {cl.label}")
                if not cl.label in classe_contagem:
                    classe_contagem[cl.label] = 0
                classe_contagem[cl.label] += 1
                example_buffer.append(example)
            else:
                if not None in classe_contagem:
                    classe_contagem[None] = 0
                    classe_contagem[None] += 1
                # yield f"[UNKNOWN] {example.n}: {example.item}"
                # log.info(f"[UNKNOWN] {example.n}: {example.item}")
                kprod.send(topic='desconhecidos', value={'example': example.__getstate__()}, key=message.key)
            if len(example_buffer) > CLEANUP_WINDOW and time.time() - last_clean_time > time_window :
                sortedKeys = sorted(classe_contagem, key=lambda x: x if type(x) == str else '')
                classe_contagem = { k: classe_contagem[k] for k in sortedKeys }
                value = {'classe-contagem': classe_contagem, 'nbytes': example.item.nbytes}
                kprod.send(topic='classe-contagem', value=value, key=message.key)
                # log.info(f"[CLASSE_CONTAGEM] {classe_contagem}")
                example_buffer = []
                classe_contagem = {}
                last_clean_time = time.time()
            elapsed += time.time() - init
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        log.exception(ex)
        raise
    finally:
        speed = counter // max(0.001, elapsed)
        elapsed = int(elapsed * 1000)
        log.info(f'consumer {client_id}: {elapsed} ms, consumed {counter} items, {speed} i/s')
        kprod.flush()

def classifier(**kwargs):
    log = logging.getLogger(__name__)
    kwargs['log'] = log
    try:
        classifier_imp(**kwargs)
    except Exception as ex:
        log.exception(log)
        raise