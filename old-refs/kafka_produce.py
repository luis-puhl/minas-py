import json
import time

import confluent_kafka
from streamz import Stream
from tornado import gen
from tornado.ioloop import IOLoop
import numpy as np

from minas.map_minas_support import *

kafkaConfig = {'bootstrap.servers': 'localhost:9092', 'group.id': 'streamz-minas'}
topic = 'test'

np.random.seed(300)
classes = list(map(mkClass, range(1000)))
clusters = sampleClusters(classes)
inputStream = loopExamplesIter(classes)
examples = list(zip(range(200), inputStream))

print('confluent_kafka.Producer()')
kprod = confluent_kafka.Producer(kafkaConfig)
print(kprod.list_topics().topics)
init = time.time()
counter = 0
for i, example in examples:
    # value = repr(example)[:-1] + ', item=' + repr(example.item) + ')'
    example.timestamp = time.time_ns()
    value = json.dumps({'example': example.__getstate__()})
    kprod.produce(topic=topic, value=value, key=str(i))
    counter += 1
elapsed = time.time() - init
print(f'kafka produce {elapsed} seconds, consumed {counter} items, {int(counter / elapsed)} i/s')
