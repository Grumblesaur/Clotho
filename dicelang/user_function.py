from copy import deepcopy
from collections import Counter
from dicelang.exceptions import BadArguments, Break, Continue, DuplicateParameter, IllegalSignal, Return
from dicelang.parser import parser
from dicelang.reconstructor import DicelangReconstructor
from dicelang.special import Undefined
from dicelang.utils import is_sorted


class UserFunction:
    reconstructor = DicelangReconstructor()

    @classmethod
    def reconstruct(cls, code):
        return cls.reconstructor.visit(code)

    def __init__(self, code_string, closed_over=None):
        ast = parser.parse(code_string, start='function')
        *self.params, self.code = ast.children
        self.required = len(self.params) - sum(p.is_default() for p in self.params)
        self.normalize()
        self.this = Undefined
        self.closed_over = closed_over or [{}]
        self.source = f'({", ".join(self.params)}) -> {code_string}'

    def __repr__(self):
        return self.source

    def serialization(self):
        return f'{self.__class__.__name__}({self.source, self.closed_over})'

    @classmethod
    def from_ast(cls, interpreter, tree, closed_over=None):
        self = object.__new__(cls)
        self.code = tree.children[-1]
        self.params = [interpreter.visit(c) for c in tree.children[:-1]]
        self.normalize() and self.validate()
        self.required = len(self.params) - sum(p.is_default() for p in self.params)
        self.closed_over = closed_over or [{}]
        self.this = Undefined
        self.source = cls.reconstruct(tree)
        return self

    def __deepcopy__(self, *args, **kwargs):
        newtree = type(self.code)(deepcopy(self.code.data), deepcopy(self.code.children))
        return self.from_ast(newtree, self.params[:], deepcopy(self.closed_over))

    def validate(self):
        if not self.params:
            return True
        if not is_sorted([p.is_default() for p in self.params]):
            raise BadArguments('all keyword arguments must follow positional arguments')
        return True

    def normalize(self):
        for p, c in Counter(str(p) for p in self.params).items():
            if c > 1:
                raise DuplicateParameter(repr(p))
        return True

    def marshal(self, *positional, **keyword):
        marshalled = {}
        positionals = len(positional)
        used = 0
        for param in self.params:
            if param.is_default():
                if param in keyword:
                    marshalled[param.name] = keyword[param.name]
                elif used < positionals:
                    marshalled[param.name] = positional[used]
                    used += 1
                else:
                    marshalled[param.name] = param.default
            else:
                if used >= positionals:
                    raise BadArguments(f'invalid number of positional arguments')
                marshalled[param.name] = positional[used]
                used += 1
        return marshalled

    def __call__(self, interpreter, *args):
        arguments = {'this': self.this}
        arguments.update(self.marshal(*args))
        interpreter.call_stack.function_push(arguments, self.closed_over)
        try:
            out = interpreter.visit(self.code.children[0])
        except Return as rs:
            out = rs.unwrap()
        except (Break, Continue) as e:
            raise IllegalSignal(f'{e.__class__.__name__} used outside of flow control context')
        interpreter.call_stack.function_pop()
        return out
