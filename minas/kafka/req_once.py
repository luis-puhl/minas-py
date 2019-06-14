
import numpy as np

from ..cluster import Cluster

def decodeClusters(clusters):
    clustersDecoded = []
    for cl in clusters:
        decoded = { k.decode(encoding='utf-8'): v for k, v in cl.items() }
        decoded['center'] = np.array(decoded['center'])
        decoded['label'] = decoded['label'].decode(encoding='utf-8')
        clustersDecoded.append(Cluster(**decoded))
    return clustersDecoded

def req_block(log, consumer, kprod, client_id, source):
    counter = 0
    while True:
        log.info(f'WAIT ON CLUSTERS {client_id}')
        kprod.send(topic='clusters', value={'source': source, 'action': 'request'})
        for message in consumer:
            if message.topic == 'clusters' and b'clusters' in message.value:
                clusters = decodeClusters(message.value[b'clusters'])
                return clusters
            if message.topic in ['items', 'desconhecidos']:
                counter += 1
            else:
                log.info(f'{message.topic} => {message.value}')
            if counter % 1000 == 0:
                log.info(f'Discarted {counter} items')