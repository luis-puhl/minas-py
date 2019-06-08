import dataclasses
import typing
import time

import numpy as np

Vector = typing.Union[list, np.ndarray, typing.Any, None]

@dataclasses.dataclass(eq=False)
class Example:
    item: Vector = dataclasses.field(repr=False)
    label: typing.Union[str, None] = None
    timestamp: int = time.time_ns()
    tries: int = 0
    n: int = 0
    def __getstate__(self):
        return {
            'item': [float(i) for i in self.item],
            'label': self.label,
            'timestamp': self.timestamp,
            'tries': self.tries,
            'n': self.n,
        }
    def __str__(self):
        return repr(self)[:-1] + ', item=[' + ', '.join(map(lambda x: '{: .4f}'.format(x), self.item)) + '])'