import traceback
from copy import deepcopy
from collections import Counter
from dicelang.exceptions import BadArguments, BadParameters, Break, Continue, DuplicateParameter, IllegalSignal, Return
from dicelang.parser import DicelangParser
from dicelang.reconstructor import DicelangReconstructor
from dicelang.special import Undefined
from dicelang.utils import is_sorted, Unfilled


class UserFunction:
    """Construct a user-created function specified by Dicelang code."""
    reconstructor = DicelangReconstructor()
    interpreter = None
    parser = DicelangParser(start='function')

    class SerializationManager:
        def __enter__(self):
            UserFunction.__repr__ = UserFunction.alt_repr
            return self

        def __exit__(self, exc_type, exc_value, exc_traceback):
            UserFunction.__repr__ = UserFunction.standard_repr
            # Avoid swallowing exceptions
            if exc_type is not None:
                traceback.print_exception(exc_type, exc_value, exc_traceback)
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
        ast = self.parser.parse(code_string)
        *params, self.code = ast.children
        self.params = [self.interpreter.visit(p) for p in params]
        self.required = len(self.params) - sum(p.is_default() for p in self.params)
        self.validate()
        self.this = Undefined
        self.closed_over = closed_over or [{}]
        self.source = code_string

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
        if cls.interpreter is None:
            cls.interpreter = interpreter
        self = object.__new__(cls)
        self.code = tree.children[-1]
        self.params = [cls.interpreter.visit(c) for c in tree.children[:-1]]
        self.validate()
        self.required = len(self.params) - sum(p.is_default() for p in self.params)
        self.closed_over = closed_over or [{}]
        self.this = Undefined
        self.source = cls.reconstruct(tree)
        return self

    def __deepcopy__(self, *args, **kwargs):
        new = object.__new__(self.__class__)
        new.code = deepcopy(self.code)
        new.params = deepcopy(self.params)
        new.required = self.required
        new.closed_over = deepcopy(self.closed_over)
        new.this = self.this
        new.source = deepcopy(self.source)
        return new

    def validate(self):
        """Ensure that all parameters without default arguments precede all
        parameters with default arguments. Disallow duplicate parameter names."""
        if not self.params:
            return True
        if not is_sorted([p.is_default() for p in self.params]):
            raise BadParameters('all keyword arguments must follow positional arguments')
        for p, c in Counter(str(p) for p in self.params).items():
            if c > 1:
                raise DuplicateParameter(repr(p))
        return True

    def marshal(self, *pos_args, **named_args):
        """Given a set of arguments, assign them to parameter names."""
        pos_args = list(pos_args)
        pos_params = [p for p in self.params if not p.is_default()]
        named_params = [p for p in self.params if p.is_default()]

        if (n_pargs := len(pos_args)) < (n_pparams := len(pos_params)):
            raise BadArguments(f'{n_pargs} positional arguments passed'
                                + f' to function with {n_pparams} positional parameter(s)')

        if (n_args := len(pos_args) + len(named_args)) > (n_params := len(pos_params) + len(named_params)):
            raise BadArguments(f'expected {n_params} total arguments; got {n_args}')

        while len(pos_args) > len(pos_params): # Some of our keyword arguments are being filled positionally
            pos_params.append(named_params.pop(0))

        marshalled = {pp.name: pa.value for pp, pa in zip(pos_params, pos_args)}
        marshalled.update(named_params := {np.name: np.default for np in named_params})
        for name, value in named_args.items():
            if name not in named_params:
                raise BadArguments(f'argument {name} does not exist or was filled positionally')
            marshalled[name] = value
        return marshalled

    def __call__(self, interpreter, *args, **kwargs):
        """Execute the function with the passed arguments and the current
        interpreter state."""
        arguments = {'self': self.this}
        arguments.update(self.marshal(*args, **kwargs))
        interpreter.call_stack.function_push(arguments, self.closed_over)
        if self.interpreter is None:
            self.__class__.interpreter = interpreter
        try:
            out = interpreter.visit(self.code.children[0])
        except Return as rs:
            out = rs.unwrap()
        except (Break, Continue) as e:
            raise IllegalSignal(f'{e.__class__.__name__} used outside of flow control context')
        interpreter.call_stack.function_pop()
        return out
