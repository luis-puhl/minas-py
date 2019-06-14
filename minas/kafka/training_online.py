import time
import traceback
import os
import logging

import numpy as np
from kafka import KafkaConsumer
from kafka import KafkaProducer
import msgpack

from ..example import Example, Vector
from ..cluster import Cluster
from ..map_minas import *
from ..minas_base import *
from .req_once import req_block, decodeClusters

RADIUS_FACTOR = 1.1
EXTENTION_FACTOR = 3
BUFF_FULL = 100
MAX_K_CLUSTERS = 100
REPR_TRESHOLD = 20
CLEANUP_WINDOW = 100

def recurenceDetection(log, clusters, sleepClusters, sleepClustersCenters, unknownBuffer, classified, recurence, counter):
    if len(sleepClusters) == 0 or len(sleepClustersCenters) == 0:
        return
    if counter % 100 == 0:
        log.info(f'[recurenceDetection] unk={len(unknownBuffer)}, sleep={len(sleepClusters)}')
    sleepClustersCenters = mkCenters(sleepClusters)
    for sleepExample in unknownBuffer:
        d, cl = minDist(sleepClusters, sleepClustersCenters, sleepExample.item)
        if (d / max(1.0, cl.maxDistance)) <= RADIUS_FACTOR:
            cl.maxDistance = max(cl.maxDistance, d)
            cl.latest = counter
            sleepExample.label = cl.label
            unknownBuffer.remove(sleepExample)
            classified.append(sleepExample)
            # yield f"[CLASSIFIED] {sleepExample.n}: {cl.label}"
            # log.info(f"[CLASSIFIED] {sleepExample.n}: {cl.label}")
            if cl in sleepClusters:
                clusters.append(cl)
                sleepClusters.remove(cl)
                sleepClustersCenters = mkCenters(sleepClusters)
                # yield f"[Recurence] {cl.label}"
                log.info(f"[Recurence] {cl.label}")
                recurence.append(cl)

