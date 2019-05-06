import time, _collections

timedResume = _collections.defaultdict(list)

def timed(func):
  global timedResume
  functionName = func.__name__
  if timedResume and timedResume.get(functionName, False):
    functionName += '_' + str(len(timedResume))
  timedResume[functionName] = []
  def f(*args, **kwargs):
    before = time.time_ns()
    rv = func(*args, **kwargs)
    after = time.time_ns()
    elapsed = after - before
    # elapsed = int((after - before) /100)
    if elapsed:
      timedResume[functionName].append(elapsed)
    # print('timed {f}: {s}ns'.format(f=functionName, s=elapsed))
    return rv
  return f

def clearTimes():
  global timedResume
  timedResume = dict([ (k, []) for k in timedResume.keys() ])

def statisticSummary():
  import numpy, pandas
  global timedResume
  means = []
  stds = []
  df = pandas.DataFrame(columns=[ 'functionName', 'minVal', 'maxVal', 'mean', 'std', ])
  for functionName in timedResume.keys():
    times = numpy.array(timedResume[functionName])
    if len(times) == 0:
      continue
    df = df.append({
      'functionName': functionName,
      'minVal': numpy.min(times),
      'maxVal': numpy.max(times),
      'mean': numpy.mean(times),
      'std': numpy.std(times),
    }, ignore_index=True)
  df = df.sort_values(by=['mean'])
  df.index = range(1 ,len(df) + 1)
  return df

def mkTimedResumePlot(df):
  import matplotlib, numpy, logging, pandas
  import matplotlib.pyplot as plt

  fig, ax = plt.subplots()
  width = 0.35  # the width of the bars

  for index, row in df.iterrows():
    ax.bar(index, row['mean'], width, yerr=row['std'], label=row['functionName'])

  # Add some text for labels, title and custom x-axis tick labels, etc.
  ax.set_ylabel('time (ns)')
  # ax.set_xticks(ind)
  ax.set_yscale('log')

  ax.grid(True)
  ax.legend()
  return fig, ax

if __name__ == "__main__":
  import numpy as np
  funcs = []
  for i in range(10):
    mu = np.random.random()
    sigma = np.random.random()
    # @timed
    def func():
      value = np.random.normal(loc=mu, scale=sigma)
      time.sleep(abs(value))
      return value
    func.__name__ = 'func_' + str(i)
    funcs.append(timed(func))
  #
  for i in range(np.random.randint(10, 100)):
    funcs[np.random.randint(0, len(funcs))]()
  #
  import matplotlib
  import matplotlib.pyplot as plt
  print(timedResume)
  fig, ax = mkTimedResumePlot()
  plt.show()
