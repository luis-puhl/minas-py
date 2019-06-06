import time
import argparse
import signal
import multiprocessing
import concurrent.futures

# from numba import jit

from minas import producer
from minas import classifier

def init_worker():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def main():
    parser = argparse.ArgumentParser(description='Minas Entrypoint.')
    # parser.add_argument("-c", "--classifier", type=int, default=0, help="Start item classifiers")
    parser.add_argument("-c", "--classifier", action="store_true", help="Start item classifier")
    parser.add_argument("-p", "--producer", action="store_true", help="Start item producer")
    args = parser.parse_args()

    pool = multiprocessing.Pool(5, init_worker)
    if args.producer:
        pool.apply_async(producer)
    if args.classifier:
        pool.apply_async(classifier)

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