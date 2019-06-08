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

def training_online():
    log = logging.getLogger(__name__)
    consumer = KafkaConsumer(
        'desconhecidos', 'clusters',
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        group_id='training_online',
        client_id=f'client_{os.uname().machine}_{hex(os.getpid())}',
        value_deserializer=msgpack.unpackb,
        key_deserializer=msgpack.unpackb,
        # StopIteration if no message after 1 sec
        # consumer_timeout_ms=1 * 1000,
        # max_poll_records=10,
        auto_offset_reset='latest',
    )
    kprod = KafkaProducer(
        bootstrap_servers='localhost:9092,localhost:9093,localhost:9094',
        value_serializer=msgpack.packb,
        key_serializer=msgpack.packb,
    )
    # 
    RADIUS_FACTOR = 1.1
    EXTENTION_FACTOR = 3
    BUFF_FULL = 100
    MAX_K_CLUSTERS = 100
    REPR_TRESHOLD = 20
    CLEANUP_WINDOW = 100
    # 
    unknownBuffer = []
    # clusters=[cl for cl in inClusters]
    # centers = mkCenters(clusters)
    sleepClusters = []
    # counter = 0
    noveltyIndex = 0
    # sentinel = object()
    # 
    clusters = []
    centers = []
    example_buffer = []
    classe_contagem = {}
    counter = 0
    elapsed = 0
    log.info('READY')
    try:
        for message in consumer:
            # message{ topic, partition, offset, key, value }
            if message.topic == 'clusters':
                clusters = []
                for c in message.value[b'clusters']:
                    c_decoded = { k.decode(encoding="utf-8"): v for k, v in c.items() }
                    c_decoded['center'] = np.array(c_decoded['center'])
                    c_decoded['label'] = c_decoded['label'].decode(encoding="utf-8")
                    clusters.append(Cluster(**c_decoded))
                centers = mkCenters(clusters)
                log.info(f'got clusters {len(clusters)}')
                continue
            if message.topic == 'desconhecidos':
                example_decoded = { k.decode(encoding="utf-8"): v for k, v in message.value[b'example'].items() }
                if example_decoded['label'] is not None:
                    example_decoded['label'] = example_decoded['label'].decode(encoding="utf-8")
                example = Example(**example_decoded)
                unknownBuffer.append(example)
            counter += 1
            log.info(f'unknownBuffer {counter}')
            if len(clusters) == 0:
                continue
            init = time.time()
            if len(unknownBuffer) > BUFF_FULL:
                log.info('unknownBuffer > BUFF_FULL')
                if len(sleepClusters) > 0:
                    # yield f'[recurenceDetection] unk={len(unknownBuffer)}, sleep={len(sleepClusters)}'
                    log.info(f'[recurenceDetection] unk={len(unknownBuffer)}, sleep={len(sleepClusters)}')
                    for sleepExample in unknownBuffer:
                        d, cl = minDist(sleepClusters, sleepExample.item)
                        if (d / max(1.0, cl.maxDistance)) <= RADIUS_FACTOR:
                            cl.maxDistance = max(cl.maxDistance, d)
                            cl.latest = counter
                            unknownBuffer.remove(sleepExample)
                            # yield f"[CLASSIFIED] {sleepExample.n}: {cl.label}"
                            log.info(f"[CLASSIFIED] {sleepExample.n}: {cl.label}")
                            if cl in sleepClusters:
                                clusters.append(cl)
                                sleepClusters.remove(cl)
                                # yield f"[Recurence] {cl.label}"
                                log.info(f"[Recurence] {cl.label}")
                if len(unknownBuffer) % (BUFF_FULL // 10) == 0:
                    # yield '[noveltyDetection]'
                    log.info('[noveltyDetection]')
                    newClusters = clustering([ ex.item for ex in unknownBuffer ])
                    temp_examples = {cl: [] for cl in newClusters}
                    for sleepExample in unknownBuffer:
                        d, cl = minDist(newClusters, sleepExample.item)
                        cl.maxDistance = max(cl.maxDistance, d)
                        cl.latest = counter
                        cl.n += 1
                        temp_examples[cl].append((sleepExample, d))
                    for ncl in newClusters:
                        if ncl.n < 2: continue
                        distances = [ d for ex, d in temp_examples[ncl] ]
                        if len(distances) == 0: continue
                        distCl2Cl, nearCl2Cl = minDist(clusters + sleepClusters, ncl.center)
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
                        else:
                            label = 'Novelty {}'.format(noveltyIndex)
                            ncl.label = label
                            # yield label
                            log.info(label)
                            kprod.send(topic='novidades', value={'label': label, 'cluster': ncl})
                            noveltyIndex += 1
                        clusters.append(ncl)
                        for ex, d in temp_examples[ncl]:
                            if ex in unknownBuffer:
                                # yield f"[CLASSIFIED] {ex.n}: {ncl.label}"
                                log.info(f"[CLASSIFIED] {ex.n}: {ncl.label}")
                                unknownBuffer.remove(ex)
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
            elapsed += time.time() - init
        # 
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        log.exception(ex)
        raise
    finally:
        speed = counter // max(0.001, elapsed)
        elapsed = int(elapsed * 1000)
        log.info(f'consumer {client_id}: {elapsed} ms, consumed {counter} items, {speed} i/s', time.time() - totalTime)
        kprod.flush()
    #
#
