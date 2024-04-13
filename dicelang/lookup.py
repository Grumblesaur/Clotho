import copy
import pickle
import sqlite3
import threading
import time
from collections import Counter
from enum import Enum, IntEnum

from dicelang import plugins
from dicelang.exceptions import BuiltinError, MissingScope, DeleteNonexistent, FetchNonexistent, Impossible
from dicelang.utils import get_attr_or_item, some

NotLocal = object()
NotBuiltin = object()


class CallStack:
    def __init__(self, datastore=None, frames=None):
        self.frame = 0
        self.datastore = datastore or SelfPruningStore('persistence.db')
        self.frames = frames or {}
        self.anonymous = []
        self.closure = []

    def reset(self):
        self.frame = 0
        self.frames.clear()
        self.anonymous.clear()
        self.closure.clear()

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


class AccessorType(Enum):
    ATTR = 0
    KEY = 1
    SLICE = 2


class IdentType(IntEnum):
    SCOPED = 0
    USER = 1
    SERVER = 2
    PUBLIC = 3

    def keyword(self):
        if self is self.SCOPED:
            return ''
        elif self is self.USER:
            return "my"
        elif self is self.SERVER:
            return "our"
        return "public"


class Module:
    exposed = plugins.exposed

    def __new__(cls, *accessors):
        name, *attrs = accessors
        if name not in cls.exposed:
            return NotBuiltin
        return Builtin(cls.exposed[name], name, attrs)


class Accessor:
    def __init__(self, atype, value):
        self.atype = atype
        self.value = value

    def get(self, from_object):
        match self:
            case self.__class__(AccessorType.ATTR, x):
                return get_attr_or_item(from_object, x)
            case self.__class__(AccessorType.KEY, x):
                return get_attr_or_item(from_object, x)
            case self.__class__(AccessorType.SLICE, x):
                return from_object[x]

    @classmethod
    def attr(cls, value):
        return cls(AccessorType.ATTR, value)

    @classmethod
    def slice(cls, value):
        return cls(AccessorType.SLICE, value)

    @classmethod
    def key(cls, value):
        return cls(AccessorType.KEY, value)

    @property
    def args(self):
        return self.atype, self.value

    __match_args__ = ('atype', 'value')

    def __repr__(self):
        return f'{type(self).__name__}({self.atype!r}, {self.value!r})'

    def __str__(self):
        match self.atype:
            case AccessorType.KEY:
                return f'[{self.value!r}]'
            case AccessorType.ATTR:
                return f'.{self.value!s}]'
            case AccessorType.SLICE:
                x, y, z = self.value.start, self.value.stop, self.value.step
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
        raise Impossible(f"Undefined or unhandled AccessorType: {self.atype}")


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
    def __init__(self, itype, call_stack, owner, name, *accessors):
        self.itype = itype
        self.owner = owner
        self.name = name
        self.accessors = accessors
        self.call_stack = call_stack

    def __repr__(self):
        return f'{self.__class__.__name__}({self.itype, self.call_stack, self.owner, self.name, self.accessors})'

    @classmethod
    def scoped(cls, call_stack, owner, name, *accessors):
        return cls(IdentType.SCOPED, call_stack, owner, name, *accessors)

    @classmethod
    def user(cls, call_stack, owner, name, *accessors):
        return cls(IdentType.USER, call_stack, owner, name, *accessors)

    @classmethod
    def server(cls, call_stack, owner, name, *accessors):
        return cls(IdentType.SERVER, call_stack, owner, name, *accessors)

    @classmethod
    def public(cls, call_stack, _owner, name, *accessors):
        return cls(IdentType.PUBLIC, call_stack, "clotho", name, *accessors)

    def get(self):
        if (maybe_builtin := Module(self.name)) is not NotBuiltin:
            target = maybe_builtin.get
        elif (maybe_scoped := self.call_stack.get(self.name)) is not NotLocal:
            target = maybe_scoped
        else:
            target = self.call_stack.datastore.get(self.itype, self.owner, self.name, *self.accessors)
        for acc in self.accessors:
            target = acc.get(target)
        return target

    def put(self, value):
        if (maybe_builtin := Module(self.name)) is not NotBuiltin:
            raise BuiltinError.from_instance(maybe_builtin, "assign to")
        elif self.itype == IdentType.SCOPED:
            return self.call_stack.put(self.name, value)
        return self.call_stack.datastore.put(self.itype, self.owner, value, self.name, *self.accessors)

    def drop(self):
        if (maybe_builtin := Module(self.name)) is not NotBuiltin:
            raise BuiltinError.from_instance(maybe_builtin, "delete")
        elif self.itype == IdentType.SCOPED:
            return self.call_stack.drop(self.name)
        return self.call_stack.datastore.drop(self.itype, self.owner, self.name, *self.accessors)


