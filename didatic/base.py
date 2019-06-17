import time
import os
import logging
import logging.config

import yaml
from kafka import KafkaProducer
from kafka import KafkaConsumer
import msgpack
from multiprocessing_logging import install_mp_handler

from humanize_bytes import humanize_bytes

with open('./didatic/logging.conf.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
logging.config.dictConfig(config)
install_mp_handler()

ONE_SECOND = 10**9
report_interval = 10 * ONE_SECOND

def report(currentTime, prefix, lastReport, init, counter, nbytes, extra=None, key=None, log=None, name=None):
    timeDiff = (currentTime - init) / ONE_SECOND
    itemSpeed = counter / timeDiff
    itemTime = timeDiff / max(counter, 1) * 1000
    byteSpeed = humanize_bytes(int(nbytes / timeDiff))
    extra = '' if extra is None else '\n\t' + repr(extra)
    key = '' if key is None else ' ' + repr(key)
    msg = '{} {:2.4f} s, {:5} i, {:6.2f} i/s, {:4.2f} ms/i, {}/s{}{}'
    return msg.format(prefix, timeDiff, counter, itemSpeed, itemTime, byteSpeed, key, extra)

def wrap(fn):
    init = time.time_ns()
    lastReport = init
    nbytes = 0
    counter = 0
    name = fn.__name__
    log = logging.getLogger(name)
    log.info(f'init {name}')
    prefix = f'{name}_{hex(os.getpid())}'
    kwargs = dict(init=init, lastReport=lastReport, nbytes=nbytes, counter=counter, log=log, prefix=prefix, name=name, )
    try:
        kwargs = fn(**kwargs)
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        log.exception(ex)
        raise
    finally:
        del kwargs['prefix']
        msg = report(currentTime=time.time_ns(), prefix=f'{prefix} DONE', **kwargs)
        log.info(msg)
    exit(0)