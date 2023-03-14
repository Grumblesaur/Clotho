import math
import copy
import re
from utils import some, get_attr_or_item
from enum import Enum, IntEnum
from typing import Any
from exceptions import BuiltinError, MissingScope
from native import shuffled, stats, flatten
from random import random as rand

NotLocal = object()
NotBuiltin = object()


class CallStack:
    def __init__(self, datastore=None, frames=None):
        self.frame = 0
        self.datastore = datastore or Temporary()
        self.frames = frames or {}
        self.anonymous = []
        self.closure = []

    def function_push(self, arguments: dict, closed: dict):
        self.frame_push()
        self.scope_push(arguments)
        self.closure_push(closed)
        return self.frame

    def function_pop(self):
        out = self.frame
        self.closure_pop()
        self.frame_pop()
        return out

    def closure_push(self, frozen):
        self.closure.append(frozen)

    def closure_pop(self):
        self.closure.pop()

    def closure_clear(self):
        self.closure.clear()

    @property
    def frame_top(self):
        try:
            return self.frames[self.frame]
        except KeyError:
            return NotLocal

    def frame_push(self):
        self.frame += 1
        self.frames[self.frame] = []
        return self.frame

    def frame_pop(self):
        out = self.frames.pop(self.frame)
        self.frame -= 1
        return out

    def freeze(self):
        if (frame := self.frame_top) is NotLocal:
            try:
                return [copy.deepcopy(self.scope_top)]
            except IndexError:
                return [{}]
        return copy.deepcopy(frame)

    def scope_push(self, scope=None):
        new = scope or {}
        try:
            self.frames[self.frame].append(new)
        except KeyError:
            self.anonymous.append(new)
        return self.frame

    def scope_pop(self):
        try:
            self.frames[self.frame].pop()
        except IndexError as e:
            if 'pop from empty list' in str(e):
                raise MissingScope("Can't pop scope from empty stack frame.")
            else:
                raise MissingScope("Can't pop scope from global stack frame.")
        except KeyError:
            self.anonymous.pop()
        return self.frame

    @property
    def scope_top(self):
        try:
            return self.frames[self.frame][-1]
        except IndexError as e:
            if 'list index out of range' in str(e):
                raise MissingScope("Can't get scope from empty stack frame.")
            else:
                raise MissingScope("Can't get scope from global stack frame.")
        except KeyError:
            return self.anonymous[-1]

    def get(self, key):
        if (frame := self.frame_top) is NotLocal:
            if self.anonymous:
                for scope in reversed(self.anonymous):
                    if key in scope:
                        return scope[key]
            return NotLocal

        for scope in reversed(frame):
            if key in scope:
                return scope[key]
        if self.closure:
            for scope in reversed(self.closure[-1]):
                if key in scope:
                    return scope[key]
        return NotLocal

    def put(self, key, value):
        if (frame := self.frame_top) is NotLocal and self.anonymous:
            for scope in self.anonymous:
                if key in scope:
                    scope[key] = value
                    return value
            self.scope_top[key] = value
            return value
        for scope in frame:
            if key in scope:
                scope[key] = value
                return value
        self.scope_top[key] = value
        return value

    def drop(self, key):
        if (frame := self.frame_top) is NotLocal and self.anonymous:
            for scope in reversed(self.anonymous):
                if key in scope:
                    out = scope[key]
                    del scope[key]
                    return out
        for scope in reversed(frame):
            if key in scope:
                out = scope[key]
                del scope[key]
                return out
        return NotLocal


class AccessType(Enum):
    KEY = 0
    SLICE = 1
    DOT = 2


class AccessorType(Enum):
    ATTR = 0
    SLICE = 1


class IdentType(IntEnum):
    SCOPED = 0
    USER = 1
    SERVER = 2
    PUBLIC = 3


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
        'sorted': sorted,
        'min': min,
        'max': max,
        'shuffled': shuffled,
        'stats': stats,
        'flatten': flatten,
        'rand': rand,
        'regex': re,
    }

    def __new__(cls, *accessors):
        name, *attrs = accessors
        if name not in cls.exposed:
            return NotBuiltin
        return Builtin(cls.exposed[name], name, attrs)


class Access:
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


class Accessor:
    def __init__(self, atype, value):
        self.atype = atype
        self.value = value

    def get(self, from_object):
        match self:
            case self.__class__(AccessorType.ATTR, x):
                return get_attr_or_item(from_object, x)
            case self.__class__(AccessorType.SLICE, x):
                return from_object[x]

    @classmethod
    def attr(cls, value):
        return cls(AccessorType.ATTR, value)

    @classmethod
    def slice(cls, value):
        return cls(AccessorType.SLICE, value)

    @property
    def args(self):
        return self.atype, self.value

    __match_args__ = ('atype', 'value')

    def __repr__(self):
        return f'{type(self).__name__}({self.atype!r}, {self.value!r})'

    def __str__(self):
        return f'{self.value!r}'


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
        elif (maybe_scoped := self.call_stack.get(self.name)) is not NotLocal:
            target = maybe_scoped
        else:
            target = self.call_stack.datastore.get(self.itype, self.name, *self.accessors)
        for acc in self.accessors:
            target = acc.get(target)
        return target

    def put(self, value):
        if (maybe_builtin := Module(self.name)) is not NotBuiltin:
            raise BuiltinError.from_instance(maybe_builtin, "assign to")
        elif self.itype == IdentType.SCOPED:
            return self.call_stack.put(self.name, value)
        return self.call_stack.datastore.put(self.itype, value, self.name, *self.accessors)

    def drop(self):
        if (maybe_builtin := Module(self.name)) is not NotBuiltin:
            raise BuiltinError.from_instance(maybe_builtin, "delete")
        elif self.itype == IdentType.SCOPED:
            return self.call_stack.drop(self.name)
        return self.call_stack.datastore.drop(self.itype, self.name, *self.accessors)


class AbstractDatastore:
    def get(self, itype, name, *accessors):
        return NotImplemented

    def put(self, itype, value, name, *accessors):
        return NotImplemented

    def drop(self, itype, name, *accessors):
        return NotImplemented


class Temporary(AbstractDatastore):
    def __init__(self):
        self.table = {
            IdentType.USER: {},
            IdentType.SERVER: {},
            IdentType.PUBLIC: {},
        }

    @staticmethod
    def mutation_target(itype, name, *accessors):
        return f'self.table[{int(itype)}][{name!r}]' + ''.join(
            f'.{acc!s}' if acc.atype == AccessorType.ATTR else f'[{acc!s}]' for acc in accessors)

    def get(self, itype, name, *accessors):
        itype = itype or IdentType.SERVER
        target = self.table[itype][name]
        for acc in accessors:
            target = acc.get(target)
        return target

    def put(self, itype, value, name, *accessors):
        itype = itype or IdentType.SERVER
        insert = self.mutation_target(itype, name, *accessors) + f' = {value!r}'
        exec(insert)
        return value

    def drop(self, itype, name, *accessors):
        itype = itype or IdentType.SERVER
        out = self.get(itype, name, *accessors)
        delete = 'del self.mutation_target(itype, name, *accessors)'
        exec(delete)
        return out
