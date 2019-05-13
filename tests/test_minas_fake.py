import unittest
import os
import queue
import asyncio
import time
import sys
import shutil
import logging
import csv
import io
from typing import List
from copy import deepcopy

import yaml
import matplotlib
import numpy as np
import pandas as pd
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from dask.distributed import Client

from minas.timed import Timed
from minas.cluster import Cluster
from minas.example import Example
from minas.minas_algo import MinasAlgorith, MinasConsts
from minas.minas_base import MinasBase

from .plots import *

class MinasFakeExamplesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # setupLog()
        with open('logging.conf.yaml', 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        logging.config.dictConfig(config)
    @classmethod
    def tearDownClass(cls):
        pass
    def setUp(self):
        self.basedir = 'run/seeds/'
    def tearDown(self):
        pass

    def setupFakeExamples(self, seed):
        np.random.seed(seed)
        attributes = np.random.randint(2, 40)
        examples = []
        for labelIndex in range(np.random.randint(2, 5)):
            mu = np.random.random() * 10
            sigma = np.random.random() * 5
            for exampleIndex in range(np.random.randint(200, 1000)):
                example = Example(item = [], label = 'Class #' + str(labelIndex))
                for i in range(attributes):
                    value = np.random.normal(loc=mu, scale=sigma)
                    example.item.append(float(value))
                examples.append(example)
        np.random.shuffle(examples)
        return examples
    
    def fake_seed(self, seed):
        dirr = self.basedir + str(seed) + '/'
        if os.path.exists(dirr):
            shutil.rmtree(dirr)
        if not os.path.exists(dirr):
            os.makedirs(dirr)
        timed = Timed()
        TimedMinasAlgorith = timed.timedClass(MinasAlgorith)
        CONSTS=MinasConsts()
        logging.info('Next seed: {}'.format(seed))
        minas = MinasBase(minasAlgorith=TimedMinasAlgorith(CONSTS=CONSTS))
        # 
        rootLogger = logging.getLogger()
        logHandler = logging.FileHandler(dirr + 'run.log')
        logHandler.formatter = rootLogger.handlers[0].formatter
        rootLogger.addHandler(logHandler)
        # ------------------------------------------------------------------------------------------------
        examples = self.setupFakeExamples(seed)
        plotExamples2D(dirr, '0-fake_base', examples)
        # ------------------------------------------------------------------------------------------------
        training_set = examples[:int(len(examples) * .1)]
        with open(dirr + 'training_set.csv', 'w') as training_set_csv:
            for ex in training_set:
                training_set_csv.write(','.join([str(i) for i in ex.item]) + ',' + ex.label + '\n')
        plotExamples2D(dirr, '1-training_set', training_set)
        
        trainingDf = pd.DataFrame(map(lambda x: {'item': x.item, 'label': x.label}, training_set))
        logging.info('trainingDf' + '\n' + str(trainingDf.groupby('label').describe()) + '\n')
        minas.offline(trainingDf)
        minas.storeToFile(dirr + 'minas.yaml')
        minas.restoreFromFile(dirr + 'minas.yaml')
        logging.info(str(minas) + str(minas))
        self.assertGreater(len(minas.clusters), 0, 'model must be trainded after offline call')
        
        plotExamples2D(dirr, '2-offline_clusters', [], minas.clusters)
        plotExamples2D(dirr, '3-offline_training', training_set, minas.clusters)
        plotExamples2D(dirr, '4-offline_all_data', examples, minas.clusters)
        minas.minasAlgorith.checkTraining(trainingDf, minas.clusters)
        # ------------------------------------------------------------------------------------------------
        testSet = examples[int(len(examples) * .1):]
        minas.online( i.item for i in testSet )
        # ------------------------------------------------------------------------------------------------
        logging.info('aggregatin resutls')
        results = []
        positiveCount = 0
        negativeCount = 0
        unknownCount = 0
        totalExamples = len(examples)
        with open(dirr + 'examples.csv', 'w') as examplesCsv:
            for ex in examples:
                ex = deepcopy(ex)
                hasLabel, cluster, d = None, None, None
                if minas:
                    hasLabel, cluster, d, ex = minas.classify(ex)
                examplesCsv.write(
                    ','.join([str(i) for i in ex.item]) + ',' +
                    ex.label + ',' +
                    (cluster.label if cluster and hasLabel else 'Unknown') + ',' +
                    ('Positive' if cluster and cluster.label == ex.label else 'Negative') +
                    '\n'
                )
                if hasLabel:
                    if cluster.label == ex.label:
                        ex.label = 'Positive'
                        positiveCount += 1
                    else:
                        ex.label = 'Negative'
                        negativeCount += 1
                else:
                    ex.label = 'Unknown'
                    unknownCount += 1
                results.append(ex)
                # end results map
        result = '[seed {seed}] positive: {p}({pp:.2%}), negative: {n}({nn:.2%}), unknown: {u}({uu:.2%})'.format(
            seed=seed,
            p=positiveCount, pp=positiveCount/totalExamples,
            n=negativeCount, nn=negativeCount/totalExamples,
            u=unknownCount, uu=unknownCount/totalExamples,
        )
        logging.info('\n\n\t=== Final Results ===\n{model}\n{result}\n'.format(model=str(minas), result=result))
        plotExamples2D(dirr, '5-online_clusters', [], minas.clusters if minas else [])
        plotExamples2D(dirr, '6-online_resutls', results, minas.clusters if minas else [])
        onlyFalses = [x for x in results if x.label is not 'Positive']
        plotExamples2D(dirr, '7-online_neg_unk', onlyFalses, minas.clusters if minas else [])
        del minas
        rootLogger.removeHandler(logHandler)
        # ------------------------------------------------------------------------------------------------
        df = timed.statisticSummary()
        logging.info(f'=========== Timed Functions Summary ===========\n{df}')
        fig, ax = timed.mkTimedResumePlot()
        plt.tight_layout(.5)
        plt.savefig(dirr + 'timed-run.png')
        plt.close(fig)
        timed.clearTimes()
        return result, df.describe()
    def test_fake_seed200(self):
        return self.fake_seed(200)
    def test_fake_seed201(self):
        return self.fake_seed(201)
    def test_fake_seed202(self):
        return self.fake_seed(202)
# 