def noveltyDetection(log, clusters, sleepClusters, unknownBuffer, classified, extensions, noveltyIndex, novelty, counter):
    if len(unknownBuffer) % (BUFF_FULL // 10) == 0:
        # yield '[noveltyDetection]'
        log.info('[noveltyDetection]')
        newClusters = clustering([ ex.item for ex in unknownBuffer ])
        newClustersCenters = mkCenters(newClusters)
        temp_examples = {cl: [] for cl in newClusters}
        for sleepExample in unknownBuffer:
            d, cl = minDist(newClusters, newClustersCenters, sleepExample.item)
            cl.maxDistance = max(cl.maxDistance, d)
            cl.latest = counter
            cl.n += 1
            temp_examples[cl].append((sleepExample, d))
        for ncl in newClusters:
            if ncl.n < 2: continue
            distances = [ d for ex, d in temp_examples[ncl] ]
            if len(distances) == 0:
                continue
            allClusters = clusters + sleepClusters
            allClustersCenters = mkCenters(allClusters)
            distCl2Cl, nearCl2Cl = minDist(allClusters, allClustersCenters, ncl.center)
            #
            mean = sum(distances) / len(distances)
            devianceSqrSum = sum([(d - mean) **2 for d in distances])
            var = devianceSqrSum / len(distances)
            stdDevDistance = var **0.5
            silhouetteFn = lambda a, b: (b - a) / max([a, b])
            silhouette = silhouetteFn(stdDevDistance, distCl2Cl)
            if silhouette < 0: continue
            # 
            sameLabel = [ cl for cl in clusters + sleepClusters if cl.label == nearCl2Cl.label ]
            sameLabelDists = [ sum((cl1.center - cl2.center) ** 2) ** (1/2) for cl1, cl2 in itertools.combinations(sameLabel, 2) ]
            #
            if distCl2Cl / max(1.0, nearCl2Cl.maxDistance) < EXTENTION_FACTOR or distCl2Cl / max(sameLabelDists) < 2:
                # yield f'Extention {nearCl2Cl.label}'
                log.info(f'Extention {nearCl2Cl.label}')
                ncl.label = nearCl2Cl.label
                extensions.append(ncl)
            else:
                label = 'Novelty {}'.format(noveltyIndex)
                ncl.label = label
                # yield label
                log.info(label)
                novelty.append(ncl)
                kprod.send(topic='novidades', value={'label': label, 'cluster': ncl})
                noveltyIndex += 1
            clusters.append(ncl)
            for ex, d in temp_examples[ncl]:
                if ex in unknownBuffer:
                    # yield f"[CLASSIFIED] {ex.n}: {ncl.label}"
                    # log.info(f"[CLASSIFIED] {ex.n}: {ncl.label}")
                    ex.label = ncl.label
                    classified.append(ex)
                    unknownBuffer.remove(ex)
    return noveltyIndex

def training_online():
    log = logging.getLogger(__name__)
    client_id=f'client_{os.uname().machine}_{hex(os.getpid())}'
    consumer = KafkaConsumer(
        'desconhecidos', 'clusters',
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        group_id='training_online',
        client_id=client_id,
        value_deserializer=msgpack.unpackb,
        key_deserializer=msgpack.unpackb,
        # StopIteration if no message after 1 sec
        # consumer_timeout_ms=10 * 1000,
        # max_poll_records=10,
        auto_offset_reset='latest',
    )
    kprod = KafkaProducer(
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        value_serializer=msgpack.packb,
        key_serializer=msgpack.packb,
    )
    # 
    unknownBuffer = []
    sleepClusters = []
    noveltyIndex = 0
    clusters = []
    centers = []
    counter = 0
    elapsed = 0
    totalTime = time.time()
    log.info('READY')
    try:
        source = __name__
        clusters = req_block(log, consumer, kprod, client_id, source)
        log.info(f'READY {client_id}')
        for message in consumer:
            # message{ topic, partition, offset, key, value }
            if message.topic == 'clusters' and b'clusters' in message.value and b'source' in message.value and message.value[b'source'] == 'offline':
                remoteClusters = decodeClusters(message.value[b'clusters'])
                # centers = mkCenters(clusters)
                # log.info(f'got clusters {len(clusters)}')
                continue
            if message.topic != 'desconhecidos':
                continue
            # 
            init = time.time()
            example_decoded = { k.decode(encoding='utf-8'): v for k, v in message.value[b'example'].items() }
            if example_decoded['label'] is not None:
                example_decoded['label'] = example_decoded['label'].decode(encoding='utf-8')
            example = Example(**example_decoded)
            example.item = np.array(example.item)
            unknownBuffer.append(example)
            counter += 1
            if counter % 10 == 0:
                log.info(f'unknownBuffer {counter}')
            if len(clusters) == 0:
                elapsed += time.time() - init
                continue
            # 
            classified = []
            recurence = []
            extensions = []
            novelty = []
            # 
            if len(unknownBuffer) < BUFF_FULL:
                elapsed += time.time() - init
                continue
            # 
            # log.info('unknownBuffer > BUFF_FULL')
            if len(sleepClusters) > 0:
                sleepClustersCenters = mkCenters(sleepClusters)
                if len(sleepClustersCenters) > 0:
                    recurenceDetection(log, clusters, sleepClusters, sleepClustersCenters, unknownBuffer, classified, recurence, counter)
                else:
                    log.info('\n\n\tsleep Clusters Centers WARN')
                    log.info(sleepClusters)
                    log.info(sleepClustersCenters)
                    log.info('\n\n')
                # 
            #
            if len(unknownBuffer) % (BUFF_FULL // 10) == 0:
                noveltyIndex = noveltyDetection(log, clusters, sleepClusters, unknownBuffer, classified, extensions, noveltyIndex, novelty, counter)
            if counter % CLEANUP_WINDOW == 0:
                # yield '[cleanup]'
                log.info(f'[cleanup] {counter}')
                for ex in unknownBuffer:
                    if counter - ex.n < 3 * CLEANUP_WINDOW:
                        unknownBuffer.remove(ex)
                for cl in clusters:
                    if counter - cl.latest < 2 * CLEANUP_WINDOW:
                        sleepClusters.append(cl)
                        clusters.remove(cl)
                if len(clusters) == 0:
                    # yield f'[fallback] {len(sleepClusters)} => clusters'
                    log.info(f'[fallback] {len(sleepClusters)} => clusters')
                    # fallback 
                    clusters.extend(sleepClusters)
                    sleepClusters.clear()
                #
            #
            if len(classified) > 0:
                classe_contagem = {}
                for ex in classified:
                    if not ex.label in classe_contagem:
                        classe_contagem[ex.label] = 0
                    classe_contagem[ex.label] += 1
                sortedKeys = sorted(classe_contagem, key=lambda x: x if type(x) == str else '')
                classe_contagem = { k: classe_contagem[k] for k in sortedKeys }
                value = {'classe-contagem': classe_contagem, 'nbytes': example.item.nbytes, 'source': 'online'}
                kprod.send(topic='classe-contagem', value=value, key=message.key)
            if len(recurence) == 0 and len(extensions) == 0 and len(novelty) == 0:
                elapsed += time.time() - init
                continue
            # BROADCAST clusters
            clusters_serial = [ c.__getstate__() for c in clusters ]
            value = {'source': 'online', 'clusters': clusters_serial}
            kprod.send(topic='clusters', value=value, key=message.key)
            # 
            clusters_serial = [ c.__getstate__() for c in clusters ]
            value = {'source': 'online', 'clusters': clusters_serial}
            kprod.send(topic='novidades', value=value, key=message.key)

            classified
            recurence
            extensions
            novelty
            elapsed += time.time() - init
        # 
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        log.exception(ex)
        raise
    finally:
        speed = counter // max(0.001, elapsed)
        elapsed = int(elapsed)
        log.info(f'DONE {elapsed} s, consumed {counter} items, {speed} i/s, {time.time() - totalTime}')
        kprod.flush()
    #
#

# def kafka2gen(kafkaConsumer):
#     for record in kafkaConsumer:
#         yield record

# def online():
#     minasOffline
#     minas = MinasBase()
#     minas.