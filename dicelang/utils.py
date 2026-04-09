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
    if not v:
        return True
    prev, *rest = v
    for item in rest:
        if prev > item:
            return False
        prev = item
    return True

class Argument:
    def __init__(self, value: Any, name: str = None):
        self.value = value
        self.name = name

    def is_named(self) -> bool:
        return self.name is not None

    def __str__(self):
        if self.is_named():
            return f'{self.name}={self.value!r}'
        return f'{self.value!r}'

    def __repr__(self):
        clsname = self.__class__.__name__
        if self.is_named():
            return f'{clsname}({self.value!r}, {self.name})'
        return f'{clsname}({self.value!r})'

    def pair(self):
        return self.name, self.value

class Parameter:
    def __init__(self, name, default=Unfilled):
        self.name = name
        self.default = default

    def is_default(self):
        return self.default is not Unfilled

    def pair(self):
        return self.name, self.default

    def __str__(self):
        if self.default is Unfilled:
            return self.name
        return f'{self.name}={self.default}'

    def __repr__(self):
        d = f', {self.default!r}' if self.default is not Unfilled else ''
        return f'{self.__class__.__name__}({self.name!r}{d})'


def get_attr_or_item(obj: Any, name) -> Any:
    if isinstance(name, str) and hasattr(obj, name):
        return getattr(obj, name)
    try:
        out = obj[name]
    except (TypeError, KeyError):
        raise InvalidSubscript(f'object or module {obj} has no attribute, key, or index {name!r}')
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
