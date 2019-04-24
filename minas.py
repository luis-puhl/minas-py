import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sklearn as sk
from sklearn.cluster import KMeans

class Example:
  label = None
  item = []

class Model:
  k = 100
  clusters = []
  radiusFactor = 1.1
  noveltyThr = 100
  lastExapleTMS = 0
  # -------- actions Thresholds ------------
  #ExND
  ndProcedureThr = 2000
  def ndProcedureThrFn(self):
    return self.representationThr * self.k
  #ExClu
  representationThr = 3
  def representationThrFn(self):
    return len(self.unknownBuffer) / self.k
  # Window size to forget outdated data
  forgetThr = 1000
  def forgetThrFn(self):
    return 2 * self.ndProcedureThr

class Cluster:
  center = []
  radius = 0
  label = ''
  counter = 0
  # statistic summary
  n = 0
  mean = []
  stdDev = 0
  max = []
  min = []

class Minas(Model):
  model = None
  def __init__(self, model=Model()):
    self.model = model
  
  """
    Require:
      k: number of micro-clusters,
      alg: clustering algorithm,
      S: Training Set
    
    Model ← ∅
    for all (class Ci in S) do
      ModelTmp ← Clustering(SClass=Ci, k, alg)
      for all (micro-cluster micro in ModelTmp) do
        micro.label ← Ci ;
      end for
      Model ← Model ∪ ModelTmp;
    end for
    return Model
  """
  def offline(self, training_set=[]):
    assert len(training_set) > 0
    # training_set = Example[]
    model = Model()
    training_set.sort(key=lambda x: x.label)
    current_label = training_set[0].label
    current_examples = []
    for example in training_set:
      if current_label != example.label:
        clusters = self.clustering(current_examples)
        for cluster in clusters:
          cluster.label = current_label
        self.clusters.extend(clusters)
        current_examples = []
        current_label = example.label
      current_examples.append(example)
    return self
  
  """
    Require:
      Model: decision model from initial training phase,
      DS: data stream,
      T: threshold,
      NumExamples: minimal number of examples to execute a ND procedure,
      windowsize: size of a data window,
      alg: clustering algorithm
    
    ShortMem ← ∅
    SleepMem ← ∅
    
    for all (example ex in DS) do
      (Dist, micro) ← closer-micro(ex,Model)
      if (Dist ≤ radius(micro) then
        ex.class ← micro.label
        update-micro(micro,ex)
      else
        ex.class ← unknown
        ShortMem ← ShortMem ∪ ex
        if (|ShortMem| ≥ NumExamples) then
          Model ← novelty-detection(Model, ShortMem, SleepMem, T, alg)
        end if
      end if
      CurrentTime ← ex.time
      if (CurrentTime mod windowSize == 0) then
        Model ← move-sleepMem(Model, SleepMem, CurrentTime, windowSize)
        ShortMem ← remove-oldExamples(ShortMem, windowsize)
      end if
    end for
  """
  def online(self, k, training_set):
    pass

  """
    Require:
      Model: current decision model,
      ShortMem: short-term memory,
      SleepMem: sleep memory,
      T: threshold,
      alg: clustering algorithm
    
    ModelTmp ← Clustering(ShortMem, k, alg)
    for all (micro-grupo micro in ModelTemp) do
      if ValidationCriterion(micro) then
        (Dist, microM) ← closest-micro(micro,Model)
        if Dist ≤ T then
          micro.label ← microM.label
        else
          (Dist, microS) ← closest-micro(micro,SleepMem)
          if Dist ≤ T then
            micro.label ← microS.label
          else
            micro.label ← new label
          end if
        end if
        Model ← Model ∪ micro
      end if
    end for
    return Model
  """
  def noveltyDetection(self, parameter_list):
    pass

  def clustering(self, examples):
    assert len(examples) > 0
    #
    # Data = {
    #   'x': [25,34,22,27,33,33,31,22,35,34,67,54,57,43,50,57,59,52,65,47,49,48,35,33,44,45,38,43,51,46],
    #   'y': [79,51,53,78,59,74,73,57,69,75,51,32,40,47,53,36,35,58,59,50,25,20,14,12,20,5,29,27,8,7]
    # }
    df = pd.DataFrame(data=[ex.item for ex in examples])
    
    n_samples = len(examples)
    n_clusters = self.k
    if n_samples < n_clusters:
      n_clusters = int(n_samples / 10)
    print(n_samples, n_clusters)
    assert n_samples >= n_clusters
    kmeans = KMeans(n_clusters=n_clusters).fit(df)
    centroids = kmeans.cluster_centers_
    print(centroids, kmeans.inertia_, kmeans.labels_)

    plt.scatter(df[0], df[1], c= kmeans.labels_.astype(float), s=50, alpha=0.5)
    plt.scatter(centroids[:, 0], centroids[:, 1], c='red', s=50)
    plt.show()

    clusters = []
    for centroid in kmeans.cluster_centers_:
      c = Cluster()
      c.center = centroid
      clusters.append(c)

    return clusters

def selfTest():
  print('Running self tests')
  # setup fake examples
  attributes = np.random.randint(2, 40)
  examples = []
  for labelIndex in range(np.random.randint(2, 5)):
      mu = np.random.random() * 10
      sigma = np.random.random() * 5
      for exampleIndex in range(np.random.randint(200, 1000)):
          example = Example()
          example.index = labelIndex
          example.label = 'Class #' + str(labelIndex)
          example.item = [np.random.normal(loc=mu, scale=sigma) for i in range(attributes)]
          examples.append(example)
  np.random.shuffle(examples)
  plotExamples2D(examples)
  #
  minas = Minas()
  minas.offline(examples[:int(len(examples) * .1)])

def plotExamples2D(examples):
  fig, ax = plt.subplots()
  for i in set([ex.index for ex in examples]):
      exs = [ex for ex in examples if ex.index == i]
      x=np.array([ex.item[0] for ex in exs])
      y=np.array([ex.item[1] for ex in exs])
      label=[ex.label for ex in examples if ex.index == i][0]
      print(i, len(exs), len(x), len(y), label)
      ax.scatter(x=x, y=y, label=label)

  ax.legend()
  ax.grid(True)

  plt.show()

if __name__ == "__main__":
  selfTest()