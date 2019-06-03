import multiprocessing as mp
import time
from multiprocessing import Process

import kafka
from kafka import KafkaProducer
from kafka import KafkaConsumer

byteOrder = 'little'
topic = 'speed-test'

producerConfings = dict(
    bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
)
consumerConfigs = dict(
    bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
    group_id='stream_share',
    consumer_timeout_ms=3 * 1000,
    auto_offset_reset='latest',
)

def kafkaProduce():
    time.sleep(0.001)
    kp = KafkaProducer(**producerConfings)
    
    endTime = time.time_ns() + 10**9
    current = time.time_ns()
    items = []
    counter = 0
    print('kafkaProduce')
    while endTime > current:
        current: int = time.time_ns()
        items.append(current)
        value = current.to_bytes(128, byteorder=byteOrder, signed=False)
        key = counter.to_bytes(128, byteorder=byteOrder, signed=False)
        kp.send(topic, value=value, key=key)
    #
    print(f'len {len(items)}')

def kafkaConsume():
    kc = KafkaConsumer(topic, **consumerConfigs)
    tofs = []
    print('kafkaConsume')
    zeroKeyFlag = True
    for message in kc:
        value: bytes = message.value
        key: bytes = message.key
        keyInt: int = int.from_bytes(key, byteorder=byteOrder, signed=False)
        if zeroKeyFlag:
            if keyInt == 0:
                zeroKeyFlag = False
            else:
                print(keyInt)
                continue
        remote: int = int.from_bytes(value, byteorder=byteOrder, signed=False)
        tof = time.time_ns() - remote
        tofs.append(tof)
    #
    summ = sum(tofs) * (10 ** (-9))
    lenn = len(tofs)
    avg = (summ / max(1, lenn))
    print('len {lenn} with {avg:.6}s avg, {summ:.6}s total'.format(lenn=lenn, summ=summ, avg=avg))

if __name__ == "__main__":
    prod = Process(target=kafkaProduce)
    cons = Process(target=kafkaConsume)
    prod.start()
    cons.start()
    prod.join()
    cons.join()