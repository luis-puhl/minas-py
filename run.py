import time

from numba import jit
import dask.dataframe as dd

from minas.map_minas import *
from minas.map_minas_support import *

# classes = list(map(mkClass, ['zero', 'one', 'duo', 'tri']))
# clusters = [ Cluster(center=cl['mu'], label=cl['label'], n=0, maxDist=sum(cl['sigma']), latest=0) for cl in classes ]
# inputStream = loopExamplesIter()
# for kl in range(10):
#     for i, o in zip(range(10), metaMinas(minasOnline(inputStream, clusters))):
#         print(o)
#     newClass = mkClass(f'New {kl}')
#     print(newClass)
#     classes.append(newClass)
#     inputStream.send(classes)
# print('done')

zipToMap = lambda x: {'item': x[0], 'label': str(x[1])}

def testCovtype():
    from sklearn.datasets import fetch_covtype
    covtype = fetch_covtype()
    total = len(covtype.data)

    onePercent = int(total*0.01)
    baseMap = map(zipToMap, zip(covtype.data[:onePercent], covtype.target[:onePercent]))
    onPercentDataFrame = pd.DataFrame(baseMap)

    clusters = minasOffline(onPercentDataFrame)
    print(len(clusters))

    fivePercent = int(total*0.05)
    fivePercentZip = zip(covtype.data[onePercent+1:fivePercent], map(str, covtype.target[onePercent+1:fivePercent]))
    inputStream = ( Example(item=i, label=t) for i, t in fivePercentZip)
    for o in metaMinas(minasOnline(inputStream, clusters)):
        print(o)

def testKddcup99():
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
        return result

    tenPercent = (total // 10)
    baseMapKddcup99 = []
    for data, target in zip(kddcup99.data[:tenPercent], kddcup99.target[:tenPercent]):
        baseMapKddcup99.append({'item': kddNormalize(data), 'label': str(target)})
    trainingDF = pd.DataFrame(baseMapKddcup99)
    print(trainingDF.head())
    init = time.time()
    clusters = minasOffline(trainingDF)
    print('minasOffline(onPercentDataFrame)', len(clusters), time.time() - init, 'seconds')
    labels = []
    for cl in clusters:
        if not cl.label in labels:
            print(cl)
            labels.append(cl.label)
    print('\n')
    """
        $ python run.py
        [0 b'tcp' b'http' b'SF' 181 5450 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 8 8 0.0
        0.0 0.0 0.0 1.0 0.0 0.0 9 9 1.0 0.0 0.11 0.0 0.0 0.0 0.0 0.0]
                                                        item       label
        0  [0.0, 0.0, 0.0, 0.0, 181.0, 5450.0, 0.0, 0.0, ...  b'normal.'
        1  [0.0, 0.0, 0.0, 0.0, 239.0, 486.0, 0.0, 0.0, 0...  b'normal.'
        2  [0.0, 0.0, 0.0, 0.0, 235.0, 1337.0, 0.0, 0.0, ...  b'normal.'
        3  [0.0, 0.0, 0.0, 0.0, 219.0, 1337.0, 0.0, 0.0, ...  b'normal.'
        4  [0.0, 0.0, 0.0, 0.0, 217.0, 2032.0, 0.0, 0.0, ...  b'normal.'
        C:\dev\minas-py\venv\lib\site-packages\sklearn\cluster\k_means_.py:971: ConvergenceWarning: Number of distinct clusters (30) found smaller than n_clusters (33). Possibly due to duplicate points in X.
        return_n_iter=True)
        C:\dev\minas-py\venv\lib\site-packages\sklearn\cluster\k_means_.py:971: ConvergenceWarning: Number of distinct clusters (2) found smaller than n_clusters (33). Possibly due to duplicate points in X.
        return_n_iter=True)
        C:\dev\minas-py\venv\lib\site-packages\sklearn\cluster\k_means_.py:971: ConvergenceWarning: Number of distinct clusters (19) found smaller than n_clusters (33). Possibly due to duplicate points in X.
        return_n_iter=True)
        C:\dev\minas-py\venv\lib\site-packages\sklearn\cluster\k_means_.py:971: ConvergenceWarning: Number of distinct clusters (29) found smaller than n_clusters (31). Possibly due to duplicate points in X.
        return_n_iter=True)
        minasOffline(onPercentDataFrame) 556 47.8538875579834 seconds
        Extention b'normal.'
        Extention b'normal.'
        Extention b'smurf.'
        Extention b'normal.'
        done
        {'known': 405538, 'unknown': 50409, 'cleanup': 4446, 'fallback': 0, 'recurenceDetection': 1670, 'recurence': 11141, 'noveltyDetection': 554}
        metaMinas(minasOnline(inputStream, clusters)) 2485.6704313755035 seconds
    """

    allZip = zip(map(kddNormalize, kddcup99.data[tenPercent+1:]), map(str, kddcup99.target[tenPercent+1:]))
    inputStream = ( Example(item=i, label=t) for i, t in allZip)
    init = time.time()
    for o in metaMinas(minasOnline(inputStream, clusters)):
        print(o)
    print('metaMinas(minasOnline(inputStream, clusters))', time.time() - init, 'seconds')


def testKddcup99Numba():
    @jit(nopython=True)
    def minDist(clusters, item):
        dists = map(lambda cl: (sum((cl['center'] - item) ** 2) ** (1/2), cl['id']), clusters)
        d, clId = min(dists, key=lambda x: x[0])
        return d, clId
    def minDistNumba(clusters, item):
        centers = [ {'center': cl.center, 'id': id(cl)} for cl in clusters ]
        d, clId = minDist(centers, item)
        for cl in clusters:
            if id(cl) == clId:
                return d, cl
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
    print('minasOffline(onPercentDataFrame)', len(clusters), time.time() - init, 'seconds')
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
    print('Numba jit minDist', time.time() - init, 'seconds')

testKddcup99()