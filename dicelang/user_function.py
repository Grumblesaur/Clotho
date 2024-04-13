from copy import deepcopy

from dicelang.exceptions import BadArguments, Break, Continue, DuplicateParameter, IllegalSignal, Return
from dicelang.parser import parser
from dicelang.reconstructor import DicelangReconstructor
from dicelang.special import Undefined


class UserFunction:
    reconstructor = DicelangReconstructor()

    @classmethod
    def reconstruct(cls, code):
        return cls.reconstructor.visit(code)

    def __init__(self, code_string, closed_over=None):
        ast = parser.parse(code_string, start='function')
        *self.params, self.code = ast.children
        self.normalize()
        self.this = Undefined
        self.closed_over = closed_over or [{}]
        self.variadic = bool(self.params) and self.params[-1].starred
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
        self.variadic = bool(self.params) and self.params[-1].starred
        self.normalize()
        self.closed_over = closed_over or [{}]
        self.this = Undefined
        self.source = cls.reconstruct(tree)
        return self

    def __deepcopy__(self, *args, **kwargs):
        newtree = type(self.code)(deepcopy(self.code.data), deepcopy(self.code.children))
        return self.from_ast(newtree, self.params[:], deepcopy(self.closed_over))

    def normalize(self):
        self.params = tuple(str(p) for p in self.params)
        last = None
        for p in sorted(self.params):
            if p == last:
                raise DuplicateParameter(repr(p))

    def marshal(self, *args):
        if not self.variadic:
            if (exp := len(self.params)) != (act := len(args)):
                raise BadArguments(f'function call expected {exp} arguments, but got {act}')
            return dict(zip((str(p) for p in self.params), args))
        if (exp := len(self.params) - 1) > (act := len(args)):
            raise BadArguments(f'function call requires at least {exp} arguments, but got {act}')
        head, rest = args[:exp], args[exp:]
        marshaled = dict(zip((str(p) for p in self.params[:-1]), head))
        marshaled[str(self.params[-1])] = tuple(rest)
        return marshaled

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
