import copy
import pickle
import sqlite3
import threading
import time
import os
from pathlib import Path
from typing import Any, Protocol, Hashable, Iterable, Self
from collections import Counter
from enum import Enum, IntEnum

from dicelang import plugins
from dicelang.exceptions import BuiltinError, MissingScope, DeleteNonexistent, FetchNonexistent, Impossible, \
    NoSuchVariable
from dicelang.utils import get_attr_or_item, some
from dicelang.special import Undefined

NotLocal = object()
NotBuiltin = object()
Scope = dict[str, Any]
Frame = list[Scope]
LookupResult = Any
Location = Path | str
IS_TEST = 'dicelang.lark' in set(os.listdir(os.getcwd()))


class Subscriptable(Protocol):
    def __getitem__(self, key_or_slice: Hashable) -> Any:
        pass


class Dottable(Protocol):
    def __getattr__(self, name: str) -> Any:
        pass


Accessible = Subscriptable | Dottable
AccessKey = slice | str | Hashable


class IdentType(IntEnum):
    SCOPED = 0
    USER = 1
    SERVER = 2
    PUBLIC = 3

    def keyword(self) -> str:
        if self is self.SCOPED:
            return ''
        elif self is self.USER:
            return "my"
        elif self is self.SERVER:
            return "our"
        return "public"


class Ownership:
    def __init__(self, user: str, server: str):
        self.user = user
        self.server = server

    def get(self, itype: IdentType) -> str:
        if itype is IdentType.USER:
            return self.user
        if itype in (IdentType.SCOPED, IdentType.SERVER):
            return self.server
        return "clotho"

    def __repr__(self):
        return f'{self.__class__.__name__}({self.user!r}, {self.server!r})'


class CallStack:
    def __init__(self, datastore=None, frames=None):
        self.frame: int = 0
        self.datastore = datastore or SelfPruningStore(f'{"../" if IS_TEST else ""}persistence.db')
        self.frames = frames or {}
        self.anonymous = []
        self.closure = []
        self.ownership = None

    def set_ownership(self, ownership: Ownership, frames: dict | None = None):
        self.ownership = ownership
        self.frames: dict = frames or {}
        self.anonymous: list = []
        self.closure: list = []

    def reset(self) -> None:
        self.frame = 0
        self.frames.clear()
        self.anonymous.clear()
        self.closure.clear()
        self.ownership = None

    def function_push(self, arguments: dict, closed: dict) -> int:
        self.frame_push()
        self.scope_push(arguments)
        self.closure_push(closed)
        return self.frame

    def function_pop(self) -> int:
        out = self.frame
        self.closure_pop()
        self.frame_pop()
        return out

    def closure_push(self, frozen) -> None:
        self.closure.append(frozen)

    def closure_pop(self) -> None:
        self.closure.pop()

    def closure_clear(self) -> None:
        self.closure.clear()

    @property
    def frame_top(self) -> Frame | object:
        try:
            return self.frames[self.frame]
        except KeyError:
            return NotLocal

    def frame_push(self) -> int:
        self.frame += 1
        self.frames[self.frame] = []
        return self.frame

    def frame_pop(self) -> Frame:
        out = self.frames.pop(self.frame)
        self.frame -= 1
        return out

    def freeze(self) -> Frame:
        if (frame := self.frame_top) is NotLocal:
            try:
                return [copy.deepcopy(self.scope_top)]
            except IndexError:
                return [{}]
        return copy.deepcopy(frame)

    def scope_push(self, scope: Scope | None = None) -> int:
        new = scope or {}
        try:
            self.frames[self.frame].append(new)
        except KeyError:
            self.anonymous.append(new)
        return self.frame

    def scope_pop(self) -> int:
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
    def scope_top(self) -> Scope:
        try:
            return self.frames[self.frame][-1]
        except IndexError as e:
            if 'list index out of range' in str(e):
                raise MissingScope("Can't get scope from empty stack frame.")
            else:
                raise MissingScope("Can't get scope from global stack frame.")
        except KeyError:
            return self.anonymous[-1]

    def get(self, key: str) -> LookupResult:
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

    def put(self, key: str, value: Any) -> Any:
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

    def drop(self, key: str) -> LookupResult:
        if (frame := self.frame_top) is NotLocal and self.anonymous:
            for scope in reversed(self.anonymous):
                if key in scope:
                    out = scope[key]
                    del scope[key]
                    return out
            raise NoSuchVariable(f"No local variable called `{key}`.")
        for scope in reversed(frame):
            if key in scope:
                out = scope[key]
                del scope[key]
                return out
        return NotLocal


