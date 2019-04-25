import os
import asyncio
import signal
from copy import deepcopy

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as matplotlib

import minas as minas

def selfTest(Minas):
  print('Running self tests')
  # ------------------------------------------------------------------------------------------------
  # setup fake examples
  np.random.seed(200)
  attributes = np.random.randint(2, 40)
  examples = []
  for labelIndex in range(np.random.randint(2, 5)):
    mu = np.random.random() * 10
    sigma = np.random.random() * 5
    for exampleIndex in range(np.random.randint(200, 1000)):
      example = minas.Example()
      example.label = 'Class #' + str(labelIndex)
      example.item = [np.random.normal(loc=mu, scale=sigma) for i in range(attributes)]
      examples.append(example)
  np.random.shuffle(examples)
  plotExamples2D('0-fake_base', examples)
  # ------------------------------------------------------------------------------------------------
  basicModel = Minas()
  # 10 %
  training_set = examples[:int(len(examples) * .1)]
  plotExamples2D('1-training_set', training_set)
  basicModel = basicModel.offline(training_set)
  #
  print(basicModel.model)
  plotExamples2D('2-offline_clusters', [], basicModel.model.clusters)
  plotExamples2D('3-offline_training', training_set, basicModel.model.clusters)
  plotExamples2D('3-offline_all_data', examples, basicModel.model.clusters)
  # ------------------------------------------------------------------------------------------------
  testSet = examples[int(len(examples) * .1):]
  np.random.shuffle(testSet)
  baseStream = (ex.item for ex in testSet)
  resultModel = basicModel.online(baseStream)
  results = []
  positiveCount = 0
  negativeCount = 0
  unknownCount = 0
  for ex in examples:
    ex = deepcopy(ex)
    hasLabel, cluster, d = resultModel.model.classify(ex)
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
  print(resultModel.model)
  print(
    'positiveCount', positiveCount,
    'negativeCount', negativeCount,
    'unknownCount', unknownCount,
  )
  plotExamples2D('5-online_clusters', [], resultModel.model.clusters)
  plotExamples2D('5-online_resutls', results, resultModel.model.clusters)

  # 
  # def signal_handler(signal, frame):
  #   loop.stop()
  #   client.close()
  #   sys.exit(0)
  # signal.signal(signal.SIGINT, signal_handler)

  # loop = asyncio.get_event_loop()
  # async def producer():

  # asyncio.ensure_future(get_reddit_top('python', client))  
  # asyncio.ensure_future(get_reddit_top('programming', client))  
  # asyncio.ensure_future(get_reddit_top('compsci', client))  
  # loop.run_forever()

def plotExamples2D(name='plotExamples2D', examples=[], clusters=[]):
  labels = [ex.label for ex in examples]
  labels.extend([ex.label for ex in clusters])
  labelSet = sorted(set(labels))

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
    # print('plotExamples2D', label, len(exs), len(x), len(y), label)
    if len(exs) > 0:
      ax.scatter(
        x=x, y=y, c=clusterColor,
        label='cluster {l} ({n})'.format(l=label, n=len(exs)),
        s=200,
        alpha=0.1,
        edgecolors=clusterColor
      )
    # 
    # color = 'C'+str(i)
    exs = [ex for ex in examples if ex.label == label]
    x=np.array([ex.item[0] for ex in exs])
    y=np.array([ex.item[1] for ex in exs])
    # label=label
    # print('plotExamples2D', label, len(exs), len(x), len(y), label)
    if len(exs) > 0:
      ax.scatter(
        x=x, y=y, c=color,
        label='{l} ({n})'.format(l=label, n=len(exs)),
        alpha=0.3,
        edgecolors=color
      )
  
  ax.legend()
  ax.grid(True)

  # plt.show()
  directory = 'plots/'
  if not os.path.exists(directory):
    os.makedirs(directory)
  plt.savefig(directory + name + '.png')

if __name__ == "__main__":
  selfTest(minas.Minas)