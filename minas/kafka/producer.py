import time

import numpy as np
from kafka import KafkaConsumer
from kafka import KafkaProducer
import msgpack

from minas.map_minas_support import *
from minas.ext_lib.humanize_bytes import humanize_bytes

DATA_SET_FAKE = 'DATA_SET_FAKE'
DATA_SET_COVTYPE = 'DATA_SET_COVTYPE'
DATA_SET_KDD99 = 'DATA_SET_KDD99'

def dataSetGenCovtype(runForever=True):
    from sklearn.datasets import fetch_covtype
    covtype = fetch_covtype()
    while runForever:
        for data, target in zip(covtype.data, covtype.target):
            msg = yield ( data, str(target) )
            if msg is StopIteration:
                runForever = False

def dataSetGenKdd99(runForever=True):
    def kddNormalize(kddArr):
        # [0 b'tcp' b'http' b'SF' ...
        result = []
        for i, kddMap, kddEntry in zip(range(len(kddArr)), kddNormalizeMap, kddArr):
            if i == 0 or i >= 4:
                result.append(float(kddEntry))
                continue
            if not kddEntry in kddMap:
                kddMap[kddEntry] = len(kddMap)
            result.append(float(kddMap[kddEntry]))
        return result
    from sklearn.datasets import fetch_kddcup99
    kddcup99 = fetch_kddcup99()
    while runForever:
        for data, target in zip(kddcup99.data, kddcup99.target):
            msg = yield ( kddNormalize(data), str(target) )
            if msg is StopIteration:
                runForever = False

def dataSetGenFake(runForever=True, classes=5, dim=2):
    greek = [
        'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta', 'iota', 'kappa', 'la', 'mu',
        'nu', 'xi', 'omicron', 'pi', 'rho', 'sigma', 'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega',
    ]
    def greekName(index):
        sufix = ''
        if index >= len(greek):
            sufix = f'_{ index // len(greek) }'
        return greek[index % len(greek)] + sufix
    def mkClass(label, dim=2):
        return dict(label=label, mu=np.random.random_sample((dim,)), sigma=np.random.random_sample((dim,)))
    fakeClasses = [ mkClass(label=greekName(i), dim=dim) for i in range(classes) ]
    while runForever:
        klass = np.random.choice(fakeClasses)
        label = klass['label']
        item = np.random.normal(klass['mu'], klass['sigma'])
        msg = yield ( item, str(label) )
        if msg is StopIteration:
            runForever = False

def producer(data_set_name=DATA_SET_FAKE, delay=0.001, report_interval=2):
    print(dict(data_set_name=data_set_name, delay=delay, report_interval=report_interval))
    datasetgenerator = dataSetGenFake()
    if data_set_name is DATA_SET_COVTYPE:
        datasetgenerator = dataSetGenCovtype()
    elif data_set_name is DATA_SET_KDD99:
        datasetgenerator = dataSetGenKdd99()
    # 
    kprod = KafkaProducer(
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        value_serializer=msgpack.packb,
        key_serializer=msgpack.packb,
    )
    ONE_SECOND = 10**9 
    report_interval *= ONE_SECOND
    counter = 0
    lastReport = time.time_ns()
    lastReportedCounter = 0
    nbytes = 0
    print('producer ready')
    for data, label in datasetgenerator:
        currentTime = time.time_ns()
        data = [ float(i) for i in data]
        kprod.send(topic='items', value=data, key=counter, timestamp_ms=currentTime)
        kprod.send(topic='items-classes', value={'item': data, 'label': label}, key=counter, timestamp_ms=currentTime)
        time.sleep(delay)
        nbytes += 8*len(data)
        counter += 1
        timeDiff = currentTime - lastReport
        if report_interval > 0 and timeDiff > report_interval:
            items = counter - lastReportedCounter
            timeDiff = timeDiff / ONE_SECOND
            itemSpeed = items/timeDiff
            itemTime = timeDiff/items * 1000
            byteSpeed = humanize_bytes(int(nbytes / timeDiff))
            print('{:2.4f} s, {:5} i, {:6.2f} i/s, {:4.2f} ms/i, {}/s'.format(timeDiff, items, itemSpeed, itemTime, byteSpeed))
            lastReport = currentTime
            lastReportedCounter = counter
            nbytes = 0