class AccessorType(Enum):
    ATTR = 0
    KEY = 1
    SLICE = 2


class Module:
    exposed = plugins.exposed

    def __new__(cls, *accessors):
        name, *attrs = accessors
        if name not in cls.exposed:
            return NotBuiltin
        return Builtin(cls.exposed[name], name, attrs)


class Accessor:
    def __init__(self, atype: AccessorType, value: AccessKey):
        self.atype = atype
        self.value = value

    def get(self, from_object: Accessible) -> Any:
        match self:
            case self.__class__(AccessorType.ATTR, x):
                return get_attr_or_item(from_object, x)
            case self.__class__(AccessorType.KEY, x):
                return get_attr_or_item(from_object, x)
            case self.__class__(AccessorType.SLICE, x):
                return from_object[x]

    @classmethod
    def attr(cls, value: str) -> Self:
        return cls(AccessorType.ATTR, value)

    @classmethod
    def slice(cls, value: slice) -> Self:
        return cls(AccessorType.SLICE, value)

    @classmethod
    def key(cls, value: Hashable) -> Self:
        return cls(AccessorType.KEY, value)

    @property
    def args(self) -> tuple[AccessorType, AccessKey]:
        return self.atype, self.value

    __match_args__ = ('atype', 'value')

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.atype!r}, {self.value!r})'

    def __str__(self) -> str:
        match self.atype:
            case AccessorType.KEY:
                return f'[{self.value!r}]'
            case AccessorType.ATTR:
                return f'.{self.value!s}]'
            case AccessorType.SLICE:
                x, y, z = self.value.start, self.value.stop, self.value.step
                match int(''.join(str(some(i)) for i in (x, y, z)), base=2):
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
        raise Impossible(f"Undefined or unhandled AccessorType: {self.atype}")


class Builtin:
    def __init__(self, obj: Any, name: str, accessors: Iterable[Accessor]):
        self.obj = obj
        self.name = name
        self.accessors = accessors

    def __repr__(self) -> str:
        name, accessors = self.accessors
        access = ''.join(repr(a) for a in accessors)
        return f'{name!s}{access}'

    def serialization(self) -> str:
        return f'{type(self).__name__}({repr(self)!r})'

    @property
    def get(self) -> Any:
        if not self.accessors:
            return self.obj
        return eval(repr(self))


