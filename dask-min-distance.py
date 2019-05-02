from dask.distributed import Client
import numpy as np

client = Client('tcp://localhost:8786')
np.random.random()

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