from collections.abc import Iterable
from functools import reduce
from numbers import Number
from operator import add
from typing import Any, Sequence, TypeVar
from dicelang.exceptions import InvalidSubscript
from dicelang.special import Spread

T = TypeVar('T')


class Parameter:
    def __init__(self, name, starred=False):
        self.name = name
        self.starred = starred

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'{self.__class__.__name__}({self.name!r}, {self.starred!r})'


def get_attr_or_item(obj: Any, name: str) -> Any:
    if hasattr(obj, name):
        return getattr(obj, name)
    try:
        out = obj[name]
    except (TypeError, KeyError):
        raise InvalidSubscript(f'builtin object {obj} or module has no attribute, key, or index {name!r}')
    return out


def split(vector: Sequence[Any], on: Any) -> tuple[Sequence[Any], Sequence[Any]]:
    mid = vector.index(on)
    left, right = vector[:mid], vector[mid+1:]
    return left, right


def isordered(x: Any) -> bool:
    return isinstance(x, (tuple, list))


def isvector(x: Any) -> bool:
    return not isinstance(x, (str, dict)) and isinstance(x, Iterable)


def iscontainer(x: Any) -> bool:
    return not isinstance(x, str) and isinstance(x, Iterable)


def some(x: Any) -> int:
    return 1 if x is not None else 0


def spread(evaluated: Iterable[T], into=None) -> list[T] | Any:
    new: list[T] = []
    for x in evaluated:
        if isinstance(x, Spread):
            new.extend(x.items)
        else:
            new.append(x)
    return new if into is None else into(new)


def vector_sum(v: Iterable[Number]) -> Number:
    return reduce(add, v) if v else 0


def sign(x: int) -> int:
    return 1 if x >= 0 else -1
