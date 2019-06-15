from base import *

def prod(**kwargs):
    kwargs['log'] = kwargs['log'] if 'log' in kwargs else logging.getLogger(__name__)
    kwargs['init'] = kwargs['init'] if 'init' in kwargs else time.time_ns()
    kwargs['lastReport'] = kwargs['lastReport'] if 'lastReport' in kwargs else init
    kwargs['nbytes'] = kwargs['nbytes'] if 'nbytes' in kwargs else 0
    kwargs['counter'] = kwargs['counter'] if 'counter' in kwargs else 0
    kwargs['prefix'] = kwargs['prefix'] if 'prefix' in kwargs else __name__
    kprod = KafkaProducer(
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        key_serializer=msgpack.packb,
    )

    for i in range(500000):
        kwargs['counter'] = i
        value = msgpack.packb(kwargs['counter'])
        kwargs['nbytes'] += len(value)
        kprod.send(topic='numbers', value=value, key=kwargs['counter'])
        currentTime = time.time_ns()
        if currentTime - kwargs['lastReport'] > report_interval:
            report(currentTime=currentTime, **kwargs)
            kwargs['lastReport'] = currentTime
    return kwargs

if __name__ == "__main__":
    wrap(prod)
