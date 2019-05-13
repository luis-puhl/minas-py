import unittest
import multiprocessing as mp

import testtools

from .test_minas_fake import MinasFakeExamplesTest
from .test_minas_forest import MinasForestCoverDataSetTest
from .test_minas_crafted import MinasCraftedExamplesTest
from .test_timed import TimedFunctionsTest

def runTestCase(caseClass):
    case: unittest.TestCase = caseClass()
    result = unittest.TestResult()
    case.run(result)
    return result

def runConcurrent():
    testCases = (MinasFakeExamplesTest, MinasForestCoverDataSetTest, MinasCraftedExamplesTest, TimedFunctionsTest)
    # suite = unittest.TestSuite()
    # suite.addTests(c() for c in testCases)
    # concurrent_suite = testtools.ConcurrentStreamTestSuite(lambda: ((case, None) for case in suite))
    # concurrent_suite.run(testtools.StreamResult())

    with mp.Pool() as pool:
        results = pool.map(runTestCase, testCases)
        print(results)
