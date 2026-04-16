from typing import Any

class BadResult(Exception):
    pass


class Result:
    def __init__(self, *, value: Any = None, console: str | None = None, error: Any = None,
                 is_helptext: bool = False, exc_type: type = None):
        self.value = value
        self.console = console
        self.error = error
        self.helptext = is_helptext
        self.exc_type = exc_type

    def _original_error(self):
        return self.error.split(': ', 1)[-1]

    def __bool__(self) -> bool:
        return self.value is not None

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(value={self.value!r}, console={self.console!r}, error={self.error!r})'

    def unwrap(self) -> Any:
        if self.error is None:
            return self.value
        raise BadResult(f"Cannot unwrap result: Error: {self.error}")

    def reraise(self):
        if self.error:
            raise self.exc_type(self._original_error())
        raise BadResult(f'Cannot reraise error when valid value was provided: {self.value!r}')

    def unwrap_eq(self, other: Any) -> bool:
        return self.unwrap() == other

    def unwrap_ne(self, other: Any) -> bool:
        return self.unwrap() != other


def success(value: Any, console: str) -> Result:
    return Result(value=value, console=console)


def failure(error: Any, console: str, exc_type: type = None) -> Result:
    return Result(error=error, console=console, exc_type=exc_type)


def helptext(value: Any):
    return Result(value=value, console=None, is_helptext=True)
