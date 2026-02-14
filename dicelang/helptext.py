from typing import Callable
from dicelang.exceptions import Help
import sys
NO_OBJECT = object()

OPERATORS = {"for": "<Placeholder `for` loop info.>"}


class HelpUndefined(NotImplementedError, Help):
    pass


def helptext(obj: object = NO_OBJECT) -> str:
    if obj is NO_OBJECT:
        raise HelpUndefined("[insert generic help overview here]")
    if isinstance(obj, Callable) or isinstance(obj, type(sys)):
        raise Help(obj.__doc__)
    if obj in OPERATORS:
        raise Help(OPERATORS[obj])
    raise Help(obj.__class__.__doc__)


