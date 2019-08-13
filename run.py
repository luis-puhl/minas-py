#!python
import time
import argparse
import signal
import multiprocessing
from multiprocessing import Process
import concurrent.futures
import os
import logging

import yaml
from multiprocessing_logging import install_mp_handler
from kafka import KafkaAdminClient
# from numba import jit

from minas import producer
from minas import classifier
from minas import training_offline
from minas import training_online
from minas import final_consumer

def setupLog():
    with open('logging.conf.yaml', 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    logging.config.dictConfig(config)
    install_mp_handler()

def main():
    setupLog()
    log = logging.getLogger(__name__)
    log.info('INIT MINAS MAIN RUN.Py')

    parser = argparse.ArgumentParser(description='Minas Entrypoint.')
    # parser.add_argument("-c", "--classifier", type=int, default=0, help="Start item classifiers")
    parser.add_argument("-p", "--producer", action="store_true", help="Start item producer")
    parser.add_argument("-c", "--classifier", action="store_true", help="Start item classifier")
    parser.add_argument("-t", "--offline", action="store_true", help="Start offline training")
    parser.add_argument("-o", "--online", action="store_true", help="Start online training")
    parser.add_argument("-f", "--final", action="store_true", help="Start final consumer")
    args = parser.parse_args()

    # pool = multiprocessing.Pool()
    start_all = not (args.producer or args.classifier or args.offline or args.online or args.final)
    print('start_all', start_all)
    # kadmin = KafkaAdminClient(
    #     bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
    # )
    # kadmin.delete_topics()
    processes = []
    try:
        if args.producer or start_all:
            # pool.apply_async(func=producer, kwds={'report_interval': 10})
            # pool.apply_async(func=producer, kwds={'report_interval': 10, 'delay': 0, 'data_set_name': 'DATA_SET_COVTYPE'})
            # pool.apply_async(func=tryWrap, kwds={'fn': producer, 'kwds': {'report_interval': 10, 'delay': 0, 'data_set': 'DATA_SET_COVTYPE'}})
            # p = Process(target=producer, name='producer', kwargs={'report_interval': 10, 'delay': 0, 'data_set_name': 'DATA_SET_COVTYPE'})
            p = Process(target=producer, name='producer', kwargs={'report_interval': 10, 'delay': 0, 'data_set_name': 'DATA_SET_KDD99'})
            processes.append(p)
            p.start()
        if args.offline or start_all:
            # pool.apply_async(training_offline)
            p = Process(target=training_offline, name='training_offline')
            processes.append(p)
            p.start()
        if args.online or start_all:
            # pool.apply_async(training_online)
            p = Process(target=training_online, name='training_online')
            processes.append(p)
        if args.final or start_all:
            # pool.apply_async(final_consumer)
            p = Process(target=final_consumer, name='final_consumer')
            processes.append(p)
        if args.classifier or start_all:
            for i in range(os.cpu_count()):
                # pool.apply_async(classifier)
                p = Process(target=classifier, name=f'classifier-{i}')
                processes.append(p)
        for p in processes:
            if not p.is_alive() and p.exitcode is None:
                p.start()
        print('processes started', processes)
        # 
        while len(processes) > 0:
            time.sleep(1)
            for p in processes:
                is_alive = False
                try:
                    is_alive = p.is_alive()
                except:
                    pass
                if not is_alive:
                    exitcode = 0
                    try:
                        p.join()
                        exitcode = p.exitcode
                        p.close()
                    except:
                        pass
                    processes.remove(p)
                    if len(processes) > 5:
                        log.info(f'process done {p.name}, {len(processes)} remaining')
                    else:
                        names = [ p.name for p in processes ]
                        log.info(f'process done {p.name}, {names} remaining')
                    name = p.name
                    if exitcode != 0:
                        raise Exception(f'Child died with error. {name} Exit code {exitcode}')
    except Exception as ex:
        log.exception(ex)
        log.info(f'Exception join {p.name}, {len(processes)}')
        log.info(processes)
        for p in processes:
            try:
                p.terminate()
                p.join()
            except:
                pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass