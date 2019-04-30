import os, asyncio, signal, time, sys, shutil
from copy import deepcopy

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as matplotlib
from dask.distributed import Client

import minas as minas

def selfTest(Minas):
  print('Running self tests')
  # ------------------------------------------------------------------------------------------------
  seed = 200
  stdout_ = sys.stdout #Keep track of the previous value.
  if os.path.exists('run'):
    shutil.rmtree('run')
  testInit = time.time()
  # run for 15 seconds
  client = Client('tcp://localhost:8786')
  while time.time() - testInit < 15:
    dirr = 'run/seed_' + str(seed) + '/'
    if not os.path.exists(dirr):
      os.makedirs(dirr)
    with Logger(dirr + 'run.log') as log:
      # ------------------------------------------------------------------------------------------------
      examples = setupFakeExamples(seed)
      plotExamples2D(dirr, '0-fake_base', examples)
      # ------------------------------------------------------------------------------------------------
      resultMinas = None
      try:
        resultMinas = runMinas(Minas, examples, dirr)
      except:
        e = sys.exc_info()
        print('Exception on Minas\t{e}\n'.format(e=e))
        raise
      # ------------------------------------------------------------------------------------------------
      results = []
      positiveCount = 0
      negativeCount = 0
      unknownCount = 0
      totalExamples = len(examples)
      with open(dirr + 'examples.csv', 'w') as examplesCsv:
        for ex in examples:
          ex = deepcopy(ex)
          hasLabel, cluster, d = None, None, None
          if resultMinas:
            hasLabel, cluster, d = resultMinas.model.classify(ex)
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
      if resultMinas:
        print(resultMinas.model)
      print('\n=== Final Results ===\n{model}\n\n{results}'.format(
        model=str(resultMinas.model if resultMinas else ''),
        results='positive: {p}({pp:.2%}), negative: {n}({nn:.2%}), unknown: {u}({uu:.2%}), '.format(
          p=positiveCount, pp=positiveCount/totalExamples,
          n=negativeCount, nn=negativeCount/totalExamples,
          u=unknownCount, uu=unknownCount/totalExamples,
        )
      ))
      plotExamples2D(dirr, '5-online_clusters', [], resultMinas.model.clusters if resultMinas else [])
      plotExamples2D(dirr, '6-online_resutls', results, resultMinas.model.clusters if resultMinas else [])
      # run once?
      # break
    # ------------------------------------------------------------------------------------------------
    seed += 1

def setupFakeExamples(seed):
  np.random.seed(seed)
  attributes = np.random.randint(2, 40)
  examples = []
  for labelIndex in range(np.random.randint(2, 5)):
    mu = np.random.random() * 10
    sigma = np.random.random() * 5
    for exampleIndex in range(np.random.randint(200, 1000)):
      example = minas.Example()
      example.label = 'Class #' + str(labelIndex)
      example.item = []
      for i in range(attributes):
        value = np.random.normal(loc=mu, scale=sigma)
        example.item.append(float(value))
      examples.append(example)
  np.random.shuffle(examples)
  return examples

def runMinas(Minas, examples, dirr):
  basicModel = Minas()
  training_set = examples[:int(len(examples) * .1)]
  with open(dirr + 'training_set.csv', 'w') as training_set_csv:
    for ex in training_set:
      training_set_csv.write(','.join([str(i) for i in ex.item]) + ',' + ex.label + '\n')
  plotExamples2D(dirr, '1-training_set', training_set)
  basicModel = basicModel.offline(training_set)
  print(str(basicModel.model))
  plotExamples2D(dirr, '2-offline_clusters', [], basicModel.model.clusters)
  plotExamples2D(dirr, '3-offline_training', training_set, basicModel.model.clusters)
  plotExamples2D(dirr, '4-offline_all_data', examples, basicModel.model.clusters)
  # ------------------------------------------------------------------------------------------------
  testSet = examples[int(len(examples) * .1):]
  baseStream = (ex.item for ex in testSet)
  resultModel = basicModel.online(baseStream)
  return resultModel

def plotExamples2D(directory, name='plotExamples2D', examples=[], clusters=[]):
  fig, ax = mkPlot(examples=examples, clusters=clusters)
  # 
  # plt.show()
  if not os.path.exists(directory):
    os.makedirs(directory)
  plt.savefig(directory + name + '.png')
  plt.close(fig)

def mkPlot(examples=[], clusters=[]):
  labels = [ex.label for ex in examples]
  labels.extend([ex.label for ex in clusters])
  labelSet = sorted(set(labels))
  # 
  fig, ax = plt.subplots()
  for i, label in enumerate(labelSet):
    color = 'C'+str(i)
    hsv = matplotlib.colors.rgb_to_hsv(matplotlib.colors.to_rgb(color))
    hsv[2] = 0.7
    clusterColor = matplotlib.colors.to_hex(matplotlib.colors.hsv_to_rgb(hsv))
    exs = [cl for cl in clusters if cl.label == label]
    x = np.array([cl.center[0] for cl in exs])
    y = np.array([cl.center[1] for cl in exs])
    scale = 200.0 * np.array([cl.maxDistance for cl in exs])
    if len(exs) > 0:
      ax.scatter(
        x=x, y=y, c=clusterColor,
        label='cluster {l} ({n})'.format(l=label, n=len(exs)),
        s=200,
        alpha=0.1,
        edgecolors=clusterColor
      )
    # 
    exs = [ex for ex in examples if ex.label == label]
    x=np.array([ex.item[0] for ex in exs])
    y=np.array([ex.item[1] for ex in exs])
    if len(exs) > 0:
      ax.scatter(
        x=x, y=y, c=color,
        label='{l} ({n})'.format(l=label, n=len(exs)),
        alpha=0.3,
        edgecolors=color
      )
  # 
  ax.legend()
  ax.grid(True)
  return fig, ax

class Logger(object):
  __slots__ = ['fileName', 'terminal', 'log']
  def __init__(self, fileName):
    self.terminal = sys.stdout
    self.fileName = fileName
  def __enter__(self):
    self.log = open(self.fileName, "a")
    return self
  def __exit__(self, exc_type, exc_value, traceback):
    pass
  def write(self, message):
    self.terminal.write(message)
    self.log.write(message)

  def flush(self):
    #this flush method is needed for python 3 compatibility.
    #this handles the flush command by doing nothing.
    #you might want to specify some extra behavior here.
    pass

if __name__ == "__main__":
  selfTest(minas.Minas)