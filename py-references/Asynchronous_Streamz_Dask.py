import time
from streamz import Stream
from dask.distributed import Client
from tornado.ioloop import IOLoop

def increment(x):
    """ A blocking increment function

    Simulates a computational function that was not designed to work
    asynchronously
    """
    time.sleep(0.1)
    return x + 1

def write(*args, **kwargs):
    print(*args, **kwargs)

async def f():
    client = await Client('tcp://192.168.15.14:8786', processes=False, asynchronous=True)
    source = Stream(asynchronous=True)
    source.scatter().map(increment).rate_limit('500ms').gather().sink(write)

    for x in range(10):
        await source.emit(x)

IOLoop().run_sync(f)
