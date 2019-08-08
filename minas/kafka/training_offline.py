import time
import traceback
import os
import logging

import numpy as np
from kafka import KafkaConsumer
from kafka import KafkaProducer
from kafka import TopicPartition
import msgpack
import yaml

from ..example import Example, Vector
from ..cluster import Cluster
from ..map_minas import *

def training_offline():
    log = logging.getLogger(__name__)
    consumer = KafkaConsumer(
        # topics=[ 'items-classes' ],
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        group_id='training_offline',
        client_id=f'client_{os.uname().machine}_{hex(os.getpid())}',
        value_deserializer=msgpack.unpackb,
        key_deserializer=msgpack.unpackb,
        # StopIteration if no message after 1 sec
        consumer_timeout_ms=1 * 1000,
        # max_poll_records=10,
        # auto_offset_reset='latest',
        auto_offset_reset='earliest',
        # auto_offset_reset (str) – A policy for resetting offsets **on OffsetOutOfRange errors**:
        # ‘earliest’ will move to the oldest available message, 
        # ‘latest’ will move to the most recent. 
        # Any other value will raise the exception. Default: ‘latest’.
    )
    partition = TopicPartition('items-classes', 0)
    consumer.assign([partition])
    consumer.seek_to_beginning()
    kprod = KafkaProducer(
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        value_serializer=msgpack.packb,
        key_serializer=msgpack.packb,
    )
    # 
    init = time.time()
    knownBuffer = []
    clusters = []
    counter = 0
    log.info('READY')
    try:
        dataset = None
        while dataset is None:
            log.info('NEAR')
            for message in consumer:
                log.info('START')
                counter += 1
                if message.topic == 'items-classes':
                    item = np.array(message.value[b'item'])
                    label = message.value[b'label'].decode(encoding='utf-8')
                    zeroItem = {'item': item, 'label': label}
                    knownBuffer.append(zeroItem)
                    dataset = message.value[b'dataset'].decode(encoding='utf-8')
                    break
                # 
            # 
        # 
        filename = f'offline_training_{dataset}.yaml'
        if os.path.exists(filename):
            log.info(f'loading from file "{filename}".')
            with open(filename, 'r') as f:
                dic = yaml.load(f, Loader=yaml.SafeLoader)
                clusters = [ Cluster(**cl) for cl in dic ]
                assert len(clusters) > 0
                clusters_serial = [ c.__getstate__() for c in clusters ]
        else:
            while len(knownBuffer) < 1000:
                for message in consumer:
                    # message{ topic, partition, offset, key, value }
                    # {'item': data, 'label': label} = value
                    counter += 1
                    if b'item' not in message.value:
                        if message.value != {b'classifier': b'WAIT ON CLUSTERS'}:
                            log.info(f'Unknown message {message.value}')
                        continue
                    item = np.array(message.value[b'item'])
                    label = message.value[b'label'].decode(encoding='utf-8')
                    value = {'item': item, 'label': label}
                    knownBuffer.append(value)
                    # if counter >= 2000:
                    #     break
                # 
            # 
            log.info(f'training started with {counter} examples')
            log.info(knownBuffer[0])
            log.info(f'Running minasOffline and storing to file "{filename}".')
            examplesDf = pd.DataFrame(knownBuffer)
            clusters = minasOffline(examplesDf)
            if len(clusters) == 0:
                raise Exception(f'Zero clusters from minasOffline. Got {examplesDf}')
            clusters_serial = [ c.__getstate__() for c in clusters ]
            # 
            with open(filename, 'w') as f:
                f.write(yaml.dump(clusters_serial))
            # 
        # 
        elapsed = time.time() - init
        speed = counter // max(0.001, elapsed)
        assert len(clusters) > 0
        log.info(f'DONE: {elapsed} s, consumed {counter} items, {speed} i/s,\t clusters => {len(clusters)} \n\t{clusters[0]}')
        kprod.flush()
        value = {'source': 'offline', 'clusters': clusters_serial}
        # 
        for i in range(10):
            kprod.send(topic='clusters', value=value)
            kprod.flush()
            time.sleep(1)
        # 
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        log.exception(ex)
        raise
    finally:
        log.info('EXIT')
