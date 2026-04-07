from copy import deepcopy
from collections import Counter
from dicelang.exceptions import BadArguments, Break, Continue, DuplicateParameter, IllegalSignal, Return
from dicelang.parser import parser
from dicelang.reconstructor import DicelangReconstructor
from dicelang.special import Undefined
from dicelang.utils import is_sorted, Unfilled


class UserFunction:
    """Construct a user-created function specified by Dicelang code."""
    reconstructor = DicelangReconstructor()

    class SerializationManager:
        def __enter__(self):
            UserFunction.__repr__ = UserFunction.alt_repr
            return self

        def __exit__(self, exc_type, exc_value, exc_traceback):
            UserFunction.__repr__ = UserFunction.standard_repr
            # Avoid swallowing exceptions
            if exc_type is not None:
                raise exc_type(exc_value)

    @classmethod
    def reconstruct(cls, code):
        """Recreate the source code of a function from its abstract syntax
        tree. This is used for calls to `repr` (either directly or via the
        `!r` specifier in f-strings) when showing output to the user."""
        return cls.reconstructor.visit(code)

    def __init__(self, code_string, closed_over=None):
        """Construct a user-created function from its source code and the
        scope variables it closes over."""
        ast = parser.parse(code_string)
        *self.params, self.code = ast.children
        self.required = len(self.params) - sum(p.is_default() for p in self.params)
        self.validate()
        self.this = Undefined
        self.closed_over = closed_over or [{}]
        self.source = f'({", ".join(self.params)}) -> {code_string}'

    def standard_repr(self):
        return self.source

    __repr__ = standard_repr

    def alt_repr(self):
        return f'{self.__class__.__name__}({self.source!r}, {self.closed_over!r})'

    def __enter__(self):
        self.__repr__ = self.alt_repr

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.__repr__ = self.standard_repr

    @classmethod
    def from_ast(cls, interpreter, tree, closed_over=None):
        """Initialize a function from its abstract syntax tree."""
        self = object.__new__(cls)
        self.code = tree.children[-1]
        self.params = [interpreter.visit(c) for c in tree.children[:-1]]
        self.validate()
        self.required = len(self.params) - sum(p.is_default() for p in self.params)
        self.closed_over = closed_over or [{}]
        self.this = Undefined
        self.source = cls.reconstruct(tree)
        return self

    def __deepcopy__(self, *args, **kwargs):
        newtree = type(self.code)(deepcopy(self.code.data), deepcopy(self.code.children))
        return self.from_ast(newtree, self.params[:], deepcopy(self.closed_over))

    def validate(self):
        """Ensure that all parameters without default arguments precede all
        parameters with default arguments. Disallow duplicate parameter names."""
        if not self.params:
            return True
        if not is_sorted([p.is_default() for p in self.params]):
            raise BadArguments('all keyword arguments must follow positional arguments')
        for p, c in Counter(str(p) for p in self.params).items():
            if c > 1:
                raise DuplicateParameter(repr(p))
        return True

    def marshal(self, *positional):
        """Given a set of arguments, assign them to parameter names."""
        marshalled = {}
        positionals = len(positional)
        used = 0
        for param in self.params:
            if param.is_default():
                if used < positionals:
                    marshalled[param.name] = positional[used]
                    used += 1
                else:
                    marshalled[param.name] = param.default
            else:
                if used >= positionals:
                    raise BadArguments(f'Got {used} positional arguments, expected {positionals}')
                marshalled[param.name] = positional[used]
                used += 1
        if (n_unfilled := Counter(marshalled.values())[Unfilled]) > 0:
            n_args = len(marshalled)
            raise BadArguments(f'Got {n_args - n_unfilled} arguments, expected {n_args}')
        return marshalled

    def __call__(self, interpreter, *args):
        """Execute the function with the passed arguments and the current
        interpreter state."""
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
