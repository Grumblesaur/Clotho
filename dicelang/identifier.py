import math
from utils import some
from enum import Enum
from typing import Any
NotBuiltin = object()


class AccessType(Enum):
    KEY = 0
    SLICE = 1
    DOT = 2


class Accessor:
    def __init__(self, key, atype):
        self.key = key
        self.atype = atype

    @classmethod
    def keyed(cls, key):
        return cls(key, AccessType.KEY)

    @classmethod
    def sliced(cls, key):
        return cls(key, AccessType.SLICE)

    @classmethod
    def dotted(cls, key):
        return cls(key, AccessType.DOT)

    def __repr__(self):
        match self.atype:
            case AccessType.KEY:
                return f'[{self.key!r}]'
            case AccessType.DOT:
                return f'.{self.key!s}]'
        x, y, z = self.key.start, self.key.stop, self.key.step
        match int(''.join(str(some(i)) for i in (x, y, z))):
            case 7:
                return f'[{x!r}:{y!r}:{z!r}]'
            case 6:
                return f'[{x!r}:{y!r}]'
            case 5:
                return f'[{x!r}::{z!r}]'
            case 4:
                return f'[{x!r}:]'
            case 3:
                return f'[:{y!r}:{z!r}]'
            case 2:
                return f'[:{y!r}]'
            case 1:
                return f'[::{z!r}]'
            case _:
                return '[:]'


class Builtin:
    def __init__(self, obj, name, accessors):
        self.obj = obj
        self.name = name
        self.accessors = accessors

    def __repr__(self):
        name, accessors = self.accessors
        access = ''.join(repr(a) for a in accessors)
        return f'{name!s}{access}'

    def serialization(self):
        return f'{type(self).__name__}({repr(self)!r})'

    @property
    def get(self):
        if not self.accessors:
            return self.obj
        return eval(repr(self))


class Module:
    exposed: dict[str, Any] = {
        'str': str,
        'int': int,
        'float': float,
        'dict': dict,
        'tuple': tuple,
        'set': set,
        'frozenset': frozenset,
        'math': math,
        'abs': abs,
    }

    def __new__(cls, *accessors):
        name, *attrs = accessors
        if name not in cls.exposed:
            return NotBuiltin
        return Builtin(cls.exposed[name], name, attrs)


class IdentType(Enum):
    SCOPED = 0
    USER = 1
    SERVER = 2
    PUBLIC = 3


class AccessorType(Enum):
    ATTR = 0
    SLICE = 1


class Accessor:
    def __init__(self, atype, value):
        self.atype = atype
        self.value = value

    @classmethod
    def attr(cls, value):
        return cls(AccessorType.ATTR, value)

    @classmethod
    def slice(cls, value):
        return cls(AccessorType.SLICE, value)

    @property
    def args(self):
        return self.atype, self.value

    def __repr__(self):
        return f'{type(self).__name__}({self.atype!r}, {self.value!r})'

    def __str__(self):
        return f'{self.value!r}'


class Lookup:
    def __init__(self, itype, call_stack, name, *accessors):
        self.itype = itype
        self.name = name
        self.accessors = accessors
        self.call_stack = call_stack

    @classmethod
    def scoped(cls, call_stack, name, *accessors):
        return cls(IdentType.SCOPED, call_stack, name, *accessors)

    @classmethod
    def user(cls, call_stack, name, *accessors):
        return cls(IdentType.USER, call_stack, name, *accessors)

    @classmethod
    def server(cls, call_stack, name, *accessors):
        return cls(IdentType.SERVER, call_stack, name, *accessors)

    @classmethod
    def public(cls, name, call_stack):
        return cls(IdentType.PUBLIC, name, call_stack)

    def get(self):
        if (maybe_builtin := Module(self.name)) is not NotBuiltin:
            target = maybe_builtin.get
            for acc in self.accessors:
                match acc.args:
                    case (AccessorType.ATTR, x):
                        target = getattr(target, x)
                    case (AccessorType.SLICE, x):
                        target = target[x]
            return target


        # TODO: or else call_stack retrieval if SCOPED

        # TODO: or else persistence retrieval
        pass

    def put(self, value):
        # TODO: raise error if assigning to a builtin if SCOPED
        # TODO: call_stack assignment if SCOPED
        # TODO: or else persistent assignment
        pass

    def drop(self):
        # TODO: raise error if dropping a builtin if SCOPED
        # TODO: call_stack removal if SCOPED
        # TODO: or else persistent removal
        pass
