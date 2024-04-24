import inspect
import itertools
import math
import operator
import random
from collections.abc import Iterable, Sequence
from functools import partialmethod
from numbers import Complex
from typing import Hashable

from lark.visitors import Interpreter

from dicelang import dicecore
from dicelang import ops
from dicelang import utils
from dicelang import result
from dicelang.exceptions import (AssignmentError, BadLiteral, Break, Continue, DicelangException, DicelangSignal, Empty,
                                 IllegalSignal, Impossible, InvalidSubscript, Return, SpreadError, Terminate, UnpackError)
from dicelang.lookup import Accessor, CallStack, IdentType, Lookup
from dicelang.special import Spread, Undefined
from dicelang.user_function import UserFunction
from dicelang.native import PrintQueue


class DicelangInterpreter(Interpreter):
    default_owner = 'clotho'

    def __init__(self, call_stack=None):
        self.call_stack = call_stack or CallStack()
        self.owner = None
        self.server = None

    def execute_test(self, tree):
        try:
            return self.visit(tree)
        finally:
            self.call_stack.reset()

    def execute(self, tree, as_owner: str = 'clotho', on_server: str = 'test'):
        try:
            self.owner = as_owner
            self.server = on_server
            value = self.visit(tree)
            r = result.success(value=value, console=PrintQueue.flush())
            self.call_stack.datastore.put(itype=IdentType.USER, owner=self.owner, value=value, name='_')
            self.call_stack.datastore.put(itype=IdentType.SERVER, owner=self.server, value=value, name='_')
            self.call_stack.datastore.put(itype=IdentType.PUBLIC, owner=self.default_owner, value=value, name='_')
        except Terminate as term:
            r = result.success(value=term.unwrap(), console=PrintQueue.flush())
        except DicelangSignal as e:
            error = IllegalSignal(f'{e.__class__.__name__} used outside of flow control context')
            r = result.failure(error=error, console=PrintQueue.flush())
        except Exception as e:
            r = result.failure(error=e, console=PrintQueue.flush())
        finally:
            self.call_stack.reset()
            self.owner = None
            self.server = None
        return r

    def block(self, tree):
        self.call_stack.scope_push()
        r = self.visit_children(tree)[-2]
        self.call_stack.scope_pop()
        return r

    def if_block(self, tree):
        _, condition, _, body = tree.children
        return self.visit(body) if self.visit(condition) else Undefined

    def if_else_block(self, tree):
        _, condition, _, if_body, _, else_body = tree.children
        return self.visit(if_body) if self.visit(condition) else self.visit(else_body)

    def while_loop(self, tree):
        _, condition, _, body = tree.children
        results = []
        try:
            while self.visit(condition):
                try:
                    results.append(self.visit(body))
                except Continue as c:
                    if c:
                        results.append(c)
        except Break as b:
            if b:
                results.append(b.value)
        return results

    def do_while_loop(self, tree):
        _, body, _, condition = tree.children
        results = [self.visit(body)]
        try:
            while self.visit(condition):
                try:
                    results.append(self.visit(body))
                except Continue as c:
                    if c:
                        results.append(c.value)
        except Break as b:
            if b:
                results.append(b.value)
        return results

    def for_loop(self, tree):
        _, ident, _, iterable, _, body = tree.children
        match name := self.visit(ident):
            case (IdentType.SCOPED, x):
                action = Lookup.scoped
            case (IdentType.USER, x):
                action = Lookup.user
            case (IdentType.SERVER, x):
                action = Lookup.server
            case (IdentType.PUBLIC, x):
                action = Lookup.public
            case _:
                raise Impossible(f"can't assign for loop variable {name}")
        loop_variable = action(self.call_stack, self.owner, x)
        results = []
        try:
            for x in self.visit(iterable):
                loop_variable.put(x)
                try:
                    results.append(self.visit(body))
                except Continue as c:
                    if c:
                        results.append(c.value)
        except Break as b:
            if b:
                results.append(b.value)
        return results

    def start(self, tree):
        self.call_stack.scope_push()
        out = self.visit_children(tree)[-1]
        self.call_stack.scope_pop()
        return out

    def if_ternary(self, tree):
        if_action, _, condition, _, else_action = tree.children
        if self.visit(condition):
            return self.visit(if_action)
        return self.visit(else_action)

    def repetition(self, tree):
        repeatable, repeats = tree.children
        return [self.visit(repeatable) for _ in range(self.visit(repeats))]

    def die_unary(self, tree):
        _, sides = self.visit(tree.children[0])
        return dicecore.keep_all(1, sides)

    def die_binary(self, tree):
        dice, _, sides = self.visit_children(tree)
        return dicecore.keep_all(dice, sides)

    def die_ternary_high(self, tree):
        dice, _, sides, _, keep = self.visit_children(tree)
        return dicecore.keep_highest(dice, sides, keep)

    def die_ternary_low(self, tree):
        dice, _, sides, _, keep = self.visit_children(tree)
        return dicecore.keep_lowest(dice, sides, keep)

    def roll_unary(self, tree):
        _, sides = self.visit(tree.children[0])
        return dicecore.keep_all(1, sides, as_sum=False)

    def roll_binary(self, tree):
        dice, _, sides = self.visit_children(tree)
        return dicecore.keep_all(dice, sides, as_sum=False)

    def roll_ternary_high(self, tree):
        dice, _, sides, _, keep = self.visit_children(tree)
        return dicecore.keep_highest(dice, sides, keep, as_sum=False)

    def roll_ternary_low(self, tree):
        dice, _, sides, _, keep = self.visit_children(tree)
        return dicecore.keep_lowest(dice, sides, keep, as_sum=False)

    def exponent(self, tree):
        mantissa, superscript = self.visit_children(tree)
        return mantissa ** superscript

    def unary_minus(self, tree):
        operand = self.visit(tree.children[0])
        if isinstance(operand, Sequence):
            return operand[::-1]
        return -operand

    def unary_plus(self, tree):
        operand = self.visit_children(tree)
        if isinstance(operand, (int, float, complex)):
            return +operand
        return operand

    def multiplication(self, tree):
        multiplier, multiplicand = self.visit_children(tree)
        if isinstance(multiplier, int) and isinstance(multiplicand, Sequence):
            direction = utils.sign(multiplier)
            return multiplicand[::direction] * abs(multiplier)
        elif isinstance(multiplier, Sequence) and isinstance(multiplicand, int):
            direction = utils.sign(multiplicand)
            return multiplier[::direction] * abs(multiplicand)
        return multiplier * multiplicand

    def division(self, tree):
        dividend, divisor = self.visit_children(tree)
        if isinstance(dividend, (list, tuple, set)):
            if not isinstance(divisor, str) and isinstance(divisor, Iterable):
                return type(dividend)(x for x in dividend if x not in divisor)
            else:
                return type(dividend)(x for x in dividend if x != divisor)
        if isinstance(dividend, dict):
            if not isinstance(divisor, str) and isinstance(divisor, Iterable):
                return {k: v for k, v in dividend.items() if k not in divisor}
            else:
                return {k: v for k, v in dividend.items() if k != divisor}
        if isinstance(dividend, str) and isinstance(divisor, str):
            return dividend.replace(divisor, '')
        return dividend / divisor

    def integer_division(self, tree):
        dividend, divisor = self.visit_children(tree)
        return dividend // divisor

    def left_shift(self, tree):
        bits, shift = self.visit_children(tree)
        if isinstance(bits, (list, tuple)):
            return bits + type(bits)([shift])
        elif isinstance(bits, str):
            return bits + str(shift)
        return bits << shift

    def right_shift(self, tree):
        bits, shift = self.visit_children(tree)
        if isinstance(bits, (list, tuple)):
            return type(bits)([shift]) + bits
        elif isinstance(bits, str):
            return str(shift) + bits
        return bits >> shift

    def remainder(self, tree):
        dividend, divisor = self.visit_children(tree)
        return dividend % divisor

    def addition(self, tree):
        addend, augend = self.visit_children(tree)
        if isinstance(addend, dict) and isinstance(augend, dict):
            return {**addend, **augend}
        if utils.isvector(addend) and utils.isvector(augend):
            return type(addend)(itertools.chain(addend, augend))
        return addend + augend

    def subtraction(self, tree):
        minuend, subtrahend = self.visit_children(tree)
        # For list-y minuends, remove the first instance of each element
        # in subtrahend (or subtrahend itself if it's not a container)
        # from minuend, if it's present.
        if utils.isordered(minuend):
            new = list(minuend)
            if utils.iscontainer(subtrahend):
                for item in subtrahend:
                    try:
                        new.remove(item)
                    except ValueError:
                        pass
                return type(minuend)(new)
            else:
                try:
                    new.remove(subtrahend)
                except ValueError:
                    pass
                return type(minuend)(new)
        elif isinstance(minuend, dict):
            return {k: v for k, v in minuend.items() if k != subtrahend}
        elif isinstance(minuend, set):
            return {item for item in minuend if item != subtrahend}
        elif isinstance(minuend, str) and isinstance(subtrahend, str):
            return minuend.replace(subtrahend, '', 1)
        return minuend - subtrahend

    def catenation(self, tree):
        return ops.cat(*self.visit_children(tree))

    def bit_and(self, tree):
        left, right = self.visit_children(tree)
        return left & right

    def bit_xor(self, tree):
        left, right = self.visit_children(tree)
        return left ^ right

    def bit_or(self, tree):
        left, right = self.visit_children(tree)
        return left | right

    def bit_not(self, tree):
        operand = self.visit(tree.children[0])
        if isinstance(operand, Complex):
            return operand.conjugate()
        return ~operand

    def sum_or_join(self, tree):
        operand = self.visit_children(tree)
        if isinstance(operand, Iterable) and not isinstance(operand, str):
            return utils.vector_sum(operand)
        elif isinstance(operand, Complex):
            return operand.imag
        return operand

    def coinflip(self, tree):
        a, b = tree.children
        return self.visit(a if random.randint(0, 1) else b)

    def random_selection_replacing_unary(self, tree):
        population = self.visit_children(tree)
        if hasattr(population, '__len__'):
            return random.choice(population)
        return population

    def random_selection_replacing_binary(self, tree):
        count, population = self.visit_children(tree)
        return random.choices(population, k=count)

    def random_selection_unary(self, tree):
        return self.random_selection_replacing_unary(tree)

    def random_selection_binary(self, tree):
        count, population = self.visit_children(tree)
        if hasattr(population, '__len__'):
            return random.sample(population, count)
        return [population] * count

    comparisons = {
        '==': operator.eq,
        '!=': operator.ne,
        '>=': operator.ge,
        '>': operator.gt,
        '<': operator.lt,
        '<=': operator.le,
    }

    def compare_math(self, tree):
        children = self.visit_children(tree)
        for i in range(0, len(children)-2, 2):
            left, op, right = children[i:i+3]
            if not self.comparisons[op](left, right):
                return False
        return True

    identity_ops = {'is': lambda a, b: a is b, 'is not': lambda a, b: a is not b}

    @staticmethod
    def identity_op(tree):
        return "is" if len(tree.children) == 1 else "is not"

    def identity(self, tree):
        children = self.visit_children(tree)
        for i in range(0, len(children)-2, 2):
            left, op, right = children[i:i+3]
            if not self.identity_ops[op](left, right):
                return False
        return True

    def member_of(self, tree):
        element, _, collection = self.visit_children(tree)
        return element in collection

    def member_of_negated(self, tree):
        element, _, _, collection = self.visit_children(tree)
        return element not in collection

    def boolean_or(self, tree):
        left, right = tree.children
        if evaluated := self.visit(left):
            return evaluated
        return self.visit(right)

    def boolean_xor(self, tree):
        operands = self.visit_children(tree)
        return any(operands) and not all(operands)

    def boolean_and(self, tree):
        left, right = tree.children
        if evaluated := self.visit(left):
            return self.visit(right)
        return evaluated

    def boolean_not(self, tree):
        return not self.visit(tree.children[0])

    @staticmethod
    def number(tree):
        match (token := tree.children[0]).type:
            case 'LIT_INT_DEC':
                return int(token.value)
            case 'LIT_INT_HEX':
                return int(token.value, 16)
            case 'LIT_REAL':
                return float(token.value)
            case 'LIT_COMPLEX':
                return complex(token.value)
            case 'LIT_NAN':
                return math.nan
            case 'LIT_INF':
                return math.inf
            case _:
                raise BadLiteral(f'unrecognized number: {token!r}')

    @staticmethod
    def string(tree):
        match (literal := tree.children[0]).type:
            case 'LIT_STRING_DOUBLE' | 'LIT_STRING_SINGLE':
                return eval(literal)
            case 'LIT_RAW_DOUBLE' | 'LIT_RAW_SINGLE':
                return literal.value[2:-1]
            case _:
                raise Impossible("unhandled string literal")

    @staticmethod
    def boolean(tree):
        match (token := tree.children[0]).type:
            case 'LIT_TRUE':
                return True
            case 'LIT_FALSE':
                return False
            case _:
                raise BadLiteral(f'unrecognized boolean: {token!r}')

    def sliced(self, tree):
        items, getter = self.visit_children(tree)
        if not hasattr(items, '__getitem__'):
            raise InvalidSubscript(f'{type(items).__name__} cannot be keyed/indexed')
        if not isinstance(getter, Hashable) and not isinstance(getter, slice):
            raise InvalidSubscript(f'{type(getter).__name__} cannot be used to key/index {type(items).__name__}')
        return items[getter]

    @staticmethod
    def whole_slice(_):
        return slice(None, None, None)

    def start_slice(self, tree):
        start, *_ = self.visit_children(tree)
        return slice(start, None, None)

    def start_step_slice(self, tree):
        start, step = self.visit_children(tree)
        return slice(start, None, step)

    def start_stop_slice(self, tree):
        start, stop = self.visit_children(tree)
        return slice(start, stop, None)

    def start_stop_step_slice(self, tree):
        return slice(*self.visit_children(tree))

    def stop_slice(self, tree):
        return slice(self.visit(tree.children[0]))

    def stop_step_slice(self, tree):
        return slice(None, *self.visit_children(tree))

    def step_slice(self, tree):
        return slice(None, None, self.visit(tree.children[0]))

    @staticmethod
    def undefined(_):
        return Undefined

    @staticmethod
    def list_empty(_):
        return []

    def list_populated(self, tree):
        return utils.spread(self.visit_children(tree))

    def list_range(self, tree):
        start, _, stop = self.visit_children(tree)
        step = 1 if start < stop else -1
        return list(range(start, stop, step))

    def list_range_stepped(self, tree):
        start, _, stop, _, step = self.visit_children(tree)
        step = abs(step)
        step = step if start < stop else -step
        return list(range(start, stop, step))

    def list_closed(self, tree):
        start, _, stop = self.visit_children(tree)
        step = 1 if (up := (start < stop)) else -1
        return list(range(start, stop + step if up else stop - step, step))

    def list_closed_stepped(self, tree):
        start, _, stop, _, step = self.visit_children(tree)
        step = abs(step)
        step = step if (up := (start < stop)) else -step
        return list(range(start, stop + step if up else stop - step, step))

    def tuple_single(self, tree):
        return tuple(x.items) if isinstance(x := self.visit(tree.children[0]), Spread) else (x,)

    def tuple_multi(self, tree):
        return utils.spread(self.visit_children(tree), into=tuple)

    def set_populated(self, tree):
        return utils.spread(self.visit_children(tree), into=set)

    def spread_unpackable(self, tree):
        items = self.visit(tree.children[0])
        if not isinstance(items, Iterable):
            raise SpreadError(f"Value after * must be iterable, not {type(items).__name__}")
        return Spread(items)

    @staticmethod
    def parameter(tree):
        return utils.Parameter(str(tree.children[0]))

    @staticmethod
    def parameter_starred(tree):
        return utils.Parameter(str(tree.children[-1]), starred=True)

    def function(self, tree):
        closure = self.call_stack.freeze()
        return UserFunction.from_ast(self, tree, closure)

    @staticmethod
    def tuple_empty(_):
        return ()

    @staticmethod
    def dict_empty(_):
        return {}

    def dict_populated(self, tree):
        pairs = {}
        for child in tree.children:
            key, value = self.visit_children(child)
            pairs[key] = value
        return pairs

    def subscript_bracket(self, tree):
        bracketed = self.visit(tree.children[0])
        if isinstance(bracketed, slice):
            return Accessor.slice(bracketed)
        return Accessor.key(bracketed)

    def subscript_dot(self, tree):
        return Accessor.attr(self.visit(tree.children[0])[1])

    def subscript_chain(self, tree):
        return self.visit_children(tree)

    def access(self, tree):
        name, *accessors = self.visit_children(tree)
        match name:
            case (IdentType.SCOPED, x):
                action = Lookup.scoped
            case (IdentType.USER, x):
                action = Lookup.user
            case (IdentType.SERVER, x):
                action = Lookup.server
            case (IdentType.PUBLIC, x):
                action = Lookup.public
            case _:
                raise Impossible(f"can't retrieve: {name!r} {accessors!r}")

        return action(self.call_stack, self.owner, x, *accessors)

    def retrieval(self, tree):
        return self.visit(tree.children[0]).get()

    def retrieval_atomic(self, tree):
        target, subscripts = self.visit_children(tree)
        last = Undefined
        for accessor in subscripts:
            last = target
            target = accessor.get(target)
        if isinstance(target, UserFunction):
            target.this = last
            return target
        if inspect.ismethod(target):
            return partialmethod(target, last)
        return target

    def function_call(self, tree):
        callee, *arguments = self.visit_children(tree)
        arguments = arguments[0] if arguments else ()
        if isinstance(callee, UserFunction):
            return callee(self, *arguments)
        return callee(*arguments)

    def arguments(self, tree):
        return self.visit_children(tree)

    @staticmethod
    def scoped_identifier(tree):
        return IdentType.SCOPED, str(tree.children[0])

    @staticmethod
    def user_identifier(tree):
        return IdentType.USER, str(tree.children[1])

    @staticmethod
    def server_identifier(tree):
        return IdentType.SERVER, str(tree.children[1])

    @staticmethod
    def public_identifier(tree):
        return IdentType.PUBLIC, str(tree.children[1])

    augments = {'+=': operator.iadd, '-=': operator.isub, '$=': ops.icat,
                '*=': operator.imul, '/=': operator.itruediv, '//=': operator.ifloordiv,
                '%=': operator.imod, '**=': operator.ipow, '<<=': operator.ilshift,
                '>>=': operator.irshift, '&=': operator.iand, '|=': operator.ior,
                '^=': operator.ixor, 'and=': ops.iand, 'xor=': ops.ixor,
                'or=': ops.ior}

    def augmented_any(self, tree):
        target, op, augment = self.visit_children(tree)
        return target.put(self.augments[op](target.get(), augment))

    def assignment_single(self, tree):
        lval, _, rval = self.visit_children(tree)
        return lval.put(rval)

    def assignment_multi(self, tree):
        lvals, rvals = utils.split(self.visit_children(tree), "=")
        if (llen := len(lvals)) > (rlen := len(rvals)):
            raise AssignmentError(f"more assignment targets {llen} than values {rlen}")
        elif llen < rlen:
            raise AssignmentError(f"fewer assignment targets {llen} than values {rlen}")
        return [lval.put(rval) for lval, rval in zip(lvals, rvals)]

    def assignment_unpack_left(self, tree):
        operands = self.visit_children(tree)
        lvals, rval = operands[1:-2], operands[-1]
        if not utils.isordered(rval):
            raise UnpackError(f"can't unpack from {rval.__class__.__name__}")
        if (act := len(rval)) < (exp := len(lvals) - 1):
            raise UnpackError(f'expected at least {exp} values to unpack, but got {act}')
        starred, individual = lvals[0], lvals[1:]
        start = len(rval) - 1
        end = start - (ilen := len(individual))
        backwards = [individual[-j].put(rval[i]) for i, j in zip(range(start, end, -1), range(1, ilen+1))]
        packed = starred.put(rval[:end+1])
        return tuple(itertools.chain([packed], reversed(backwards)))

    def assignment_unpack_middle(self, tree):
        operands = self.visit_children(tree)
        lvals, rval = operands[0:-2], operands[-1]
        if not utils.isordered(rval):
            raise UnpackError(f"can't unpack from {rval.__class__.__name__}")
        if (act := len(rval)) < (exp := len(lvals) - 1):
            raise UnpackError(f'expected at least {exp} values to unpack, but got {act}')
        head, rest = utils.split(lvals, "*")
        starred, tail = rest[0], rest[1:]
        hc, tc = len(head), len(tail)
        hvals, svals, tvals = rval[:hc], rval[hc:-tc], rval[-tc:]
        hout = [left.put(right) for left, right in zip(head, hvals)]
        tout = [left.put(right) for left, right in zip(tail, tvals)]
        sout = starred.put(svals)
        return tuple(itertools.chain(hout, [sout], tout))

    def assignment_unpack_right(self, tree):
        operands = self.visit_children(tree)
        lvals, rval = operands[0:-2], operands[-1]
        if not utils.isordered(rval):
            raise UnpackError(f"can't unpack from {rval.__class__.__name__}")
        if (act := len(rval)) < (exp := len(lvals) - 1):
            raise UnpackError(f'expected at least {exp} values to unpack, but got {act}')
        individual, starred = utils.split(lvals, "*")
        end = len(individual)
        forwards = [individual[i].put(rval[i]) for i in range(end)]
        packed = starred[0].put(rval[end:])
        return tuple(itertools.chain(forwards, [packed]))

    def assignment_unpack(self, tree):
        operands = self.visit_children(tree)
        lvals, rval = operands[0:-2], operands[-1]
        if not utils.isordered(rval):
            raise UnpackError(f"can't unpack from {rval.__class__.__name__}")
        if (act := len(rval)) < (exp := len(lvals)):
            raise UnpackError(f'expected {exp} values to unpack, but got {act}')
        return tuple(left.put(right) for left, right in zip(lvals, rval))

    def __default__(self, tree):
        return self.visit(tree.children[0])

    def deletion(self, tree):
        deleted = tuple(target.drop() for target in self.visit_children(tree)[1:])
        if len(deleted) == 1:
            return deleted[0]
        return deleted

    def keyword(self, tree):
        evaluated = self.visit_children(tree)
        try:
            keyword, value = evaluated
        except ValueError:
            keyword, value = evaluated, Empty
        match sig := keyword.type:
            case 'KW_CONTINUE':
                raise Continue(value)
            case 'KW_BREAK':
                raise Break(value)
            case 'KW_RETURN':
                raise Return(value)
            case 'KW_TERMINATE':
                raise Terminate(value)
            case _:
                raise Impossible(f'unknown signal: {sig}')
