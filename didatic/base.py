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

def report(log, currentTime, prefix, lastReport, init, counter, nbytes, extra=''):
    timeDiff = (currentTime - init) / ONE_SECOND
    itemSpeed = counter / timeDiff
    itemTime = timeDiff / max(counter, 1) * 1000
    byteSpeed = humanize_bytes(int(nbytes / timeDiff))
    if len(extra) > 0:
        extra = '\n\t' + extra
    log.info('{} {:2.4f} s, {:5} i, {:6.2f} i/s, {:4.2f} ms/i, {}/s{}'.format(prefix, timeDiff, counter, itemSpeed, itemTime, byteSpeed, extra))

def wrap(fn):
    init = time.time_ns()
    lastReport = init
    nbytes = 0
    counter = 0
    log = logging.getLogger(fn.__name__)
    log.info(f'init {fn.__name__}')
    prefix = f'{fn.__name__}_{hex(os.getpid())}'
    kwargs = dict(init=init, lastReport=lastReport, nbytes=nbytes, counter=counter, log=log, prefix=prefix, )
    try:
        kwargs = fn(**kwargs)
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        log.exception(ex)
        raise
    finally:
        del kwargs['prefix']
        report(currentTime=time.time_ns(), prefix=f'{prefix} DONE', **kwargs)