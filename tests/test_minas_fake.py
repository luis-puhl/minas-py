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
        pass
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
    
    def runSeeded(self, basicModel: MinasBase, seed):
        # dirr = input()
        dirr = 'run/seeds/' + str(seed) + '/'
        if not os.path.exists(dirr):
            os.makedirs(dirr)
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
        basicModel.offline(trainingDf)
        basicModel.storeToFile(dirr + 'minas.yaml')
        basicModel.restoreFromFile(dirr + 'minas.yaml')
        logging.info(str(basicModel) + str(basicModel))
        self.assertGreater(len(basicModel.clusters), 0, 'model must be trainded after offline call')
        
        plotExamples2D(dirr, '2-offline_clusters', [], basicModel.clusters)
        plotExamples2D(dirr, '3-offline_training', training_set, basicModel.clusters)
        plotExamples2D(dirr, '4-offline_all_data', examples, basicModel.clusters)
        # ------------------------------------------------------------------------------------------------
        testSet = examples[int(len(examples) * .1):]
        basicModel.online( i.item for i in testSet )
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
                if basicModel:
                    hasLabel, cluster, d, ex = basicModel.classify(ex)
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
        logging.info('\n\n\t=== Final Results ===\n{model}\n[seed {seed}] positive: {p}({pp:.2%}), negative: {n}({nn:.2%}), unknown: {u}({uu:.2%})\n'.format(
        model=str(basicModel),
        seed=seed,
        p=positiveCount, pp=positiveCount/totalExamples,
        n=negativeCount, nn=negativeCount/totalExamples,
        u=unknownCount, uu=unknownCount/totalExamples,
        ))
        plotExamples2D(dirr, '5-online_clusters', [], basicModel.clusters if basicModel else [])
        plotExamples2D(dirr, '6-online_resutls', results, basicModel.clusters if basicModel else [])
        del basicModel
        rootLogger.removeHandler(logHandler)

    # def test_sample(self):
    #     logging.info('Running self test')
    #     # ------------------------------------------------------------------------------------------------
    #     seed = 200
    #     stdout_ = sys.stdout #Keep track of the previous value.
    #     if os.path.exists('run/seeds'):
    #         shutil.rmtree('run/seeds')
    #     testInit = time.time_ns()
    #     timed = Timed()
    #     TimedMinasAlgorith = timed.timedClass(MinasAlgorith)
    #     CONSTS=MinasConsts()
    #     # CONSTS.k = 5
    #     # CONSTS.ndProcedureThr = 100
    #     while time.time_ns() - testInit < 10 * (10 ** 9):
    #         logging.info('Next seed: {}'.format(seed))
    #         minas = MinasBase(minasAlgorith=TimedMinasAlgorith(CONSTS=CONSTS))
    #         self.runSeeded(minas, seed)
    #         # ------------------------------------------------------------------------------------------------
    #         seed += 1
    #     logging.info('Done self test')
        
    #     # ------------------------------------------------------------------------------------------------
    #     df = timed.statisticSummary()
    #     logging.info(f'=========== Timed Functions Summary ===========\n{df}')
    #     fig, ax = timed.mkTimedResumePlot(df)
    #     plt.tight_layout(.5)
    #     plt.savefig('./run/seeds/timed-run.png')
    #     plt.close(fig)
    #     timed.clearTimes()
    
    def fake_seed(self, seed):
        dirr = 'run/seeds/' + str(seed) + '/'
        if os.path.exists(dirr):
            shutil.rmtree(dirr)
        timed = Timed()
        TimedMinasAlgorith = timed.timedClass(MinasAlgorith)
        CONSTS=MinasConsts()
        # CONSTS.k = 5
        # CONSTS.ndProcedureThr = 100
        logging.info('Next seed: {}'.format(seed))
        minas = MinasBase(minasAlgorith=TimedMinasAlgorith(CONSTS=CONSTS))
        self.runSeeded(minas, seed)
        # ------------------------------------------------------------------------------------------------
        df = timed.statisticSummary()
        logging.info(f'=========== Timed Functions Summary ===========\n{df}')
        fig, ax = timed.mkTimedResumePlot()
        plt.tight_layout(.5)
        plt.savefig(dirr + 'timed-run.png')
        plt.close(fig)
        timed.clearTimes()
    def test_fake_seed200(self):
        self.fake_seed(200)
    def test_fake_seed201(self):
        self.fake_seed(201)
    def test_fake_seed202(self):
        self.fake_seed(202)
# 