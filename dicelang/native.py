import math
import statistics
import functools
import operator
from numbers import Complex
from random import shuffle

import more_itertools

from typing import TypeVar, Iterable, Any
from numbers import Real, Number
T = TypeVar('T')


class _PrintQueue:
    def __init__(self, queue: list | None = None):
        self.queued = queue or []

    def _print_kernel(self, *args, sep=' ', end='\n') -> str:
        msg = sep.join(str(a) for a in args) + end
        self.queued.append(msg)
        return msg

    def print(self, *args) -> str:
        """Print an arbitrary sequence of values, separated by spaces."""
        return self._print_kernel(*args, end='')

    def print0(self, *args) -> str:
        """Print an arbitrary sequence of values with no separators."""
        return self._print_kernel(*args, sep='', end='')

    def println(self, *args) -> str:
        """Print an arbitrary sequence of values, separated by spaces, and followed by a newline."""
        return self._print_kernel(*args)

    def println0(self, *args) -> str:
        """Print an arbitrary sequence of values without separators, followed by a newline."""
        return self._print_kernel(*args, sep='')

    def flush(self) -> str:
        flushed = ''.join(self.queued)
        self.queued.clear()
        return flushed


PrintQueue = _PrintQueue()


def shuffled(iterable: Iterable[T]) -> list[T]:
    new = list(iterable)
    shuffle(new)
    return new


def stats(iterable: dict[Any, Real] | Iterable[Real]):
    items = iterable.values() if isinstance(iterable, dict) else iterable
    out = {'average': statistics.mean(items), 'minimum': min(items),
           'maximum': max(items), 'median': statistics.median(items),
           'size': len(items), 'sum': sum(items)}
    out['stddev'] = statistics.pstdev(items, out['average'])
    out['q1'] = statistics.median(x for x in items if x < out['median'])
    out['q3'] = statistics.median(x for x in items if x > out['median'])
    return out


def flatten(items: Iterable[Any]) -> list[Any]:
    return list(more_itertools.collapse(items))


def lzip(*iterables: Iterable) -> list[tuple]:
    return list(zip(*iterables))


def typeof(x: Any) -> type:
    return x.__class__


def typename(x: Any) -> str:
    return x.__class__.__name__


def magnitude(x: Number) -> Real:
    if isinstance(x, Complex):
        return abs(x)
    return math.ceil(math.log10(x))


def product(xs, start=1):
    return functools.reduce(operator.mul, xs, start)
