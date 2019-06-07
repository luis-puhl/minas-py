import time
import argparse
import signal
import multiprocessing
import concurrent.futures

# from numba import jit

from minas import producer
from minas import classifier
from minas import training_offline
from minas import training_online
from minas import final_consumer

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def main():
    parser = argparse.ArgumentParser(description='Minas Entrypoint.')
    # parser.add_argument("-c", "--classifier", type=int, default=0, help="Start item classifiers")
    parser.add_argument("-p", "--producer", action="store_true", help="Start item producer")
    parser.add_argument("-c", "--classifier", action="store_true", help="Start item classifier")
    parser.add_argument("-t", "--offline", action="store_true", help="Start offline training")
    parser.add_argument("-o", "--online", action="store_true", help="Start online training")
    parser.add_argument("-f", "--final", action="store_true", help="Start final consumer")
    parser.add_argument("-a", "--all", action="store_true", help="Start all ")
    args = parser.parse_args()

    pool = multiprocessing.Pool(initializer=init_worker)
    if args.producer or args.all:
        pool.apply_async(func=producer, kwds={'report_interval': 0})
    if args.classifier or args.all:
        pool.apply_async(classifier)
    if args.offline or args.all:
        pool.apply_async(training_offline)
    if args.online or args.all:
        pool.apply_async(training_online)
    if args.final or args.all:
        pool.apply_async(final_consumer)

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