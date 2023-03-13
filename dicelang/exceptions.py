import special


class DicelangException(Exception):
    pass


class DicelangSignal(Exception):
    pass


class DicelangError(DicelangException):
    pass


class LiteralError(DicelangError):
    pass


class SubscriptError(DicelangError):
    pass


class DiceError(DicelangError):
    pass


class ScopeError(DicelangError):
    pass


class SpreadError(DicelangError):
    pass


class AssignmentError(DicelangError):
    pass


class UnpackError(AssignmentError):
    pass


class BuiltinError(DicelangError):
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


class Impossible(DicelangException):
    pass