class Lookup:
    def __init__(self, itype: IdentType, call_stack: CallStack, owner: str, name: str, *accessors: Accessor):
        self.itype = itype
        self.owner = owner
        self.name = name
        self.accessors = accessors
        self.call_stack = call_stack

    def __repr__(self) -> str:
        clsname = self.__class__.__name__
        return f'{clsname}({self.itype!r}, {self.call_stack!r}, {self.owner!r}, {self.name!r}, {self.accessors!r})'

    @classmethod
    def scoped(cls, call_stack: CallStack, ownership: Ownership, name: str, *accessors: Accessor) -> Self:
        return cls(itype := IdentType.SCOPED, call_stack, ownership.get(itype), name, *accessors)

    @classmethod
    def user(cls, call_stack: CallStack, ownership: Ownership, name: str, *accessors: Accessor) -> Self:
        return cls(itype := IdentType.USER, call_stack, ownership.get(itype), name, *accessors)

    @classmethod
    def server(cls, call_stack: CallStack, ownership: Ownership, name: str, *accessors: Accessor) -> Self:
        return cls(itype := IdentType.SERVER, call_stack, ownership.get(itype), name, *accessors)

    @classmethod
    def public(cls, call_stack: CallStack, ownership: Ownership, name: str, *accessors: Accessor) -> Self:
        return cls(itype := IdentType.PUBLIC, call_stack, ownership.get(itype), name, *accessors)

    def get(self) -> Any:
        if (maybe_builtin := Module(self.name)) is not NotBuiltin:
            target = maybe_builtin.get
        elif (maybe_scoped := self.call_stack.get(self.name)) is not NotLocal:
            target = maybe_scoped
        else:
            itype = self.itype if self.itype is not IdentType.SCOPED else IdentType.SERVER
            target = self.call_stack.datastore.get(itype, self.owner, self.name, *self.accessors)
        for acc in self.accessors:
            target = acc.get(target)
        return target

    def put(self, value: Any) -> Any:
        if (maybe_builtin := Module(self.name)) is not NotBuiltin:
            raise BuiltinError.from_instance(maybe_builtin, "assign to")
        elif self.itype == IdentType.SCOPED and self.call_stack.frame > 0:
            return self.call_stack.put(self.name, value)
        itype = self.itype if self.itype is not IdentType.SCOPED else IdentType.SERVER
        return self.call_stack.datastore.put(itype, self.owner, value, self.name, *self.accessors)

    def drop(self) -> Any:
        if (maybe_builtin := Module(self.name)) is not NotBuiltin:
            raise BuiltinError.from_instance(maybe_builtin, "delete")
        elif self.itype == IdentType.SCOPED and IdentType.SCOPED > 0:
            return self.call_stack.drop(self.name)
        itype = self.itype if self.itype is not IdentType.SCOPED else IdentType.SERVER
        return self.call_stack.datastore.drop(itype, self.owner, self.name, *self.accessors)


class BasicStore:
    def __init__(self):
        self.storage = {IdentType.USER: {}, IdentType.SERVER: {}, IdentType.PUBLIC: {}}

    def get(self, itype: IdentType, owner: str, name: str, *accessors: Accessor) -> Any:
        store = self.storage[itype or IdentType.SERVER]
        failed = False
        if owner not in store:
            store[owner] = {}
            failed = True
        elif name not in store[owner]:
            failed = True
        if failed:
            raise FetchNonexistent(f"No variable named '{itype.keyword()} {name}'.")
        value = store[owner][name]
        for accessor in accessors:
            value = accessor.get(value)
        return value

    def put(self, itype: IdentType, owner: str, value, name: str, *accessors: Accessor) -> Any:
        store = self.storage[itype or IdentType.SERVER]
        if owner not in store:
            store[owner] = {name: value}
        elif name not in store[owner]:
            store[owner][name] = value
        else:
            exec(f'store[owner][name]{"".join(str(acc) for acc in accessors)} = {value!r}')
        return value

    def drop(self, itype: IdentType, owner: str, name: str, *accessors: Accessor) -> Any:
        store = self.storage[itype or IdentType.SERVER]
        if owner not in store or name not in store[owner]:
            raise DeleteNonexistent(f'"{itype.keyword()} {name}"')
        value = store[owner][name]
        for accessor in accessors:
            accessor.get(value)
        exec(f'del store[owner][name]{"".join(str(acc) for acc in accessors)}')
        return value


