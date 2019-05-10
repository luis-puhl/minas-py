import unittest
import time
import inspect
import typing

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

from minas.timed import Timed

class TimedFunctionsTest(unittest.TestCase):
    def setUp(self):
        self.tm = Timed()
    
    def tearDown(self):
        pass

    def test_resume_plot(self):
        tm = self.tm
        timed = tm.timed
        self.assertIsInstance(timed, typing.Callable)
        funcs = []
        for i in range(10):
            mu = np.random.random()
            sigma = np.random.random()
            # @timed
            def func():
                value = np.random.normal(loc=mu, scale=sigma)
                time.sleep(abs(value))
                return value
            func.__name__ = 'func_' + str(i)
            funcs.append(timed(func))
        #
        for i in range(np.random.randint(10, 100)):
            funcs[np.random.randint(0, len(funcs))]()
        #
        print(tm.timedResume)
        fig, ax = tm.mkTimedResumePlot()
        plt.show()


if __name__ == '__main__':
    unittest.main()
