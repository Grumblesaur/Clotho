from typing import Any


class Result:
    def __init__(self, *, value: Any = None, console: str | None = None, error: Any = None,
                 is_helptext: bool = False):
        self.value = value
        self.console = console
        self.error = error
        self.helptext = is_helptext

    def __bool__(self) -> bool:
        return self.value is not None

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(value={self.value!r}, console={self.console!r}, error={self.error!r})'


def success(value: Any, console: str) -> Result:
    return Result(value=value, console=console)


def failure(error: Any, console: str) -> Result:
    return Result(error=error, console=console)


def helptext(value: Any):
    return Result(value=value, console=None, is_helptext=True)
