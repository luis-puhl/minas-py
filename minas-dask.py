import logging, scipy, dask, pandas, numpy, time, typing
import dask.dataframe as ddf
import dask.distributed as dask_distributed
from sklearn.cluster import KMeans
from sklearn.externals import joblib

import minas
import timed

class MinasDask(minas.Minas):
  @timed.timed
  def closestCluster(vec, clusters):
    """Returns the nearest cluster and its distance (nearCl, dist)"""
    dist = float("inf")
    nearCl = None
    for cl in clusters:
      d = scipy.spatial.distance.euclidean(cl.center, vec)
      if d < dist:
        dist = d
        nearCl = cl
    return nearCl, dist
  
  @timed.timed
  def clustering(self, examples):
    n_samples = len(examples)
    n_clusters = min(self.k, int(n_samples / (3 * self.representationThr)))
    assert n_samples >= n_clusters
    df = pandas.DataFrame(data=[ex.item for ex in examples])
    kmeans = KMeans(n_clusters=n_clusters)
    # with joblib.parallel_backend('dask'):
    #   kmeans.fit(df)
    kmeans.fit(df)

    clusters = [minas.Cluster(center=centroid) for centroid in kmeans.cluster_centers_]
    # Add examples to its cluster
    for ex in examples:
      nearCl, dist = self.closestCluster(ex.item, clusters)
      nearCl.addExample(ex)
    return clusters

  @timed.timed
  def offline(self, training_set):
    if hasattr(training_set, '__len__') and len(training_set) <= 0:
      raise Exception('offline training set must have len > 0')
    self.clusters = []
    df = pandas.DataFrame(data=[{'item': ex.item, 'label': ex.label} for ex in training_set])
    # df = ddf.from_pandas(df, chunksize=self.k)
    # 
    def addLabelsAndValidate(label, clusters):
      for cluster in clusters:
        isRepresentative = cluster.n > self.representationThr
        if isRepresentative:
          cluster.label = label
          return cluster
    for group, label in df.groupby('label'):
      clustersDelayed = dask.delayed(self.clustering)(group)
      validClustersDelayed = dask.delayed(addLabelsAndValidate)(label, clustersDelayed)
      self.clusters.append(validClustersDelayed)
    self.clusters = self.clusters.compute()
    self.ndProcedureThr = len(training_set)
    logging.info('[offline end]')
    # store self to a file
    return self

  @timed.timed
  def onlineProcessExample(self, item):
    example = minas.Example(item=item)
    self.globalCount += 1
    self.lastExapleTMS = example.timestamp
    cluster, dist = self.closestCluster(example.item)
    example.tries += 1
    isClassified = dist <= (self.radiusFactor * cluster.radius())
    if isClassified:
      example.label = cluster.label
      cluster.addExample(example)
      self.counter += 1
    else:
      # None is unknown class
      self.unknownBuffer.append(example)
    #
    if len(self.unknownBuffer) > self.ndProcedureThr:
      self.bufferFull()
    return example, isClassified, cluster, dist

def selfTest():
  client = dask_distributed.Client('tcp://localhost:8786')
  instance = MinasDask()
  # 
  numpy.random.seed(201)
  def mkStream(classes):
    while True:
      cl = classes[numpy.random.randint(0, len(classes))]
      msg = yield minas.Example(
        label = cl['label'],
        item = [float(numpy.random.normal(loc=cl['mu'], scale=cl['sigma'])) for i in range(40)],
      )
  stream = mkStream([{
    'label': 'Class #' + str(i),
    'mu': numpy.random.random() * 10,
    'sigma': numpy.random.random() * 5,
  } for i in range(numpy.random.randint(2, 5))])
  # 
  i = 0
  examples = []
  def limit(stream, limit):
    for target_list in range(limit):
      yield next(stream)
  start = time.time_ns()
  examples = client.scatter(limit(stream, 10000))
  future = client.submit(instance.offline, examples)
  future.compute()
  elapsed = time.time_ns() - start
  print(f'offinle of {i} took {elapsed}ns ({i/elapsed} i/ns)')
  exit()
  # 
  unk = 0
  pos = 0
  neg = 0
  start = time.time_ns()
  for ex in stream:
    example, isClassified, cluster, dist = instance.onlineProcessExample(ex.item)
    if not isClassified:
      unk += 1
    else:
      if example.label == ex.label:
        pos += 1
      else:
        neg += 1
    i += 1
    if i > 10000 * 10:
      break
  elapsed = time.time_ns() - start
  print(f'online of {i} took {elapsed}ns ({i/elapsed} i/ns)')
  print(f'pos {pos} ({int( (pos/i)*1000 )}, neg {neg} ({int( (neg/i)*1000 )}, unk {unk} ({int( (unk/i)*1000 )}')

if __name__ == "__main__":
  try:
    selfTest()
  except KeyboardInterrupt as ex:
    print('KeyboardInterrupt')
    exit()