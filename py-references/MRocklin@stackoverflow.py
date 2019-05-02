from distributed.joblib import DistributedBackend

# it is important to import joblib from sklearn if we want the distributed features to work with sklearn!
from sklearn.externals.joblib import Parallel, parallel_backend, register_parallel_backend

... 

search = RandomizedSearchCV(model, param_space, cv=10, n_iter=1000, verbose=1)

register_parallel_backend('distributed', DistributedBackend)

with parallel_backend('distributed', scheduler_host='your_scheduler_host:your_port'):
        search.fit(digits.data, digits.target)