class BasicStore:
    def __init__(self):
        self.storage = {IdentType.USER: {}, IdentType.SERVER: {}, IdentType.PUBLIC: {}}

    def get(self, itype: IdentType, owner: str, name: str, *accessors):
        store = self.storage[itype or IdentType.SERVER]
        failed = False
        if owner not in store:
            store[owner] = {}
            failed = True
        elif name not in store[owner]:
            failed = True
        if failed:
            raise FetchNonexistent(f'"{itype.keyword()} {name}"')
        value = store[owner][name]
        for accessor in accessors:
            value = accessor.get(value)
        return value

    def put(self, itype: IdentType, owner: str, value, name: str, *accessors):
        store = self.storage[itype or IdentType.SERVER]
        if owner not in store:
            store[owner] = {name: value}
        elif name not in store[owner]:
            store[owner][name] = value
        else:
            exec(f'store[owner][name]{"".join(str(acc) for acc in accessors)} = {value!r}')
        return value

    def drop(self, itype: IdentType, owner: str, name: str, *accessors):
        store = self.storage[itype or IdentType.SERVER]
        if owner not in store or name not in store[owner]:
            raise DeleteNonexistent(f'"{itype.keyword()} {name}"')
        value = store[owner][name]
        for accessor in accessors:
            accessor.get(value)
        exec(f'del store[owner][name]{"".join(str(acc) for acc in accessors)}')
        return value


class PersistentStore(BasicStore):
    def __init__(self, db_location):
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

    def __del__(self):
        self.conn.commit()
        self.conn.close()

    def get(self, itype: IdentType, owner: str, name: str, *accessors):
        try:
            value = super().get(itype, owner, name, *accessors)
        except FetchNonexistent:
            res = self.cur.execute('SELECT value FROM variables WHERE ownership = ? AND owner = ? AND name = ?',
                                   (itype, owner, name))
            if (pickled := res.fetchone()) is None:
                print(pickled)
                raise
            value = pickle.loads(pickled[0])
        return value

    def put(self, itype: IdentType, owner: str, value, name: str, *accessors):
        super().put(itype, owner, value, name, *accessors)
        obj = self.storage[itype or IdentType.SERVER][owner][name]
        self.cur.execute('''INSERT INTO variables VALUES(?, ?, ?, ?)
                             ON CONFLICT(ownership, owner, name)
                             DO UPDATE SET value = EXCLUDED.value''', (itype, owner, name, pickle.dumps(obj)))
        self.conn.commit()
        return value

    def drop(self, itype: IdentType, owner: str, name: str, *accessors):
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
    def __init__(self, db_location, cycle_time=3 * 60 * 60, cycle_decay=5):
        super().__init__(db_location)
        self.cycle_decay = cycle_decay
        self.usage = {IdentType.USER: {}, IdentType.SERVER: {}, IdentType.PUBLIC: {}}

        def pruning_task(datastore):
            while True:
                time.sleep(cycle_time)
                pruned = datastore.prune()
                print(f'pruned {pruned} objects from cache')

        self.pruner = threading.Thread(target=pruning_task, args=(self,), daemon=True)
        self.pruner.start()
        print('Self-pruning thread initiated. Culling cycle:', cycle_time / 3600, 'hours.')

    def get(self, itype: IdentType, owner: str, name: str, *accessors):
        out = super().get(itype, owner, name, *accessors)
        usage = self.usage[itype or IdentType.SERVER]
        if owner not in usage:
            usage[owner] = Counter({name: 1})
        else:
            usage[owner][name] += 1
        return out

    def put(self, itype: IdentType, owner: str, value, name: str, *accessors):
        out = super().put(itype, owner, value, name, *accessors)
        usage = self.usage[itype or IdentType.SERVER]
        if owner not in usage:
            usage[owner] = Counter({name: 1})
        else:
            usage[owner][name] += 1
        return out

    def drop(self, itype: IdentType, owner: str, name: str, *accessors):
        out = super().drop(itype, owner, name, *accessors)
        usage = self.usage[itype or IdentType.SERVER]
        if owner not in usage or name not in usage[owner]:
            return out
        if accessors is None:
            del usage[owner][name]
        else:
            usage[owner][name] += 1
        return out

    def prune(self):
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

    def _remove(self, itype: IdentType, owner: str, name: str):
        del self.storage[itype][owner][name]
        del self.usage[itype][owner][name]
        return 1
