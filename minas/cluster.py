import dataclasses
import typing
import time

import scipy

from .example import Example, Vector

@dataclasses.dataclass
class Cluster:
    center: Vector = dataclasses.field(repr=False)
    label: typing.Union[str, None] = None
    n: int = 0
    latest: int = 0
    timestamp: int = time.time_ns()
    lastExapleTMS: int = 0
    maxDistance: float = 0.0
    meanDistance: float = 0.0
    sumDistance: float = 0.0
    rolingVarianceSum: float = 0.0
    stdDev: float = 0.0
    temp_examples: typing.Union[list, None] = dataclasses.field(repr=False, default=None)
    distances: typing.Union[Vector, None] = dataclasses.field(repr=False, default=None)
    def __getstate__(self):
        return {
            'label': self.label,
            'center': [float(i) for i in self.center],
            'n': self.n,
            'maxDistance': self.maxDistance,
            'lastExapleTMS': self.lastExapleTMS,
        }
    def __str__(self):
        return repr(self)[:-1] + ', center=[' + ', '.join(map(lambda x: '{: .4f}'.format(x), self.center)) + '])'
    def __eq__(self, other):
        return self.timestamp == other.timestamp and self.label == other.label and self.n == other.n and (self.center == other.center).all()
    def __hash__(self):
        return self.timestamp
    def __add__(self, other):
        if isinstance(other, Example):
            self.addExample(other)
            return self
        return self
    def radius(self):
        return self.maxDistance
    def dist(self, vec):
        return scipy.spatial.distance.euclidean(self.center, vec)
    def addExample(self, other, dist=None):
        if dist is None:
            dist = self.dist(other.item)
        self.n += 1
        self.lastExapleTMS = max(other.timestamp, self.lastExapleTMS)
        self.maxDistance = max(dist, self.maxDistance)
        self.sumDistance += dist
        self.meanDistance = self.sumDistance / self.n
        self.rolingVarianceSum += (dist - self.meanDistance) ** 2
        self.stdDev = self.rolingVarianceSum ** (1/2)
        if hasattr(self, 'temp_examples') and isinstance(self.temp_examples, list):
            self.temp_examples.append((other, dist))
    def silhouette(self):
        if hasattr(self, 'temp_examples') and not isinstance(self.temp_examples, list):
            return None
        distances = []
        for ex, dist in self.temp_examples:
            if dist is None:
                dist = self.dist(ex.item)
            distances.append(dist)
        if len(distances) == 0:
            return None
        mean = sum(distances) / len(distances)
        devianceSqrSum = sum([(d - mean) **2 for d in distances])
        var = devianceSqrSum / len(distances)
        stdDevDistance = var **0.5
        # 
        silhouette = lambda a, b: (b - a) / max([a, b])
        return silhouette(dist, stdDevDistance)
