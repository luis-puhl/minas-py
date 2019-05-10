import dataclasses
import typing
import time

import numpy as np

Vector = typing.Union[list, np.ndarray, typing.Any, None]

@dataclasses.dataclass(eq=False)
class Example:
    item: Vector
    label: typing.Union[str, None] = None
    timestamp: int = time.time_ns()
    tries: int = 0
    def __getstate__(self):
        return {
            'item': [float(i) for i in self.item],
            'label': self.label,
            'timestamp': self.timestamp,
            'tries': self.tries,
        }