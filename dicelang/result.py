NotSpecified = object


class Result:
    def __init__(self, *, value=NotSpecified, console: str = NotSpecified, error = NotSpecified):
        self.value = value
        self.console = console
        self.error = error

    def __bool__(self):
        return self.value is not NotSpecified

    def __repr__(self):
        return f'{self.__class__.__name__}(value={self.value!r}, console={self.console!r}, error={self.error!r})'


def success(value, console: str):
    return Result(value=value, console=console)


def failure(error, console: str):
    return Result(error=error, console=console)
