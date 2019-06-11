import time
import logging

import numpy as np
# from kafka import KafkaConsumer
from kafka import KafkaProducer
import msgpack

from minas.map_minas_support import *
from minas.ext_lib.humanize_bytes import humanize_bytes

DATA_SET_FAKE = 'DATA_SET_FAKE'
DATA_SET_COVTYPE = 'DATA_SET_COVTYPE'
DATA_SET_KDD99 = 'DATA_SET_KDD99'

def dataSetGenCovtype(log):
    from sklearn.datasets import fetch_covtype
    covtype = fetch_covtype()
    # covtype.data.shape Out[2]: (581012, 54) 581 012
    log.info(f'Dataset len {covtype.data.shape}')
    allData = list()
    for data, target in zip(covtype.data, covtype.target):
        data = [ float(i) for i in data]
        allData.append( (data, str(target)) )
    #
    return allData

def dataSetGenKdd99():
    kddNormalizeMap = list(range(40))
    kddNormalizeMap[1:3] = {}, {}, {}
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
    # kddcup99.data.shape Out[2]: (494021, 41) 494 021
    log.info(f'Dataset len {kddcup99.data.shape}')
    allData = list()
    for data, target in zip(kddcup99.data, kddcup99.target):
        data = kddNormalize(data)
        data = [ float(i) for i in data]
        allData.append( (data, str(target)) )
    #
    return allData

def dataSetGenFake(classes=5, dim=2):
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
    allData = list()
    for i in range(500000):
        klass = np.random.choice(fakeClasses)
        label = klass['label']
        item = np.random.normal(klass['mu'], klass['sigma'])
        data = [ float(i) for i in item]
        allData.append( (data, str(label)) )
    #
    return allData

ONE_SECOND = 10**9
def send_dataset(topic, dataset, kprod, counter, nbytes, report_interval, data_nbytes, init, log):
    lastReport = time.time_ns()
    for data in dataset:
        currentTime = time.time_ns()
        counter += 1
        nbytes += data_nbytes
        kprod.send(topic=topic, value=data, key=counter, timestamp_ms=currentTime)
        if report_interval > 0 and currentTime - lastReport > report_interval:
            timeDiff = (currentTime - init) / ONE_SECOND
            itemSpeed = counter / timeDiff
            itemTime = timeDiff / counter * 1000
            byteSpeed = humanize_bytes(int(nbytes / timeDiff))
            log.info('{:2.4f} s, {:5} i, {:6.2f} i/s, {:4.2f} ms/i, {}/s'.format(timeDiff, counter, itemSpeed, itemTime, byteSpeed))
            lastReport = currentTime
    kprod.flush()
    return ( counter, nbytes )

def producer_imp(log=None, data_set_name=DATA_SET_FAKE, delay=0.001, report_interval=2):
    setup_init = time.time()
    if log is None:
        log = logging.getLogger(__name__)
    log.info(f'data_set_name={data_set_name}, delay={delay}, report_interval={report_interval}')
    if data_set_name == DATA_SET_FAKE:
        datasetgenerator = dataSetGenFake(log=log)
    if data_set_name == DATA_SET_COVTYPE:
        datasetgenerator = dataSetGenCovtype(log=log)
    elif data_set_name == DATA_SET_KDD99:
        datasetgenerator = dataSetGenKdd99(log=log)
    #
    data, label = datasetgenerator[0]
    data_np = np.array(data)
    data_nbytes = data_np.nbytes
    packed = msgpack.packb(data)
    log.info(f'data size={len(data)}, nbytes={data_nbytes}, serial={len(data)}, packed={len(packed)}, \n\t{repr(data)}\n=>\t{packed}')
    # 
    halfDataLen = int(len(datasetgenerator)/2)
    trainingData = [ {'item': data, 'label': label} for data, label in datasetgenerator[0:halfDataLen] ]
    testData = [ data for data, label in datasetgenerator[halfDataLen:] ]
    # 
    kprod = KafkaProducer(
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        value_serializer=msgpack.packb,
        key_serializer=msgpack.packb,
        # batch_size = 16384 = 2**14
        batch_size=halfDataLen
    )
    report_interval *= ONE_SECOND
    counter = 0
    nbytes = 0
    lastReport = time.time_ns()
    init = time.time_ns()
    timeDiff = 0
    log.info(f'READY in {time.time() - setup_init} s')
    # TODO: separar dados rotulados e não rotulados nessa etapa
    # TODO: carregar tudo na memória
    # TODO: testar também com 1/2 para treinamento com validação cruzada
    # TODO: testar N-fold cross validation
    # 
    try:
        counter, nbytes = send_dataset('items-classes', trainingData, kprod, counter, nbytes, report_interval, data_nbytes, init, log)
        log.info('trainingData all produced')
        # 
        # Dado não rotulado para classificadores
        init_time = time.time_ns()
        kprod.send(topic='items', value={'init_time': init_time}, key=counter)
        counter, nbytes = send_dataset('items', testData, kprod, counter, nbytes, report_interval, data_nbytes, init, log)
        log.info('testData all produced')
    finally:
        currentTime = time.time_ns()
        timeDiff = currentTime - init
        items = max(counter, 1)
        timeDiff = timeDiff / ONE_SECOND
        itemSpeed = items/timeDiff
        itemTime = timeDiff/items * 1000
        byteSpeed = humanize_bytes(int(nbytes / timeDiff))
        log.info('total produced: {:2.4f} s, {:5} i, {:6.2f} i/s, {:4.2f} ms/i, {}/s'.format(timeDiff, items, itemSpeed, itemTime, byteSpeed))
    
def producer(**kwargs):
    log = logging.getLogger(__name__)
    kwargs['log'] = log
    try:
        producer_imp(**kwargs)
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        log.exception(log)
        exit(1)
