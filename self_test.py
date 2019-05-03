import os, queue, asyncio, time, sys, shutil, logging, csv, io
from typing import List
from copy import deepcopy

import matplotlib, numpy, yaml
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from dask.distributed import Client

import minas
from timeout import timeout
from timed import timed, mkTimedResumePlot, timedResume, statisticSummary

def setupFakeExamples(seed):
  numpy.random.seed(seed)
  attributes = numpy.random.randint(2, 40)
  examples = []
  for labelIndex in range(numpy.random.randint(2, 5)):
    mu = numpy.random.random() * 10
    sigma = numpy.random.random() * 5
    for exampleIndex in range(numpy.random.randint(200, 1000)):
      example = minas.Example()
      example.label = 'Class #' + str(labelIndex)
      example.item = []
      for i in range(attributes):
        value = numpy.random.normal(loc=mu, scale=sigma)
        example.item.append(float(value))
      examples.append(example)
  numpy.random.shuffle(examples)
  return examples

def plotExamples2D(directory, name='plotExamples2D', examples: List[minas.Example] = [], clusters: List[minas.Cluster] = []):
  fig, ax = mkPlot(examples=examples, clusters=clusters)
  # 
  # plt.show()
  if not os.path.exists(directory):
    os.makedirs(directory)
  plt.savefig(directory + name + '.png')
  plt.close(fig)

@timed
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
    x = numpy.array([cl.center[0] for cl in exs])
    y = numpy.array([cl.center[1] for cl in exs])
    scale = 200.0 * numpy.array([cl.maxDistance for cl in exs])
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
    x=numpy.array([ex.item[0] for ex in exs])
    y=numpy.array([ex.item[1] for ex in exs])
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

async def testRun(Minas, seed):
  # dirr = input()
  dirr = 'run/seeds/' + str(seed) + '/'
  if not os.path.exists(dirr):
    os.makedirs(dirr)
  rootLogger = logging.getLogger()
  logHandler = logging.FileHandler(dirr + 'run.log')
  logHandler.formatter = rootLogger.handlers[0].formatter
  rootLogger.addHandler(logHandler)
  # ------------------------------------------------------------------------------------------------
  examples = setupFakeExamples(seed)
  plotExamples2D(dirr, '0-fake_base', examples)
  # ------------------------------------------------------------------------------------------------
  resultMinas = None
  try:
    basicModel = Minas()
    training_set = examples[:int(len(examples) * .1)]
    with open(dirr + 'training_set.csv', 'w') as training_set_csv:
      for ex in training_set:
        training_set_csv.write(','.join([str(i) for i in ex.item]) + ',' + ex.label + '\n')
    plotExamples2D(dirr, '1-training_set', training_set)
    basicModel = basicModel.offline(training_set)
    logging.info(str(basicModel) + str(repr(basicModel)))
    plotExamples2D(dirr, '2-offline_clusters', [], basicModel.clusters)
    plotExamples2D(dirr, '3-offline_training', training_set, basicModel.clusters)
    plotExamples2D(dirr, '4-offline_all_data', examples, basicModel.clusters)
    # ------------------------------------------------------------------------------------------------
    testSet = examples[int(len(examples) * .1):]
    resultModel = basicModel.online([i.item for i in testSet])
    resultMinas = resultModel
  except Exception as exc:
    logging.info(exc)
    raise exc
  # ------------------------------------------------------------------------------------------------
  logging.info('aggregatin resutls')
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
        hasLabel, cluster, d = resultMinas.classify(ex)
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
  logging.info('\n\n\t=== Final Results ===\n{model}\n[seed {seed}] positive: {p}({pp:.2%}), negative: {n}({nn:.2%}), unknown: {u}({uu:.2%})\n'.format(
    model=repr(resultMinas),
    seed=seed,
    p=positiveCount, pp=positiveCount/totalExamples,
    n=negativeCount, nn=negativeCount/totalExamples,
    u=unknownCount, uu=unknownCount/totalExamples,
  ))
  plotExamples2D(dirr, '5-online_clusters', [], resultMinas.clusters if resultMinas else [])
  plotExamples2D(dirr, '6-online_resutls', results, resultMinas.clusters if resultMinas else [])
  del resultMinas
  rootLogger.removeHandler(logHandler)

