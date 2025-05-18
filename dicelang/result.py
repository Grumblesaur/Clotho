from typing import Any
NotSpecified = object


class Result:
    def __init__(self, *, value: Any = None, console: str | None = None, error: Any = None):
        self.value = value
        self.console = console
        self.error = error

    def __bool__(self) -> bool:
        return self.value is not None

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(value={self.value!r}, console={self.console!r}, error={self.error!r})'


def success(value: Any, console: str) -> Result:
    return Result(value=value, console=console)


def failure(error: Any, console: str) -> Result:
    return Result(error=error, console=console)
