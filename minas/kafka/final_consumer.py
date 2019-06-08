import time
import os

import numpy as np
from kafka import KafkaConsumer
from kafka import KafkaProducer
import msgpack

def final_consumer():
    consumer = KafkaConsumer(
        'classe-contagem', 'novidades',
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        group_id='final_consumer',
        client_id=f'client_{os.uname().machine}_{hex(os.getpid())}',
        value_deserializer=msgpack.unpackb,
        key_deserializer=msgpack.unpackb,
        # StopIteration if no message after 1 sec
        # consumer_timeout_ms=1 * 1000,
        # max_poll_records=10,
        auto_offset_reset='latest',
    )
    print('final_consumer READY')
    classe_contagem = {}
    try:
        for message in consumer:
            # message{ topic, partition, offset, key, value }
            print('final_consumer', message.topic, message.key, message.value)
            # if message.topic == 'classe-contagem':
            #     classe_contagem[key] = message.value
            # else:
            #     print('final_consumer', message.topic, message.key, message.value, '\n')
            #
        #
    finally:
        print('final_consumer classe_contagem', classe_contagem)
    #
#