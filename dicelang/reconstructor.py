from lark.visitors import Interpreter
from dicelang.exceptions import Impossible

import dicelang.utils


class DicelangReconstructor(Interpreter):
    def __init__(self, indent='    '):
        self.level = 0
        self.indent = indent

    def __default__(self, tree):
        return self.visit(tree.children[0])

    @staticmethod
    def scoped_identifier(tree):
        return tree.children[0].value

    @staticmethod
    def user_identifier(tree):
        return f'my {tree.children[-1].value}'

    @staticmethod
    def server_identifier(tree):
        return f'our {tree.children[-1].value}'

    @staticmethod
    def public_identifier(tree):
        return f'public {tree.children[-1].value}'

    def priority(self, tree):
        return f'({self.visit(tree.children[0])})'

    def block(self, tree):
        self.level += 1
        begin, *segments, end = self.visit_children(tree)
        indent, endent = self.indent * self.level, self.indent * (self.level - 1)
        body = indent + f';\n{indent}'.join(segments)
        self.level -= 1
        return f'{begin}\n{body}\n{endent}{end}'

    def if_block(self, tree):
        return ' '.join(self.visit_children(tree))

    def if_else_block(self, tree):
        return ' '.join(self.visit_children(tree))

    def while_loop(self, tree):
        return ' '.join(self.visit_children(tree))

    def do_while_loop(self, tree):
        return ' '.join(self.visit_children(tree))

    def for_loop(self, tree):
        return ' '.join(self.visit_children(tree))

    def keyword(self, tree):
        match tree.children:
            case [x]:
                return str(x)
            case [x, y]:
                return f'{x} {self.visit(y)}'
            case _:
                raise Impossible(f'unknown control flow: {tree.children}')

    def subscript_chain(self, tree):
        return ''.join(self.visit_children(tree))

    def subscript_bracket(self, tree):
        return f'[{self.visit(tree.children[0])}]'

    def subscript_dot(self, tree):
        return f'.{self.visit(tree.children[0])}'

    def index_or_key(self, tree):
        return self.visit(tree.children[0])

    @staticmethod
    def whole_slice(_):
        return ':'

    def start_slice(self, tree):
        return f'{self.visit(tree.children[0])}:'

    def start_step_slice(self, tree):
        start, step = self.visit_children(tree)
        return f'{start}::{step}'

    def start_stop_slice(self, tree):
        start, stop = self.visit_children(tree)
        return f'{start}:{stop}'

    def start_stop_step_slice(self, tree):
        start, stop, step = self.visit_children(tree)
        return f'{start}:{stop}:{step}'

    def stop_slice(self, tree):
        return f':{self.visit(tree.children[0])}'

    def stop_step_slice(self, tree):
        stop, step = self.visit_children(tree)
        return f':{stop}:{step}'

    def step_slice(self, tree):
        return f'::{self.visit(tree.children[0])}'

    def assignment_single(self, tree):
        return ' '.join(self.visit_children(tree))

    def assignment_unpack(self, tree):
        segments = self.visit_children(tree)
        left, right = utils.split(segments, '=')
        lvals = ', '.join(left)
        rval = right[0]
        return f'{lvals} = {rval}'

    def assignment_unpack_left(self, tree):
        segments = self.visit_children(tree)
        left, right = utils.split(segments, '=')
        lvals = ', '.join(left)
        rval = right[0]
        return f'*{lvals} = {rval}'

    def assignment_unpack_middle(self, tree):
        segments = self.visit_children(tree)
        left, right = utils.split(segments, '=')
        head, tail = utils.split(left, "*")
        middle, tail = tail[0], tail[1:]
        leading = ', '.join(head)
        middle = f'*{middle}'
        trailing = ', '.join(tail)
        rval = right[0]
        lvals = ', '.join([leading, middle, trailing])
        return f'{lvals} = {rval}'

    def assignment_unpack_right(self, tree):
        segments = self.visit_children(tree)
        left, right = utils.split(segments, '=')
        individual, starred = utils.split(left, '*')
        leading = ', '.join(individual)
        starred = f'*{starred[0]}'
        lvals = f'{leading}, {starred}'
        rval = right[0]
        return f'{lvals} = {rval}'

    def augmented(self, tree):
        return ' '.join(self.visit_children(tree))

    def function(self, tree):
        *parameters, body = self.visit_children(tree)
        signature = ', '.join(parameters)
        return f'({signature}) -> {body}'

    @staticmethod
    def parameter(tree):
        return tree.children[0].value

    @staticmethod
    def parameter_starred(tree):
        return f'*{tree.children[-1].value}'

    def if_ternary(self, tree):
        return ' '.join(self.visit_children(tree))

    def repeat(self, tree):
        return ' '.join(self.visit_children(tree))

    def boolean_or(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} or {right}'

    def boolean_xor(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} xor {right}'

    def boolean_and(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} and {right}'

    def boolean_not(self, tree):
        return ' '.join(self.visit_children(tree))

    def compare_math(self, tree):
        return ' '.join(self.visit_children(tree))

    def identity(self, tree):
        return ' '.join(self.visit_children(tree))

    def member_of(self, tree):
        return ' '.join(self.visit_children(tree))

    def member_of_negated(self, tree):
        return ' '.join(self.visit_children(tree))

    def bit_or(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} | {right}'

    def bit_xor(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} ^ {right}'

    def bit_and(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} & {right}'

    def bit_not(self, tree):
        return f'~{self.visit(tree.children[0])}'

    def addition(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} + {right}'

    def subtraction(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} - {right}'

    def catenation(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} $ {right}'

    def multiplication(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} * {right}'

    def division(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} / {right}'

    def integer_division(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} // {right}'

    def remainder(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} % {right}'

    def left_shift(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} << {right}'

    def right_shift(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} >> {right}'

    def unary_minus(self, tree):
        return f'-{self.visit(tree.children[0])}'

    def unary_plus(self, tree):
        return f'+{self.visit(tree.children[0])}'

    def exponent(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} ** {right}'

    def sum_or_join(self, tree):
        return f'&{self.visit(tree.children[0])}'

    def len_or_mag(self, tree):
        return f'#{self.visit(tree.children[0])}'

    def coinflip(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} ! {right}'

    def random_selection_replacing_unary(self, tree):
        return f'@{self.visit(tree.children[0])}'

    def random_selection_replacing_binary(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} @ {right}'

    def random_selection_unary(self, tree):
        return f'@!{self.visit(tree.children[0])}'

    def random_selection_binary(self, tree):
        left, right = self.visit_children(tree)
        return f'{left} @! {right}'

    def die_unary(self, tree):
        return ' '.join(self.visit_children(tree))

    def die_binary(self, tree):
        return ' '.join(self.visit_children(tree))

    def die_ternary_high(self, tree):
        return ' '.join(self.visit_children(tree))

    def die_ternary_low(self, tree):
        return ' '.join(self.visit_children(tree))

    def roll_unary(self, tree):
        return ' '.join(self.visit_children(tree))

    def roll_binary(self, tree):
        return ' '.join(self.visit_children(tree))

    def roll_ternary_high(self, tree):
        return ' '.join(self.visit_children(tree))

    def roll_ternary_low(self, tree):
        return ' '.join(self.visit_children(tree))

    def retrieval_atomic(self, tree):
        left, right = self.visit_children(tree)
        return f'{left}{right}'

    def function_call(self, tree):
        callee, args = self.visit_children(tree)
        return f'{callee}({args})'

    def spread_unpackable(self, tree):
        return f'*{self.visit(tree.children[0])}'

    @staticmethod
    def undefined(_):
        return 'Undefined'

    @staticmethod
    def list_empty(_):
        return '[]'

    def list_populated(self, tree):
        items = ', '.join(self.visit_children(tree))
        return f'[{items}]'

    def list_range_stepped(self, tree):
        items = ' '.join(self.visit_children(tree))
        return f'[{items}]'

    def list_closed(self, tree):
        items = ' '.join(self.visit_children(tree))
        return f'[{items}]'

    def list_closed_stepped(self, tree):
        items = ' '.join(self.visit_children(tree))
        return f'[{items}]'

    @staticmethod
    def string(tree):
        return tree.children[0].value

    @staticmethod
    def boolean(tree):
        return tree.children[0].value

    @staticmethod
    def number(tree):
        return tree.children[0].value

    def tuple_single(self, tree):
        return f'({self.visit(tree.children[0])},)'

    def tuple_multi(self, tree):
        items = ', '.join(self.visit_children(tree))
        return f'({items})'

    @staticmethod
    def tuple_empty(_):
        return ()

    def set_populated(self, tree):
        items = ', '.join(self.visit_children(tree))
        return '{' + items + '}'

    @staticmethod
    def dict_empty(_):
        return {}

    def dict_populated(self, tree):
        return '{' + ', '.join(self.visit_children(tree)) + '}'

    def kv_pair(self, tree):
        key, value = self.visit_children(tree)
        return f'{key}: {value}'


if __name__ == '__main__':
    from parser import parser
    input_ = '''f = (*a) -> begin d a[0] + d a[1] + sum(a[2:]) end'''
    ast = parser.parse(input_)
    dr = DicelangReconstructor()
    output = dr.visit(ast)
    print(output)
