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
    processes = []
    if args.producer or start_all:
        # pool.apply_async(func=producer, kwds={'report_interval': 10})
        # pool.apply_async(func=producer, kwds={'report_interval': 10, 'delay': 0, 'data_set_name': 'DATA_SET_COVTYPE'})
        # pool.apply_async(func=tryWrap, kwds={'fn': producer, 'kwds': {'report_interval': 10, 'delay': 0, 'data_set': 'DATA_SET_COVTYPE'}})
        p = Process(target=producer, kwargs={'report_interval': 10, 'delay': 0, 'data_set_name': 'DATA_SET_COVTYPE'})
        processes.append(p)
    if args.offline or start_all:
        # pool.apply_async(training_offline)
        p = Process(target=training_offline)
        processes.append(p)
    if args.online or start_all:
        # pool.apply_async(training_online)
        p = Process(target=training_online)
        processes.append(p)
    if args.final or start_all:
        # pool.apply_async(final_consumer)
        p = Process(target=final_consumer)
        processes.append(p)
    if args.classifier or start_all:
        for i in range(os.cpu_count()):
            # pool.apply_async(classifier)
            p = Process(target=classifier)
            processes.append(p)
    for p in processes:
        p.start()
    print('processes started')

    try:
        while len(processes) > 0:
            time.sleep(10)
            for p in processes:
                if not p.is_alive():
                    p.close()
                    try:
                        p.join()
                    except:
                        pass
                    processes.remove(p)
    except KeyboardInterrupt:
        # pool.terminate()
        # pool.join()
        for p in processes:
            p.terminate()
            p.join()
    else:
        # pool.close()
        # pool.join()
        for p in processes:
            p.close()
            p.join()

if __name__ == "__main__":
    main()