class PersistentStore(BasicStore):
    def __init__(self, db_location: Location):
        super().__init__()
        self.conn = sqlite3.connect(db_location)
        self.cur = self.conn.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS variables(
            ownership INTEGER NOT NULL,
            owner TEXT NOT NULL,
            name TEXT NOT NULL,
            value BLOB,
            PRIMARY KEY(ownership, owner, name)
        );""")
        self.conn.commit()

    def __del__(self) -> None:
        self.conn.commit()
        self.conn.close()

    def get(self, itype: IdentType, owner: str, name: str, *accessors: Accessor) -> Any:
        try:
            value = super().get(itype, owner, name, *accessors)
        except FetchNonexistent:
            res = self.cur.execute('SELECT value FROM variables WHERE ownership = ? AND owner = ? AND name = ?',
                                   (itype, owner, name))
            if (pickled := res.fetchone()) is None:
                value = Undefined
            else:
                value = pickle.loads(pickled[0])
        return value

    def put(self, itype: IdentType, owner: str, value, name: str, *accessors: Accessor) -> Any:
        super().put(itype, owner, value, name, *accessors)
        obj = self.storage[itype or IdentType.SERVER][owner][name]
        self.cur.execute('''INSERT INTO variables VALUES(?, ?, ?, ?)
                             ON CONFLICT(ownership, owner, name)
                             DO UPDATE SET value = EXCLUDED.value''', (itype, owner, name, pickle.dumps(obj)))
        self.conn.commit()
        return value

    def drop(self, itype: IdentType, owner: str, name: str, *accessors: Accessor) -> Any:
        try:  # Obtain a copy of the item we intend to delete, or raise an error on deleting a missing object.
            out = self.get(itype, owner, name, *accessors)
            super().drop(itype, owner, name)
        except FetchNonexistent as e:
            raise DeleteNonexistent(e)
        if accessors:  # On a subscript deletion, remove the target item from the cache and therefrom update the store.
            obj = self.storage[itype][owner][name]
            exec(f'del obj{"".join(str(acc) for acc in accessors)}')
            self.put(itype, owner, obj, name)
            return out

        # Otherwise, just prune the whole row from the store.
        self.cur.execute('DELETE FROM variables WHERE ownership = ? AND owner = ? AND name = ?', (itype, owner, name))
        self.conn.commit()
        return out


class SelfPruningStore(PersistentStore):
    def __init__(self, db_location: Location, cycle_time: int = 3 * 60 * 60, cycle_decay: int = 5):
        super().__init__(db_location)
        self.cycle_decay = cycle_decay
        self.usage = {IdentType.USER: {}, IdentType.SERVER: {}, IdentType.PUBLIC: {}}

        def pruning_task(datastore) -> None:
            while True:
                time.sleep(cycle_time)
                pruned = datastore.prune()
                print(f'pruned {pruned} objects from caches')

        self.pruner = threading.Thread(target=pruning_task, args=(self,), daemon=True)
        self.pruner.start()
        print(f'Self-pruning thread initiated. Culling cycle: {cycle_time / 3600:.2f} hours.')

    def get(self, itype: IdentType, owner: str, name: str, *accessors: Accessor) -> Any:
        out = super().get(itype, owner, name, *accessors)
        usage = self.usage[itype or IdentType.SERVER]
        if owner not in usage:
            usage[owner] = Counter({name: 1})
        else:
            usage[owner][name] += 1
        return out

    def put(self, itype: IdentType, owner: str, value, name: str, *accessors: Accessor) -> Any:
        out = super().put(itype, owner, value, name, *accessors)
        usage = self.usage[itype or IdentType.SERVER]
        if owner not in usage:
            usage[owner] = Counter({name: 1})
        else:
            usage[owner][name] += 1
        return out

    def drop(self, itype: IdentType, owner: str, name: str, *accessors: Accessor) -> Any:
        out = super().drop(itype, owner, name, *accessors)
        usage = self.usage[itype or IdentType.SERVER]
        if owner not in usage or name not in usage[owner]:
            return out
        if accessors is None:
            del usage[owner][name]
        else:
            usage[owner][name] += 1
        return out

    def prune(self) -> int:
        marked = []
        for itype in self.usage:
            for owner in self.usage[itype]:
                for name in self.usage[itype][owner]:
                    if (uses := self.usage[itype][owner][name]) == 0:
                        marked.append((itype, owner, name))
                    else:
                        self.usage[itype][owner][name] = max(0, uses - self.cycle_decay)
        pruned = 0
        for item in marked:
            pruned += self._remove(*item)
            print(f'prune {item} from cache')
        return pruned

    def _remove(self, itype: IdentType, owner: str, name: str) -> int:
        del self.storage[itype][owner][name]
        del self.usage[itype][owner][name]
        return 1
