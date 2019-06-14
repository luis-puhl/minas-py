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
from .req_once import req_block

def classifier_imp(log, time_window=10, size_window=500):
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
    itemRecordBuffer = []
    classe_contagem = {}
    counter = 0
    elapsed = 0
    last_clean_time = time.time()
    last_report_time = time.time()
    crossPolinationFails = 0
    try:
        source = __name__
        # clusters = req_block(log, consumer, kprod, client_id, source)
        log.info(f'READY {client_id}')
        for message in consumer:
            if crossPolinationFails >= 10:
                raise Exception(f'Cross Polination Fails {crossPolinationFails}')
            # message{ topic, partition, offset, key, value }
            if len(clusters) == 0 and crossPolinationFails < 10:
                log.info(f'{client_id} requesting clusters')
                kprod.send(topic='clusters', value={'source': source, 'client_id': client_id, 'action': 'request'})
                crossPolinationFails += 1
            if message.topic == 'clusters' and b'clusters' in message.value:
                if len(clusters) == 0 or message.value[b'source'] in [b'online', b'offline']:
                    clusters = []
                    for c in message.value[b'clusters']:
                        c_decoded = { k.decode(encoding='utf-8'): v for k, v in c.items() }
                        c_decoded['center'] = np.array(c_decoded['center'])
                        c_decoded['label'] = c_decoded['label'].decode(encoding='utf-8')
                        clusters.append(Cluster(**c_decoded))
                    centers = mkCenters(clusters)
                    log.info(f'{client_id} got clusters {len(clusters)}')
            elif message.topic == 'clusters':
                # b'action' in message.value and message.value[b'action'] == b'request' and len(clusters) > 0
                remote = None
                if b'client_id' in message.value:
                    remote = message.value[b'client_id'].decode(encoding='utf-8')
                if client_id == remote:
                    crossPolinationFails += 1
                    log.info(f'Cross polination FAIL')
                elif crossPolinationFails < 10:
                    log.info(f'Cross polination {len(clusters)} from {client_id} to {remote}')
                    serialClusters = [ cl.__getstate__() for cl in clusters ]
                    kprod.send(topic='clusters', value={'source': 'classifier', 'clusters': serialClusters})
            elif message.topic == 'items':
                counter += 1
                itemRecordBuffer.append(message)
            else:
                log.info(f'{client_id} message unkown')
                log.info(message)
            # end message absortion
            #
            if len(clusters) == 0 or len(itemRecordBuffer) == 0:
                # skip
                continue
            init = time.time()
            for record in itemRecordBuffer:
                if time.time() - last_report_time > time_window:
                    last_report_time = time.time()
                    report = dict(
                        itemRecordBuffer=len(itemRecordBuffer),
                        clusters=len(clusters),
                        counter=counter,
                        crossPolinationFails=crossPolinationFails,
                    )
                    log.info(f'{client_id} report => {report}')
                # record.value = {item: [], dataset: ''}
                example = Example(item=np.array(record.value[b'item']), n=record.key)
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
                    kprod.send(topic='desconhecidos', value={'example': example.__getstate__()}, key=record.key)
                # end classification
                # 
                if len(example_buffer) > CLEANUP_WINDOW and time.time() - last_clean_time > time_window :
                    sortedKeys = sorted(classe_contagem, key=lambda x: x if type(x) == str else '')
                    classe_contagem = { k: classe_contagem[k] for k in sortedKeys }
                    value = {'classe-contagem': classe_contagem, 'nbytes': example.item.nbytes}
                    kprod.send(topic='classe-contagem', value=value, key=record.key)
                    # log.info(f"[CLASSE_CONTAGEM] {classe_contagem}")
                    example_buffer = []
                    classe_contagem = {}
                    last_clean_time = time.time()
            elapsed += time.time() - init
        # for consumer
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        log.exception(ex)
        raise
    finally:
        if len(clusters) > 0:
            speed = counter // max(0.001, elapsed)
            elapsed = int(elapsed * 1000)
            log.info(f'consumer {client_id}: {elapsed} ms, consumed {counter} items, {speed} i/s')
            kprod.flush()
            return True
        else:
            log.info(f'Fail to load clusters, EXIT')
            return False

def classifier(**kwargs):
    log = logging.getLogger(__name__)
    kwargs['log'] = log
    time.sleep(10)
    try:
        classifier_imp(**kwargs)
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        log.exception(log)
        raise