import os

import matplotlib
import numpy as np
import yaml
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from dask.distributed import Client

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

def plotExamples2D(directory, name='plotExamples2D', examples = [], clusters = []):
    fig, ax = mkPlot(examples=examples, clusters=clusters)
    # 
    # plt.show()
    if not os.path.exists(directory):
        os.makedirs(directory)
    plt.savefig(directory + name + '.png')
    plt.close(fig)
