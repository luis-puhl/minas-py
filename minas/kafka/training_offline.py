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

def training_offline():
    log = logging.getLogger(__name__)
    consumer = KafkaConsumer(
        'items-classes',
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        group_id='training_offline',
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
    init = time.time()
    knownBuffer = []
    clusters = []
    counter_global = 0
    init_global = time.time()
    log.info('onffline training READY')
    try:
        for message in consumer:
            # message{ topic, partition, offset, key, value }
            # {'item': data, 'label': label} = value
            counter_global += 1
            item = message.value[b'item']
            label = message.value[b'label'].decode(encoding="utf-8")
            value = {'item': item, 'label': label}
            knownBuffer.append(value)
            counter = len(knownBuffer)
            if counter >= 2000:
                break
            # 
        # 
        log.info(f'onffline training started with {counter} examples')
        log.info(knownBuffer[0])
        examplesDf = pd.DataFrame(knownBuffer)
        clusters = minasOffline(examplesDf)
        clusters_serial = [ c.__getstate__() for c in clusters ]
        value = {'source': 'offline', 'clusters': clusters_serial}
        kprod.send(topic='clusters', value=value)
        elapsed = time.time() - init
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        traceback.log.info_exc()
        log.info('Exception', ex)
        raise
    finally:
        elapsed = time.time() - init_global
        counter = counter_global
        speed = counter // max(0.001, elapsed)
        elapsed = int(elapsed * 1000)
        cl = clusters[0] if len(clusters) > 0 else ''
        log.info(f'{len(clusters)} clusters {cl}')
        log.info(f'onffline training DONE: {elapsed} ms, consumed {counter} items, {speed} i/s')
        kprod.flush()