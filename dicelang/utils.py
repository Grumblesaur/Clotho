from functools import reduce
from operator import add
from special import Spread
from collections.abc import Iterable


def isordered(x):
    return isinstance(x, (tuple, list))


def isvector(x):
    return not isinstance(x, (str, dict)) and isinstance(x, Iterable)


def iscontainer(x):
    return not isinstance(x, str) and isinstance(x, Iterable)


def some(x):
    return 1 if x is not None else 0


def spread(evaluated, into=None):
    new = []
    for x in evaluated:
        if isinstance(x, Spread):
            new.extend(x.items)
        else:
            new.append(x)
    return new if into is None else into(new)


def vector_sum(v):
    return reduce(add, v) if v else 0


def sign(x):
    return 1 if x >= 0 else -1
