class Spread:
    def __init__(self, items):
        self.items = items


def do_nothing():
    pass


class _Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance


class Undefined(_Singleton):
    def __repr__(self):
        return "Undefined"

    def __bool__(self):
        return False


Undefined = Undefined()
