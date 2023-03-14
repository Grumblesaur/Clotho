from parser import parser
from special import Undefined
from exceptions import DuplicateArgument
from copy import deepcopy


class UserFunction:
    def __init__(self, code_string, closed_over=None):
        ast = parser.parse(code_string, start='function')
        *self.params, self.code = ast.children
        self.this = Undefined
        self.closed_over = closed_over or [{}]
        self.normalize()

    @classmethod
    def from_ast(cls, code, params, closed_over=None):
        self = object.__new__(cls)
        self.code = code
        self.params = params
        self.closed_over = closed_over or [{}]

    def __deepcopy__(self, *args, **kwargs):
        newtree = type(self.code)(deepcopy(self.code.data), deepcopy(self.code.children))
        return self.from_ast(newtree, self.params[:], deepcopy(self.closed_over))

    def normalize(self):
        self.params = tuple(str(p) for p in self.params)
        last = None
        for p in sorted(self.params):
            if p == last:
                raise DuplicateArgument(repr(p))

    def __call__(self, interpreter, *args):
        pass
