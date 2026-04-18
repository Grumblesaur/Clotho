import datetime
import sys
import traceback
from dbm.sqlite3 import LOOKUP_KEY

import lark

from dicelang.exceptions import Terminate, Help, DicelangSignal, IllegalSignal, ExcessiveRuntime, Continue, Break, \
    Impossible
from dicelang.lookup import CallStack, Ownership, IdentType, Lookup
from dicelang import result
from dicelang.native import PrintQueue
from dicelang.special import Undefined


class DicelangInterpreter:
    default_owner = 'clotho'
    default_server = 'test'
    default_channel = 'default'
    dispatch = None

    def __init__(self, call_stack: CallStack = None, time_limit_seconds: int | None = 15):
        self.call_stack = call_stack or CallStack()
        self.ownership = None
        self.command_limit = datetime.timedelta(time_limit_seconds) if time_limit_seconds is not None else None
        self.start_time = None
        self.limited = self.command_limit is not None

    def execute(self, tree, as_owner: str = None, as_server: str = None, in_channel: str = None):
        owner = as_owner or self.default_owner
        server = as_server or self.default_server
        channel = in_channel or self.default_channel
        try:
            self.ownership = Ownership(user=owner, server=server, channel=channel)
            self.call_stack.set_ownership(self.ownership)
            self.start_time = datetime.datetime.now()
            value = self.visit(tree)
            r = result.success(value=value, console=PrintQueue.flush())
            arg_sets = [
                {'itype': IdentType.USER, 'owner': self.ownership.user},
                {'itype': IdentType.SERVER, 'owner': self.ownership.server},
                {'itype': IdentType.CHANNEL, 'owner': self.ownership.channel},
                {'itype': IdentType.PUBLIC, 'owner': self.default_owner},
                {'itype': IdentType.USER_SERVER, 'owner': f'{self.ownership.server}:{self.ownership.user}'},
            ]
            for arg_set in arg_sets:
                self.call_stack.datastore.put(**arg_set, value=value, name='_')
        except Terminate as term:
            r = result.success(value=term.unwrap(), console=PrintQueue.flush())
        except Help as e:
            r = result.helptext(value=e)
        except DicelangSignal as e:
            error = IllegalSignal(f'{e.__class__.__name__} used outside of flow control context')
            r = result.failure(error=error, console=PrintQueue.flush())
        except Exception as e:
            r = result.failure(error=f'{e.__class__.__name__}: {e!s}', console=PrintQueue.flush(), exc_type=e.__class__)
            traceback.print_tb(e.__traceback__)
        finally:
            self.call_stack.reset()
            self.start_time = None
        return r

    def check_excessive_runtime(self, action: str, limit=None):
        if not self.limited:
            return
        now = datetime.datetime.now()
        delta = datetime.timedelta(limit) if limit else self.command_limit
        if (tm := now - self.start_time) > delta:
            raise ExcessiveRuntime(f'{tm.seconds} seconds to {action} (limit: {delta.seconds})')
    

    def visit_children(self, tree):
        return [self.visit(child) if isinstance(child, lark.Tree) else child for child in tree.children]

    def dispatch_default(self, tree):
        return self.visit(tree.children[0])

    def visit(self, tree):
        handler = self.dispatch.get(tree.data, self.dispatch_default)
        return handler(tree)

    def block(self, tree: lark.Tree):
        """d:block"""
        self.call_stack.scope_push()
        r = self.visit_children(tree)[-2]
        self.call_stack.scope_pop()
        return r

    def if_block(self, tree: lark.Tree):
        """d:if_block"""
        _if_kw, condition, _then_kw, body = tree.children
        return self.visit(body) if self.visit(condition) else Undefined

    def if_else_block(self, tree: lark.Tree):
        """d:if_else_block"""
        _if_kw, condition, _then_kw, if_body, _else_kw, else_body = tree.children
        return self.visit(if_body) if self.visit(condition) else self.visit(else_body)

    def while_loop(self, tree: lark.Tree):
        """d:while_loop"""
        _while_kw, condition, _do_kw, body = tree.children
        results = []
        try:
            while self.visit(condition):
                try:
                    results.append(self.visit(body))
                except Continue as c:
                    if c:
                        results.append(c.value)
                self.check_excessive_runtime("to execute command with while loop")
        except Break as b:
            if b:
                results.append(b.value)
        return results

    def do_while_loop(self, tree: lark.Tree):
        """d:do_while_loop"""
        _do_kw, body, _while_kw, condition = tree.children
        results = [self.visit(body)]
        try:
            while self.visit(condition):
                try:
                    results.append(self.visit(body))
                except Continue as c:
                    if c:
                        results.append(c.value)
                self.check_excessive_runtime("to execute command with do-while loop")
        except Break as b:
            if b:
                results.append(b.value)
        return results

    def for_loop(self, tree: lark.Tree):
        """d:for_loop"""
        _for_kw, ident, _in_kw, iterable, _do_kw, body = tree.children
        action = None
        x = None
        match name := self.visit(ident):
            case (IdentType.SCOPED, x):
                action = Lookup.scoped
            case (IdentType.USER, x):
                action = Lookup.user
            case (IdentType.CHANNEL, x):
                action = Lookup.channel
            case (IdentType.PUBLIC, x):
                action = Lookup.public
            case (IdentType.USER_SERVER, x):
                action = Lookup.user_server
            case (IdentType.SERVER, x):
                action = Lookup.server
            case _:
                raise Impossible(f"can't assign for loop variable {name}")

        loop_variable = action(self.call_stack, self.ownership, x)
        results = []
        try:
            for x in self.visit(iterable):
                loop_variable.put(x)
                try:
                    results.append(self.visit(body))
                except Continue as c:
                    if c:
                        results.append(c.value)
                self.check_excessive_runtime("to execute command with for loop")
        except Break as b:
            if b:
                results.append(b.value)
        return results