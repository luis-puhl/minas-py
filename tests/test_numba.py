import unittest

from minas.map_minas import *
from minas.map_minas_support import *

class TimedFunctionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass
    @classmethod
    def tearDownClass(cls):
        pass
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_minDistNumba(self):
        klss = sampleClasses()
        clusters = sampleClusters(klss)
        
        init = time.time_ns()
        minDist(clusters, nextRandExample(klss).item)
        print(f'minDist Python baseline  {time.time_ns() - init}')
        init = time.time_ns()
        for i in range(100):
            minDist(clusters, nextRandExample(klss).item)
        print(f'minDist Python 100x      {time.time_ns() - init}')

        
        init = time.time_ns()
        minDistNumba(clusters, nextRandExample(klss).item)
        print(f'minDistNumba cold        {time.time_ns() - init}')
        
        init = time.time_ns()
        minDistNumba(clusters, nextRandExample(klss).item)
        print(f'minDistNumba hot         {time.time_ns() - init}')
        init = time.time_ns()
        for i in range(100):
            minDistNumba(clusters, nextRandExample(klss).item)
        print(f'minDistNumba hot 100x    {time.time_ns() - init}')
    def test_Kddcup99Numba():
        from sklearn.datasets import fetch_kddcup99
        kddcup99 = fetch_kddcup99()
        total = len(kddcup99.data)
        online = 442800
        offline = 48791
        # total - online - offline

        print(kddcup99.data[0])
        kddNormalizeMap = list(range(40))
        kddNormalizeMap[1:3] = {}, {}, {}
        def kddNormalize(kddArr):
            # [0 b'tcp' b'http' b'SF' ...
            result = []
            for i, kddMap, kddEntry in zip(range(len(kddArr)), kddNormalizeMap, kddArr):
                if i == 0 or i >= 4:
                    result.append(float(kddEntry))
                    continue
                if not kddEntry in kddMap:
                    kddMap[kddEntry] = len(kddMap)
                result.append(float(kddMap[kddEntry]))
            return np.array(result)

        tenPercent = (total // 10)
        baseMapKddcup99 = []
        for data, target in zip(kddcup99.data[:tenPercent], kddcup99.target[:tenPercent]):
            baseMapKddcup99.append({'item': kddNormalize(data), 'label': str(target)})
        trainingDF = pd.DataFrame(baseMapKddcup99)
        print(trainingDF.head())
        init = time.time()
        clusters = minasOffline(trainingDF)
        print(f'minasOffline(testKddcup99Numba) => {len(clusters)}, {time.time() - init} seconds')
        labels = []
        for cl in clusters:
            if not cl.label in labels:
                print(cl)
                labels.append(cl.label)
        print('\n')

        minasOnline
        allZip = zip(map(kddNormalize, kddcup99.data[tenPercent+1:]), map(str, kddcup99.target[tenPercent+1:]))
        inputStream = ( Example(item=i, label=t) for i, t in allZip)
        init = time.time()
        for o in metaMinas(minasOnline(inputStream, clusters, minDist=minDistNumba)):
            print(o)
        print(f'metaMinas(minasOnline(testKddcup99Numba) {time.time() - init} seconds')
# 