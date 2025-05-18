from typing import SupportsInt


def cat(x: SupportsInt, y: SupportsInt) -> int:
    return int(f'{int(x)}{int(y)}')


icat = cat


def iand(x: bool, y: bool) -> bool:
    return x and y


def ior(x: bool, y: bool) -> bool:
    return x or y


def ixor(x: bool, y: bool) -> bool:
    return x and not y or y and not x
