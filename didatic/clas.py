import argparse
import multiprocessing
from multiprocessing import Process

from base import *

def clas(name='clas', client_id=None, **kwargs):
    log = kwargs['log'] if 'log' in kwargs else logging.getLogger(name)
    kwargs['init'] = kwargs['init'] if 'init' in kwargs else time.time_ns()
    kwargs['lastReport'] = kwargs['lastReport'] if 'lastReport' in kwargs else init
    kwargs['nbytes'] = kwargs['nbytes'] if 'nbytes' in kwargs else 0
    kwargs['counter'] = kwargs['counter'] if 'counter' in kwargs else 0
    kwargs['prefix'] = kwargs['prefix'] if 'prefix' in kwargs else name
    # 
    if client_id is None:
        client_id = f'{name}_{hex(os.getpid())}'
    consumer = KafkaConsumer(
        'numbers',
        bootstrap_servers='localhost',
        group_id=name,
        client_id=client_id,
        # value_deserializer=msgpack.unpackb,
        key_deserializer=msgpack.unpackb,
        # StopIteration if no message after 1 sec
        consumer_timeout_ms=60 * 1000,
        # max_poll_records=10,
        auto_offset_reset='latest',
        # auto_offset_reset='earliest',
        # enable_auto_commit=False,
    )
    kprod = KafkaProducer(
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        value_serializer=msgpack.packb,
        key_serializer=msgpack.packb,
    )

    kwargs['lastReport'] = kwargs['init'] - report_interval
    resume = {'unknown': 0, 'not_prime': 0, 'total_clas': 0}
    partitions = {}
    # consumer
    for record in consumer:
        # consumer.com
        kwargs['counter'] += 1
        kwargs['nbytes'] += len(record.value)
        if record.partition not in partitions:
            partitions[record.partition] = 0
        partitions[record.partition] += 1
        value = msgpack.unpackb(record.value)
        resume['total_clas'] += 1
        if value % 2 == 0 or value % 3 == 0:
            resume['not_prime'] += 1
        else:
            resume['unknown'] += 1
            kprod.send(topic='unknown', value=value, key=record.key)
        # 
        currentTime = time.time_ns()
        if currentTime - kwargs['lastReport'] > report_interval:
            # committed = consumer.committed()
            kprod.send(topic='result', value=resume, key=record.key)
            resume['partitions'] = partitions
            log.info( report(currentTime=currentTime, key=record.key, extra=resume, **kwargs) )
            kwargs['lastReport'] = currentTime
            resume = {'unknown': 0, 'not_prime': 0, 'total_clas': 0}
    kwargs['extra'] = {**resume, 'partitions': partitions}
    return kwargs

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Minas Entrypoint.')
    parser.add_argument('--classifiers', type=int, default=1, help='Number of classifiers')
    args = parser.parse_args()
    processes = []
    try:
        for i in range(args.classifiers):
            p = Process(target=wrap, name=f'classifier-{i}', args=(clas,))
            p.start()
            processes.append(p)
        while len(processes) > 2:
            time.sleep(5)
            for p in processes:
                if not p.is_alive():
                    print('end', p.exitcode, p.name, hex(p.pid), len(processes))
                    processes.remove(p)
                    p.close()
            print('waiting', len(processes))
        for i in range(10):
            for p in processes:
                p.join(1)
                if not p.is_alive():
                    print('join end', p.exitcode, p.name, hex(p.pid), len(processes))
                    processes.remove(p)
                    p.close()
                else:
                    print('join waiting', p, p.name, hex(p.pid), len(processes))
    except Exception as ex:
        print(ex)
        for p in processes:
            p.terminate()
        if type(ex) is not KeyboardInterrupt:
            raise
    print(__name__, 'DONE')
    exit(0)

