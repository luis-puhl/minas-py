import time
import os
import logging

import numpy as np
import pandas as pd
from kafka import KafkaConsumer
from kafka import KafkaProducer
import msgpack

from minas.ext_lib.humanize_bytes import humanize_bytes

def final_consumer(report_interval=10):
    log = logging.getLogger(__name__)
    consumer = KafkaConsumer(
        'classe-contagem', 'novidades',
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        group_id='final_consumer',
        client_id=f'client_{os.uname().machine}_{hex(os.getpid())}',
        value_deserializer=msgpack.unpackb,
        key_deserializer=msgpack.unpackb,
        # StopIteration if no message after 1 sec
        consumer_timeout_ms=1 * 60 * 1000,
        # max_poll_records=10,
        auto_offset_reset='latest',
    )
    classe_contagem = {}
    labelCount = {}
    init = time.time()
    totalCounter = 0
    nbytes = 0
    log.info('READY')
    lastReport = time.time()
    try:
        for message in consumer:
            # message{ topic, partition, offset, key, value }
            if message.topic == 'classe-contagem' and b'classe-contagem' in message.value:
                sizeof = 16
                if b'nbytes' in message.value:
                    sizeof = message.value[b'nbytes']
                for k, v in message.value[b'classe-contagem'].items():
                    if k not in classe_contagem:
                        classe_contagem[k] = 0
                    classe_contagem[k] += v
                    totalCounter += v
                    nbytes += v * sizeof
                elapsed = time.time() - init
                if time.time() - lastReport > report_interval:
                    itemSpeed = totalCounter / max(0.001, elapsed)
                    itemTime = elapsed / max(1, totalCounter) * 1000
                    byteSpeed = humanize_bytes(int(nbytes / elapsed))
                    log.info('{:2.4f} s, {:5} i, {:6.2f} i/s, {:4.2f} ms/i, {}/s'.format(elapsed, totalCounter, itemSpeed, itemTime, byteSpeed))
                    lastReport = time.time()
            elif message.topic == 'novidades':
                src = message.value[b'source'].decode(encoding='utf-8')
                for cl in message.value[b'clusters']:
                    label = cl[b'label']
                    if label not in labelCount:
                        labelCount[label] = 0
                    labelCount[label] += 1
                log.info(f'novidades {src} {labelCount}')
            else:
                log.info(f'topic={message.topic}, key={message.key}, value={message.value}')
            #
        #
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        log.exception(ex)
        raise
    finally:
        log.info(f'classe_contagem {classe_contagem}')
        elapsed = time.time() - init
        itemSpeed = totalCounter / max(0.001, elapsed)
        itemTime = elapsed / max(1, totalCounter) * 1000
        byteSpeed = humanize_bytes(int(nbytes / elapsed))
        log.info('{:2.4f} s, {:5} i, {:6.2f} i/s, {:4.2f} ms/i, {}/s'.format(elapsed, totalCounter, itemSpeed, itemTime, byteSpeed))
    #
#