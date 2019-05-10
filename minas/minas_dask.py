import time
import os
import typing
import dataclasses

import yaml
import pandas as pd
import numpy as np
from sklearn.externals import joblib
from sklearn.cluster import KMeans
import dask
from dask.distributed import Client

from .example import Example, Vector
from .cluster import Cluster
from .minas_algo import MinasAlgorith, ClusterList, ExampleList
from .minas_base import MinasBase

@dataclasses.dataclass
class MinasAlgorithJoblib(MinasAlgorith):
    def clustering(self, examples: typing.List[Vector], label: str = None) -> ClusterList:
        n_clusters = min(self.CONSTS.k, int(len(examples) / (3 * self.CONSTS.representationThr)))
        kmeans = KMeans( n_clusters=n_clusters, n_jobs=-1 )
        kmeans.fit(examples)
        return [Cluster(center=centroid, label=label) for centroid in kmeans.cluster_centers_]

@dataclasses.dataclass
class MinasAlgorithDaskKmeans(MinasAlgorith):
    def clustering(self, examples: typing.List[Vector], label: str = None) -> ClusterList:
        n_clusters = min(self.CONSTS.k, int(len(examples) / (3 * self.CONSTS.representationThr)))
        kmeans = KMeans( n_clusters=n_clusters )
        with joblib.parallel_backend('dask'):
            kmeans.fit(examples)
        return [Cluster(center=centroid, label=label) for centroid in kmeans.cluster_centers_]

@dataclasses.dataclass
class MinasAlgorithDaskKmeansScatter(MinasAlgorith):
    def clustering(self, examples: typing.List[Vector], label: str = None) -> ClusterList:
        n_clusters = min(self.CONSTS.k, int(len(examples) / (3 * self.CONSTS.representationThr)))
        kmeans = KMeans( n_clusters=n_clusters )
        with joblib.parallel_backend('dask', scatter=[examples]):
            kmeans.fit(examples)
        return [Cluster(center=centroid, label=label) for centroid in kmeans.cluster_centers_]

@dataclasses.dataclass
class MinasAlgorithDask(MinasAlgorith):
    def clustering(self, examples: typing.List[Vector], label: str = None) -> ClusterList:
        n_clusters = min(self.CONSTS.k, int(len(examples) / (3 * self.CONSTS.representationThr)))
        kmeans = KMeans( n_clusters=n_clusters )
        with joblib.parallel_backend('dask'):
            kmeans.fit(examples)
        return [Cluster(center=centroid, label=label) for centroid in kmeans.cluster_centers_]
    @dask.delayed
    def trainGroup(self, group, label: str = None):
        clusters = self.clustering(group, label)
        for ex in group:
            dist, nearCl = self.closestCluster(ex, clusters)
            nearCl += Example(ex)
        return [cluster for cluster in clusters if cluster.n > self.CONSTS.representationThr]
    def training(self, examplesDf, daskClient: Client = None):
        clusters = []
        groupSize = self.CONSTS.k * self.CONSTS.representationThr
        for label, group in examplesDf.groupby('label'):
            for chunk in range(0, len(group), groupSize):
                subgroup = group[chunk:chunk + groupSize]
                subgroupDf = pd.DataFrame(iter(subgroup['item']))
                if daskClient:
                    daskClient.scatter(subgroupDf)
                clusters += self.trainGroup(subgroupDf, label)
        return clusters

@dataclasses.dataclass
class MinasDask(MinasBase):
    minasAlgorith: MinasAlgorith = MinasAlgorithDask()
    daskClient: typing.Union[Client, None] = None
    def offline(self, examplesDf):
        self.clusters = self.minasAlgorith.training(examplesDf, daskClient=self.daskClient).compute()
        self.sleepClusters = []
        self.unknownBuffer = []
#
