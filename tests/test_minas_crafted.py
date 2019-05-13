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
from .test_minas_fake import MinasFakeExamplesTest

class MinasCraftedExamplesTest(MinasFakeExamplesTest):
    def setupFakeExamples(self, seed):
        np.random.seed(seed)
        attributes = np.random.randint(2, 40)
        labels = np.random.randint(2, 5)
        count = 3000

        lbs = []
        for labelIndex in range(labels):
            attrs = []
            for attrIndex in range(attributes):
                attr = {
                    'mu': (np.random.random() + 1) * (np.random.random() - 1),
                    'sigma': np.random.random(),
                }
                attrs.append(attr)
            lbs.append(attrs)
        
        examples = []
        for k in range(count):
            labelIndex = np.random.randint(0, labels)
            item = []
            for attr in lbs[labelIndex]:
                value = attr['sigma'] * np.random.randn() + attr['mu']
                attr['mu'] += attr['sigma'] * np.random.randn()
                item.append(value)
            example = Example(item=item, label='Class #{}'.format(labelIndex))
            examples.append(example)
        # np.random.shuffle(examples)
        return examples
    
    def fake_seed(self, seed):
        dirr = 'run/crafted/' + str(seed) + '/'
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
# 