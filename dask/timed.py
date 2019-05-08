import time
import inspect

import matplotlib
import matplotlib.pyplot as plt

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

class Timed():
    def __init__(self):
        self.timedResume = {}
        self.functs = []
    def timed(self, func, functionName = None):
        if functionName is None:
            functionName = func.__name__
        if functionName in self.functs:
            functionName += '_' + str(len(self.functs))
        self.timedResume[functionName] = []
        def f(*args, **kwargs):
            before = time.time_ns()
            rv = func(*args, **kwargs)
            after = time.time_ns()
            elapsed = after - before
            if elapsed:
                self.timedResume[functionName].append(elapsed)
            return rv
        return f
    def timedClass(self, ogclass):
        newFuncs = {}
        for name, fn in inspect.getmembers(ogclass):
            if not name.startswith('_') and callable(fn):
                fn = self.timed(fn, name)
                fn.__name__ = name
                newFuncs[name] = fn
        return type(ogclass.__name__ + 'Timed', (ogclass, ), newFuncs)
    def clearTimes(self):
        self.timedResume = dict( (k, []) for k in self.functs )
    def statisticSummary(self):
        records = []
        for k, v in self.timedResume.items():
            for i in v:
                records.append({'func': k, 'time': i})
        df = pd.DataFrame(records, columns=['func', 'time'])
        if len(records) == 0:
            return df
        return df.groupby('func')
    def mkTimedResumePlot(self):
        records = []
        df = pd.DataFrame(columns=[ 'functionName', 'minVal', 'maxVal', 'mean', 'std', ])
        # 
        for functionName in self.timedResume.keys():
            times = np.array(self.timedResume[functionName])
            if len(times) == 0:
                continue
            df = df.append({
                'functionName': functionName,
                'minVal': np.min(times),
                'maxVal': np.max(times),
                'mean': np.mean(times),
                'std': np.std(times),
            }, ignore_index=True)
        df = df.sort_values(by=['mean'])
        df.index = range(1 ,len(df) + 1)
        # 
        fig, ax = plt.subplots()
        width = 0.35    # the width of the bars

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
    tm = Timed()
    timed = tm.timed
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
    print(tm.timedResume)
    fig, ax = tm.mkTimedResumePlot()
    plt.show()
