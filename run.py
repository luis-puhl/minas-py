# import time
import argparse
import concurrent.futures

# from numba import jit

from minas import producer
from minas import classifier

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Minas Entrypoint.')
    # parser.add_argument("-c", "--classifier", type=int, default=0, help="Start item classifiers")
    parser.add_argument("-c", "--classifier", action="store_true", help="Start item classifier")
    parser.add_argument("-p", "--producer", action="store_true", help="Start item producer")
    args = parser.parse_args()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        if args.producer:
            executor.submit(producer)
        if args.classifier:
            executor.submit(classifier)