def testForestCover(runName, minasInstance: minas.Minas, directory = 'run/forest-cover-type-dataset/'):
  total = 581013
  with open(directory + 'covtype.csv') as csvfile:
    reader = csv.reader(csvfile)
    # Elevation,Aspect,Slope,Horizontal_Distance_To_Hydrology,Vertical_Distance_To_Hydrology,Horizontal_Distance_To_Roadways,
    # Hillshade_9am,Hillshade_Noon,Hillshade_3pm,Horizontal_Distance_To_Fire_Points,Wilderness_Area1,Wilderness_Area2,
    # Wilderness_Area3,Wilderness_Area4,Soil_Type1,Soil_Type2,Soil_Type3,Soil_Type4,Soil_Type5,Soil_Type6,Soil_Type7,Soil_Type8,
    # Soil_Type9,Soil_Type10,Soil_Type11,Soil_Type12,Soil_Type13,Soil_Type14,Soil_Type15,Soil_Type16,Soil_Type17,Soil_Type18,
    # Soil_Type19,Soil_Type20,Soil_Type21,Soil_Type22,Soil_Type23,Soil_Type24,Soil_Type25,Soil_Type26,Soil_Type27,Soil_Type28,
    # Soil_Type29,Soil_Type30,Soil_Type31,Soil_Type32,Soil_Type33,Soil_Type34,Soil_Type35,Soil_Type36,Soil_Type37,Soil_Type38,
    # Soil_Type39,Soil_Type40,Cover_Type
    header = next(reader)

    trainingSet = []
    trainingSetPlot = []
    i = 0
    trainingSetCsvFileName = directory + 'covtype_training_set.csv'
    trainingSetCsvFile = io.StringIO()
    if not os.path.exists(trainingSetCsvFileName):
      trainingSetCsvFile = open(directory + 'covtype_training_set.csv', 'w')
    with trainingSetCsvFile as trainingSetCsv:
      trainingSetCsv.write(','.join(header) + '\n')
      for row in reader:
        sys.stdout.write('.')
        item = row[:-1]
        label = row[-1]
        trainingSetPlot.append(minas.Example(item=item[:2], label=label))
        trainingSet.append(minas.Example(label=label, item=item))
        trainingSetCsv.write(','.join(row) + '\n')
        i += 1
        if i >= total * .1:
          break
    basicModel = minasInstance.offline(trainingSet)
    basicModel.storeToFile(directory + runName + '.minas.yaml')
    del trainingSet
    logging.info(str(basicModel) + str(repr(basicModel)))
    plotExamples2D(directory + runName, '1-training_set', trainingSetPlot, [])
    plotExamples2D(directory + runName, '2-offline_clusters', [], basicModel.clusters)
    plotExamples2D(directory + runName, '3-offline_training', trainingSetPlot, basicModel.clusters)
    del trainingSetPlot
    # ------------------------------------------------------------------------------------------------
    testSet = []
    resultModel = basicModel
    with open(directory + 'covtype_test_set.csv', 'w') as test_set_csv:
      for row in reader:
        sys.stdout.write('.')
        item = row[:-1]
        label = row[-1]
        test_set_csv.write(','.join(row) + '\n')
        resultModel = basicModel.onlineProcessExample(item)
        i += 1
  # ------------------------------------------------------------------------------------------------
  logging.info('aggregatin resutls')
  results = []
  positiveCount = 0
  negativeCount = 0
  unknownCount = 0
  with open(directory + 'covtype_test_set.csv', 'r') as test_set_csv:
    with open(directory + 'covtype_test_results.csv', 'w') as testResultsCsv:
      for row in test_set_csv:
        item = row[:-1]
        label = row[-1]
        testExample = minas.Example(item=item)
        hasLabel, cluster, dist = resultModel.classify(testExample)
        if hasLabel:
          if cluster.label == label:
            testExample.label = 'Positive'
            positiveCount += 1
          else:
            testExample.label = 'Negative'
            negativeCount += 1
        else:
          testExample.label = 'Unknown'
          unknownCount += 1
        if len(results) < 1000:
          results.append(testExample)
        testResultsCsv.write(','.join(row + [testExample.label])+ '\n')
  logging.info(
    '\n\n\t=== Final Results ===\n{resultModel}\n[forest-cover-type-dataset] positive: {p}({pp:.2%}), negative: {n}({nn:.2%}), unknown: {u}({uu:.2%})\n'.format(
      model=repr(resultModel),
      p=positiveCount, pp=positiveCount/total,
      n=negativeCount, nn=negativeCount/total,
      u=unknownCount, uu=unknownCount/total,
    )
  )
  plotExamples2D(directory + runName, '5-online_clusters', [], resultModel.clusters)
  plotExamples2D(directory + runName, '6-online_resutls', results, resultModel.clusters)
  del resultModel

  # ------------------------------------------------------------------------------------------------
  df = statisticSummary()
  logging.info(f'=========== Timed Functions Summary ===========\n{df}')
  fig, ax = mkTimedResumePlot(df)
  plt.tight_layout(.5)
  plt.savefig('./run/testForestCover_timed_run.png')
  plt.close(fig)
  timedResume = dict([ (k, []) for k in timedResume.keys() ])

  return (positiveCount, negativeCount, unknownCount)

# @timeout(60*10)
def selfTest(Minas):
  with open('logging.conf.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
  logging.config.dictConfig(config)
  logging.info('Running self test')
  # ------------------------------------------------------------------------------------------------
  seed = 200
  stdout_ = sys.stdout #Keep track of the previous value.
  if os.path.exists('run/seeds'):
    shutil.rmtree('run/seeds')
  testInit = time.time_ns()
  exception = None
  while not exception and (time.time_ns() - testInit < 10):
    logging.info('Next seed: {}'.format(seed))
    asyncio.run(testRun(Minas, seed))
    # ------------------------------------------------------------------------------------------------
    seed += 1
  if exception:
    raise RuntimeError('SelfTest Fail') from exception
  logging.info('Done self test')
 
  # ------------------------------------------------------------------------------------------------
  import matplotlib, numpy
  matplotlib.use('Agg')
  import matplotlib.pyplot as plt
  from timed import mkTimedResumePlot, timedResume, statisticSummary

  df = statisticSummary()
  logging.info(f'=========== Timed Functions Summary ===========\n{df}')
  fig, ax = mkTimedResumePlot(df)
  plt.tight_layout(.5)
  plt.savefig('./run/seeds/timed-run.png')
  plt.close(fig)
  timedResume = dict([ (k, []) for k in timedResume.keys() ])

  # ------------------------------------------------------------------------------------------------
  logging.info('Test Forest Cover')
  minasInstance = Minas()
  testForestCover('basic', minasInstance)
  
  client = Client('tcp://localhost:8786')
  minasInstance = Minas(daskEnableKmeans=True, daskEnableDist=False)
  testForestCover('daskEnableKmeans', minasInstance)