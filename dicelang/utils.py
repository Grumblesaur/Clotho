import sentinel
from collections.abc import Iterable
from functools import reduce
from numbers import Number
from operator import add
from typing import Any, Sequence, TypeVar
from dicelang.exceptions import InvalidSubscript

T = TypeVar('T')
Unfilled = sentinel.create()

def is_sorted(v: Sequence[T]) -> bool:
    prev, *rest = v
    for item in rest:
        if prev > item:
            return False
        prev = item
    return True

class Parameter:
    def __init__(self, name, default=Unfilled):
        self.name = name
        self.default = default

    def is_default(self):
        return self.default is not Unfilled

    def __str__(self):
        return self.name

    def __repr__(self):
        d = f', {self.default!r}' if self.default is not Unfilled else ''
        return f'{self.__class__.__name__}({self.name!r}{d})'


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


def vector_sum(v: Iterable[Number]) -> Number:
    return reduce(add, v) if v else 0


def sign(x: int) -> int:
    return 1 if x >= 0 else -1
