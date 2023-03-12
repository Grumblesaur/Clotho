import copy
from exceptions import ScopeError

NotLocal = object()


class CallStack:
    def __init__(self, frames=None):
        self.frame = 0
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
                raise ScopeError("Can't pop scope from empty stack frame.")
            else:
                raise ScopeError("Can't pop scope from global stack frame.")
        except KeyError:
            self.anonymous.pop()
        return self.frame

    @property
    def scope_top(self):
        try:
            return self.frames[self.frame][-1]
        except IndexError as e:
            if 'list index out of range' in str(e):
                raise ScopeError("Can't get scope from empty stack frame.")
            else:
                raise ScopeError("Can't get scope from global stack frame.")
        except KeyError:
            return self.anonymous[-1]

    def get(self, key):
        if (frame := self.frame_top) is NotLocal and self.anonymous:
            for scope in reversed(self.anonymous):
                if key in scope:
                    return scope[key]
        for scope in reversed(frame):
            if key in scope:
                return scope[key]

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

