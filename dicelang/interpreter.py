import dicecore
import statistics
import utils
import random
import operator
import re
import math
import itertools
import more_itertools
from special import Undefined, Spread
from call_stack import CallStack
from collections.abc import Iterable, Sequence
from typing import Hashable
from numbers import (Real, Complex, Integral, Number)
from lark.visitors import Interpreter
from math import log, log10, ceil
from identifier import Lookup, Accessor, IdentType
from exceptions import (
    LiteralError, SpreadError,
    SubscriptError,
)


class DicelangInterpreter(Interpreter):
    def __init__(self, call_stack=None):
        self.call_stack = call_stack or CallStack()

    def block(self, tree):
        self.call_stack.scope_push()
        result = self.visit_children(tree)[-1]
        self.call_stack.scope_pop()
        return result

    def if_block(self, tree):
        _, condition, _, body = tree.children
        return self.visit(body) if self.visit(condition) else Undefined

    def if_else_block(self, tree):
        _, condition, _, if_body, _, else_body = tree.children
        return self.visit(if_body) if self.visit(condition) else self.visit(else_body)

    def while_loop(self, tree):
        _, condition, _, body = tree.children
        results = []
        while self.visit(condition):
            results.append(self.visit(body))
        return results

    def do_while_loop(self, tree):
        _, body, _, condition = tree.children
        results = [self.visit(body)]
        while self.visit(condition):
            results.append(self.visit(body))
        return results

    def start(self, tree):
        return self.visit_children(tree)[-1]

    def if_ternary(self, tree):
        if_action, _, condition, _, else_action = tree.children
        if self.visit(condition):
            return self.visit(if_action)
        return self.visit(else_action)

    def if_binary(self, tree):
        condition_action, _, _, else_action = tree.children
        if yes := self.visit(condition_action):
            return yes
        return self.visit(else_action)

    def repetition(self, tree):
        repeats = self.visit(tree.children[2])
        return [self.visit(tree.children[0]) for _ in range(repeats)]

    def die_unary(self, tree):
        _, sides = self.visit_children(tree)
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
        _, sides = self.visit_children(tree)
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
        mantissa, _, superscript = self.visit_children(tree)
        return mantissa ** superscript

    def logarithm(self, tree):
        base, _, antilogarithm = self.visit_children(tree)
        return log(antilogarithm, base)

    def unary_minus(self, tree):
        _, operand = self.visit_children(tree)
        if isinstance(operand, Sequence):
            return operand[::-1]
        return -operand

    def unary_plus(self, tree):
        _, operand = self.visit_children(tree)
        return +operand

    def multiplication(self, tree):
        multiplier, _, multiplicand = self.visit_children(tree)
        if isinstance(multiplier, int) and isinstance(multiplicand, Sequence):
            direction = utils.sign(multiplier)
            return multiplicand[::direction] * multiplier
        elif isinstance(multiplier, Sequence) and isinstance(multiplicand, int):
            direction = utils.sign(multiplicand)
            return multiplier[::direction] * multiplicand
        return multiplier * multiplicand

    def division(self, tree):
        dividend, _, divisor = self.visit_children(tree)
        if isinstance(dividend, (list, tuple)):
            if not isinstance(divisor, str) and isinstance(divisor, Iterable):
                return type(dividend)(x for x in dividend if x not in divisor)
            else:
                return type(dividend)(x for x in dividend if x != divisor)
        if isinstance(dividend, str) and isinstance(divisor, str):
            return dividend.replace(divisor, '')
        return dividend / divisor

    def integer_division(self, tree):
        dividend, _, divisor = self.visit_children(tree)
        return dividend // divisor

    def left_shift(self, tree):
        bits, _, shift = self.visit_children(tree)
        if isinstance(bits, (list, tuple)):
            return bits + type(bits)([shift])
        elif isinstance(bits, str):
            return bits + str(shift)
        return bits << shift

    def right_shift(self, tree):
        bits, _, shift = self.visit_children(tree)
        if isinstance(bits, (list, tuple)):
            return type(bits)([shift]) + bits
        elif isinstance(bits, str):
            return str(shift) + bits
        return bits >> shift

    def remainder(self, tree):
        dividend, _, divisor = self.visit_children(tree)
        return dividend % divisor

    def addition(self, tree):
        addend, _, augend = self.visit_children(tree)
        if isinstance(addend, dict) and isinstance(augend, dict):
            return {**addend, **augend}
        if utils.isvector(addend) and utils.isvector(augend):
            return type(addend)(itertools.chain(addend, augend))
        return addend + augend

    def subtraction(self, tree):
        minuend, _, subtrahend = self.visit_children(tree)
        # For list-y minuends, remove the first instance of each element
        # in subtrahend (or subtrahend itself it it's not a container)
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
        elif isinstance(minuend, str) and isinstance(subtrahend, str):
            return minuend.replace(subtrahend, '', 1)
        return minuend - subtrahend

    def catenation(self, tree):
        high_order, _, low_order = self.visit_children(tree)
        return int(f'{int(high_order)}{int(low_order)}')

    def bit_and(self, tree):
        left, _, right = self.visit_children(tree)
        return left & right

    def bit_xor(self, tree):
        left, _, right = self.visit_children(tree)
        return left ^ right

    def bit_or(self, tree):
        left, _, right = self.visit_children(tree)
        return left | right

    def bit_not(self, tree):
        _, operand = self.visit_children(tree)
        if isinstance(operand, Complex):
            return operand.conjugate()
        return ~operand

    def sum_or_join(self, tree):
        _, operand = self.visit_children(tree)
        if isinstance(operand, Iterable) and not isinstance(operand, str):
            return utils.vector_sum(operand)
        elif isinstance(operand, Complex):
            return operand.imag
        return operand

    def len_or_mag(self, tree):
        _, operand = self.visit_children(tree)
        if hasattr(operand, '__len__'):
            return len(operand)
        elif isinstance(operand, Complex):
            return abs(operand)
        elif isinstance(operand, (Integral, Real)):
            return ceil(log10(operand))
        return 0

    def max_unary(self, tree):
        _, operand = self.visit_children(tree)
        return max(operand)

    def min_unary(self, tree):
        _, operand = self.visit_children(tree)
        return min(operand)

    def max_binary(self, tree):
        a, _, b = self.visit_children(tree)
        return max(a, b)

    def min_binary(self, tree):
        a, _, b = self.visit_children(tree)
        return min(a, b)

    def coinflip(self, tree):
        a = tree.children[0]
        b = tree.children[2]
        return self.visit(a if random.randint(0, 1) else b)

    def random_selection_replacing_unary(self, tree):
        _, population = self.visit_children(tree)
        if hasattr(population, '__len__'):
            return random.choice(population)
        return population

    def random_selection_replacing_binary(self, tree):
        count, _, population = self.visit_children(tree)
        return random.choices(population, k=count)

    def random_selection_unary(self, tree):
        return self.random_selection_replacing_unary(tree)

    def random_selection_binary(self, tree):
        count, _, population = self.visit_children(tree)
        if hasattr(population, '__len__'):
            return random.sample(population, count)
        return [population] * count

    def sorted(self, tree):
        _, operand = self.visit_children(tree)
        if isinstance(operand, Iterable):
            return sorted(operand)
        return operand

    def shuffled(self, tree):
        _, operand = self.visit_children(tree)
        if isinstance(operand, Iterable):
            new = list(operand)
            random.shuffle(new)
            return new
        return operand

    def statistics(self, tree):
        _, operand = self.visit_children(tree)
        if isinstance(operand, Number):
            operand = [operand]
        elif isinstance(operand, dict):
            operand = list(operand.values())
        out = {'average': statistics.mean(operand), 'minimum': min(operand), 'maximum': max(operand),
               'median': statistics.median(operand), 'size': len(operand), 'sum': sum(operand)}
        out['stddev'] = statistics.pstdev(operand, out['average'])
        out['q1'] = statistics.median(x for x in operand if x < out['median'])
        out['q3'] = statistics.median(x for x in operand if x > out['median'])
        return out

    def floor_or_flatten(self, tree):
        operand = self.visit(tree.children[1])
        if isinstance(operand, Iterable) and not isinstance(operand, str):
            return list(more_itertools.collapse(operand))
        if isinstance(operand, float):
            return math.floor(operand)
        return operand

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
        left, _, right = tree.children
        if evaluated := self.visit(left):
            return evaluated
        return self.visit(right)

    def boolean_xor(self, tree):
        left, _, right = self.visit_children(tree)
        items = left, right
        return any(items) and not all(items)

    def boolean_and(self, tree):
        left, _, right = tree.children
        if evaluated := self.visit(left):
            return self.visit(right)
        return evaluated

    def boolean_not(self, tree):
        return not self.visit(tree.children[1])

    def regex_search(self, tree):
        subject, _, pattern = self.visit_children(tree)
        if match := re.search(pattern, subject):
            return {'start': match.start(), 'end': match.end()}
        return {}

    def regex_match(self, tree):
        subject, _, pattern = self.visit_children(tree)
        return bool(re.match(pattern, subject))

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
                raise LiteralError(f'unrecognized number: {token!r}')

    @staticmethod
    def string(tree):
        return eval(tree.children[0].value)

    @staticmethod
    def boolean(tree):
        match (token := tree.children[0]).type:
            case 'LIT_TRUE':
                return True
            case 'LIT_FALSE':
                return False
            case _:
                raise LiteralError(f'unrecognized boolean: {token!r}')

    def sliced(self, tree):
        items, getter = self.visit_children(tree)
        if not hasattr(items, '__getitem__'):
            raise SubscriptError(f'{items.__class__.__name__} cannot be keyed/indexed')

        if not isinstance(getter, Hashable) and not isinstance(getter, slice):
            raise SubscriptError(f'{getter.__class__.__name__} cannot be used to key/index {items.__class__.__name__}')

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

    def retrieval(self, tree):
        name, *subscripts = self.visit_children(tree)
        accessors = []
        for sub in subscripts:
            match sub:
                case (IdentType.SCOPED, attr):
                    accessors.append(Accessor.attr(attr))
                case _:
                    accessors.append(Accessor.slice(sub))
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
                raise NotImplementedError(f'impossible retrieval: {name!r} {subscripts!r}')

        lookup = action(self.call_stack, x, *accessors)
        return lookup.get()

    def function_call(self, tree):
        callee, *arguments = self.visit_children(tree)
        return callee(*arguments)

    @staticmethod
    def scoped_identifier(tree):
        return IdentType.SCOPED, str(tree.children[0])

    @staticmethod
    def user_identifier(tree):
        return IdentType.USER, str(tree.children[0])

    @staticmethod
    def server_identifier(tree):
        return IdentType.SERVER, str(tree.children[0])

    @staticmethod
    def public_identifier(tree):
        return IdentType.PUBLIC, str(tree.children[0])

    def __default__(self, tree):
        return self.visit(tree.children[0])


if __name__ == '__main__':
    from parser import parser
    di = DicelangInterpreter()
    tests = "set('abc'); math.sin(math.pi / 2); frozenset([1, 2, 3]); math".split(';')
    for t in tests:
        ast = parser.parse(t)
        output = di.visit(ast)
        print(output)