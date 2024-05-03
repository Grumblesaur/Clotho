from dicelang import special


class DicelangException(Exception):
    """Base class for the Dicelang exception hierarchy."""
    pass


Empty = object()


class ParseError(DicelangException):
    pass


class DicelangSignal(DicelangException):
    """Branch of the exception hierarchy for flow control. These
    exceptions can optionally capture a value, which will be used
    in certain contexts."""
    def __init__(self, value=Empty):
        self.value = value

    def __bool__(self):
        return self.value is not Empty

    def unwrap(self):
        return self.value if self else special.Undefined


class Break(DicelangSignal):
    pass


class Continue(DicelangSignal):
    pass


class Return(DicelangSignal):
    pass


class Terminate(DicelangSignal):
    pass


class ProgrammingError(DicelangException):
    """Indicates a bug or unhandled case."""
    pass


class UndefinedName(ProgrammingError):
    pass


class DeleteNonexistent(UndefinedName):
    pass


class FetchNonexistent(UndefinedName):
    pass


class IllegalSignal(ProgrammingError):
    pass


class BadLiteral(ProgrammingError):
    pass


class MissingScope(ProgrammingError):
    pass


class Impossible(ProgrammingError):
    pass


class NoSuchVariable(ProgrammingError):
    pass


class DicelangRuntimeError(DicelangException):
    """Indicates an error that probably arose from a user's code."""
    pass


class ExcessiveRuntime(DicelangRuntimeError):
    pass


class DuplicateParameter(DicelangRuntimeError):
    pass


class BadArguments(DicelangRuntimeError):
    pass


class InvalidSubscript(DicelangRuntimeError):
    pass


class ImpossibleDice(DicelangRuntimeError):
    pass


class SpreadError(DicelangRuntimeError):
    pass


class AssignmentError(DicelangRuntimeError):
    pass


class UnpackError(AssignmentError):
    pass


class BuiltinError(DicelangRuntimeError):
    Module = type(special)
    Class = type
    Function = type(special.do_nothing())

    @classmethod
    def from_instance(cls, instance, action_name):
        match type(instance):
            case cls.Module:
                err = "module"
            case cls.Class:
                err = "class"
            case cls.Function:
                err = "function"
            case _:
                err = "variable"
        return cls(f"can't {action_name} built-in {err}.")
