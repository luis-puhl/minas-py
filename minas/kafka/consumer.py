import time
import os

import numpy as np
from kafka import KafkaConsumer
from kafka import KafkaProducer
import msgpack

def consumer():
    consumer = KafkaConsumer(
        'classe-contagem', 'novidades',
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
    for message in consumer:
        # message{ topic, partition, offset, key, value }
        print(message.topic, message.key, message.value)