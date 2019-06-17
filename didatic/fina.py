from base import *

def fina(name='detc', group_id=0, **kwargs):
    log = kwargs['log'] if 'log' in kwargs else logging.getLogger(name)
    kwargs['init'] = kwargs['init'] if 'init' in kwargs else time.time_ns()
    kwargs['lastReport'] = kwargs['lastReport'] if 'lastReport' in kwargs else init
    kwargs['nbytes'] = kwargs['nbytes'] if 'nbytes' in kwargs else 0
    kwargs['counter'] = kwargs['counter'] if 'counter' in kwargs else 0
    kwargs['prefix'] = kwargs['prefix'] if 'prefix' in kwargs else name
    # 
    consumer = KafkaConsumer(
        'result',
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        group_id=name,
        client_id=kwargs['prefix'],
        # value_deserializer=msgpack.unpackb,
        key_deserializer=msgpack.unpackb,
        # StopIteration if no message after 1 sec
        consumer_timeout_ms=4* 60 * 1000,
        # max_poll_records=10,
        auto_offset_reset='latest',
        # auto_offset_reset='earliest',
    )

    resume = {'prime': 0, 'not_prime': 0}
    for record in consumer:
        kwargs['counter'] += 1
        kwargs['nbytes'] += len(record.value)
        value = msgpack.unpackb(record.value)
        for key, value in value.items():
            key = key.decode('utf-8')
            if key not in resume:
                resume[key] = 0
            resume[key] += value
        # 
        currentTime = time.time_ns()
        if currentTime - kwargs['lastReport'] > report_interval:
            resume['total'] = resume['prime'] + resume['not_prime']
            log.info( report(currentTime=currentTime, key=record.key, extra=resume, **kwargs) )
            kwargs['lastReport'] = currentTime
    resume['total'] = resume['prime'] + resume['not_prime']
    kwargs['extra'] = resume
    return kwargs

if __name__ == "__main__":
    wrap(fina)
