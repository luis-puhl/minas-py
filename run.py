import time
import argparse
import signal
import multiprocessing
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

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def main():
    setupLog()

    parser = argparse.ArgumentParser(description='Minas Entrypoint.')
    # parser.add_argument("-c", "--classifier", type=int, default=0, help="Start item classifiers")
    parser.add_argument("-p", "--producer", action="store_true", help="Start item producer")
    parser.add_argument("-c", "--classifier", action="store_true", help="Start item classifier")
    parser.add_argument("-t", "--offline", action="store_true", help="Start offline training")
    parser.add_argument("-o", "--online", action="store_true", help="Start online training")
    parser.add_argument("-f", "--final", action="store_true", help="Start final consumer")
    args = parser.parse_args()

    pool = multiprocessing.Pool()
    start_all = not (args.producer or args.classifier or args.offline or args.online or args.final)
    print('start_all', start_all)
    if args.producer or start_all:
        # pool.apply_async(func=producer, kwds={'report_interval': 10})
        pool.apply_async(func=producer, kwds={'report_interval': 10, 'delay': 0})
    if args.offline or start_all:
        pool.apply_async(training_offline)
    if args.online or start_all:
        pool.apply_async(training_online)
    if args.final or start_all:
        pool.apply_async(final_consumer)
    if args.classifier or start_all:
        for i in range(os.cpu_count() - 5):
            pool.apply_async(classifier)
    print('processes started')

    try:
        while True:
            time.sleep(100)
    except KeyboardInterrupt:
        pool.terminate()
        pool.join()
    else:
        pool.close()
        pool.join()

if __name__ == "__main__":
    main()