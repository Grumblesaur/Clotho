from functools import reduce
from operator import add
from special import Spread
from collections.abc import Iterable
from exceptions import InvalidSubscript


def get_attr_or_item(obj, name):
    if hasattr(obj, name):
        return getattr(obj, name)
    try:
        out = obj[name]
    except (TypeError, KeyError):
        raise InvalidSubscript(f'builtin object or module has no attribute, key, or index {name!r}')
    return out


def split(vector, on):
    mid = vector.index(on)
    left, right = vector[:mid], vector[mid+1:]
    return left, right


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
