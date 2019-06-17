from base import *

def detc(name='detc', **kwargs):
    log = kwargs['log'] if 'log' in kwargs else logging.getLogger(name)
    kwargs['init'] = kwargs['init'] if 'init' in kwargs else time.time_ns()
    kwargs['lastReport'] = kwargs['lastReport'] if 'lastReport' in kwargs else init
    kwargs['nbytes'] = kwargs['nbytes'] if 'nbytes' in kwargs else 0
    kwargs['counter'] = kwargs['counter'] if 'counter' in kwargs else 0
    kwargs['prefix'] = kwargs['prefix'] if 'prefix' in kwargs else name
    prefix = kwargs['prefix']
    # 
    consumer = KafkaConsumer(
        'unknown',
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        group_id=name,
        client_id=kwargs['prefix'],
        # value_deserializer=msgpack.unpackb,
        key_deserializer=msgpack.unpackb,
        # StopIteration if no message after 1 sec
        consumer_timeout_ms=10 * 1000,
        # max_poll_records=10,
        # auto_offset_reset='latest',
        auto_offset_reset='earliest',
    )
    kprod = KafkaProducer(
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        value_serializer=msgpack.packb,
        key_serializer=msgpack.packb,
    )

    allPrimes = [ 2 ]
    resume = {'prime': 0, 'not_prime': 0}
    for record in consumer:
        kwargs['counter'] += 1
        kwargs['nbytes'] += len(record.value)
        value = msgpack.unpackb(record.value)
        for prime in allPrimes:
            if value % prime == 0:
                resume['not_prime'] += 1
                break
        else:
            allPrimes.append(value)
            resume['prime'] += 1
        # 
        currentTime = time.time_ns()
        if currentTime - kwargs['lastReport'] > report_interval:
            kprod.send(topic='result', value=resume, key=record.key)
            log.info( report(currentTime=currentTime, key=record.key, extra=resume, **kwargs) )
            kwargs['lastReport'] = currentTime
            resume = {'prime': 0, 'not_prime': 0}
    log.info( report(currentTime=time.time_ns(), extra=resume, **kwargs) )
    return kwargs

if __name__ == "__main__":
    wrap(detc)
