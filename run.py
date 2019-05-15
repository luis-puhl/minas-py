import time
from minas.map_minas import *

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

from sklearn.datasets import fetch_covtype
covtype = fetch_covtype()
total = len(covtype.data)

zipToMap = lambda x: {'item': x[0], 'label': str(x[1])}
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

from sklearn.datasets import fetch_covtype
covtype = fetch_covtype()
total = len(covtype.data)

zipToMap = lambda x: {'item': x[0], 'label': str(x[1])}
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
    total - online - offline

    def kddNormalize(kddArr):
        # [0 b'tcp' b'http' b'SF' ...
        kddArr
    tenPercent = (total // 10)
    baseMapKddcup99 = map(zipToMap, zip(kddcup99.data[:tenPercent], kddcup99.target[:tenPercent]))
    init = time.time()
    clusters = minasOffline(pd.DataFrame(baseMapKddcup99))
    print('minasOffline(onPercentDataFrame)', len(clusters), time.time() - init, 'seconds')

    allZip = zip(covtype.data[tenPercent+1:], map(str, covtype.target[tenPercent+1:]))
    inputStream = ( Example(item=i, label=t) for i, t in allZip)
    init = time.time()
    for o in metaMinas(minasOnline(inputStream, clusters)):
        print(o)
    print('metaMinas(minasOnline(inputStream, clusters))', time.time() - init, 'seconds')

testKddcup99()