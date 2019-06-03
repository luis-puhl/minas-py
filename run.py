import time

from numba import jit
import dask.dataframe as dd
from dask.distributed import Client

from minas.map_minas import *
from minas.map_minas_support import *

zipToMap = lambda x: {'item': x[0], 'label': str(x[1])}

daskClient = Client('192.168.15.12:8786')
def clusteringDask(unknownBuffer, label=None, MAX_K_CLUSTERS=100, REPR_TRESHOLD=20):
    df = pd.DataFrame(unknownBuffer).drop_duplicates()
    if len(df) == 0:
        return []
    n_clusters = min(MAX_K_CLUSTERS, len(unknownBuffer) // ( 3 * REPR_TRESHOLD))
    if n_clusters == 0:
        n_clusters = len(unknownBuffer)
    # ddf = dd.from_pandas(df, npartitions=8)
    # daskClient.scatter(ddf, broadcast=True)
    with joblib.parallel_backend('dask'):
        kmeans = KMeans(n_clusters=n_clusters)
        kmeans.fit(df)
    newClusters = [Cluster(center=centroid, label=label, n=0, maxDistance=0, latest=0) for centroid in kmeans.cluster_centers_]
    return newClusters

def testSamples():
    np.random.seed(300)
    classes = list(map(mkClass, ['zero', 'one', 'duo', 'tri']))
    clusters = sampleClusters(classes)
    inputStream = loopExamplesIter(classes)
    
    init = time.time()
    for kl in range(10):
        for i, o in zip(range(1000), minasOnline(inputStream, clusters)):
            pass
            # print(o)
        newClass = mkClass(f'New {kl}')
        print(newClass)
        classes.append(newClass)
        inputStream.send(classes)
    print(f'minasOnline testSamples {time.time() - init} seconds')
    
    sumary = dict(
        clusteringDask=[],
        testSamples=[],
        minDistNumba=[],
    )
    for iter_ in range(100):
        init = time.time()
        for i, o in zip(range(4428), minasOnline(inputStream, clusters, clustering=clusteringDask)):
            pass
        sumary['clusteringDask'].append(time.time() - init)
    
        init = time.time()
        for i, o in zip(range(4428), minasOnline(inputStream, clusters)):
            pass
        sumary['testSamples'].append(time.time() - init)
    
        init = time.time()
        for i, o in zip(range(4428), minasOnline(inputStream, clusters, minDist=minDistNumba)):
            pass
        sumary['minDistNumba'].append(time.time() - init)
    for k, v in sumary.items():
        print(f'{k}=>\t{sum(v)}')

def testCovtype():
    from sklearn.datasets import fetch_covtype
    covtype = fetch_covtype()
    total = len(covtype.data)

    onePercent = int(total*0.01)
    baseMap = map(zipToMap, zip(covtype.data[:onePercent], covtype.target[:onePercent]))
    onPercentDataFrame = pd.DataFrame(baseMap)

    init = time.time()
    clusters = minasOffline(onPercentDataFrame)
    print(f'minasOffline(testCovtype) => {len(clusters)}, {time.time() - init} seconds')
    print(len(clusters))

    fivePercent = int(total*0.05)
    fivePercentZip = zip(covtype.data[onePercent+1:fivePercent], map(str, covtype.target[onePercent+1:fivePercent]))
    inputStream = ( Example(item=i, label=t) for i, t in fivePercentZip)
    init = time.time()
    for o in metaMinas(minasOnline(inputStream, clusters)):
        print(o)
    print(f'metaMinas(minasOnline(testCovtype) {time.time() - init} seconds')

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
    clusters = minasOffline(trainingDF, clustering=clusteringDask)
    print(f'minasOffline(testKddcup99) => {len(clusters)}, {time.time() - init} seconds')
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
    for o in metaMinas(minasOnline(inputStream, clusters, clustering=clusteringDask)):
        print(o)
    print(f'metaMinas(minasOnline(testKddcup99) {time.time() - init} seconds')

testSamples()
testKddcup99()