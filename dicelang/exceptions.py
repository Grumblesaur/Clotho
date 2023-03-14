import special


class DicelangException(Exception):
    """Base class for the Dicelang exception hierarchy."""
    pass


class DicelangSignal(DicelangException):
    """Branch of the exception hierarchy for flow control. These
    exceptions can optionally capture a value, which will be used
    in certain contexts."""
    def __init__(self, value=None):
        self.value = value

    def __bool__(self):
        return self.value is not None

    def get(self):
        return self.value


class BreakSignal(DicelangSignal):
    pass


class ContinueSignal(DicelangSignal):
    pass


class ReturnSignal(DicelangSignal):
    pass


class ProgrammingError(DicelangException):
    """Indicates a bug or unhandled case."""
    pass


class BadLiteral(ProgrammingError):
    pass


class MissingScope(ProgrammingError):
    pass


class Impossible(ProgrammingError):
    pass


class DicelangRuntimeError(DicelangException):
    """Indicates an error that probably arose from a user's code."""
    pass


class DuplicateArgument(DicelangRuntimeError):
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
