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
