from enum import Enum, IntEnum
import random
from dicelang.exceptions import ImpossibleDice
RollResult = int | list[int]


class Mode(IntEnum):
    DROP = 0
    KEEP = 1

class Target(IntEnum):
    LOWEST = -1
    ALL = 0
    HIGHEST = 1


def kernel(dice: int, sides: int, n: int = 1, mode: Mode = Mode.KEEP, target: Target = Target.ALL, as_sum: bool = True) -> RollResult:
    if n > dice and mode is Mode.KEEP or n >= dice and mode is Mode.DROP:
        raise ImpossibleDice(f'tried to {"keep" if mode else "drop"} {n} {"die" if n == 1 else "dice"},'
                             + f' but only {dice} {"die was" if n == 1 else "dice were"} rolled.')
    if n < 1:
        raise ImpossibleDice(f'tried to {"keep" if mode else "drop"} non-positive number of dice ({n})')

    rolls = sorted(random.randint(1, sides) for _ in range(dice))
    results = None
    match (mode, target):
        case _, Target.ALL:
            results = rolls
        case Mode.KEEP, Target.LOWEST:
            results = rolls[:n]
        case Mode.DROP, Target.LOWEST:
            results = rolls[n:]
        case Mode.KEEP, Target.HIGHEST:
            results = rolls[-n:]
        case Mode.DROP, Target.HIGHEST:
            results = rolls[:-n]

    return sum(results) if as_sum else results


def keep_all(dice: int, sides: int, as_sum: bool = True) -> RollResult:
    return kernel(dice, sides, as_sum=as_sum)

def keep_highest(dice: int, sides: int, n: int, as_sum: bool = True) -> RollResult:
    return kernel(dice, sides, n, target=Target.HIGHEST, as_sum=as_sum)

def keep_lowest(dice: int, sides: int, n: int, as_sum: bool = True) -> RollResult:
    return kernel(dice, sides, n, target=Target.LOWEST, as_sum=as_sum)

def drop_highest(dice: int, sides: int, n: int, as_sum: bool = True) -> RollResult:
    return kernel(dice, sides, n, mode=Mode.DROP, target=Target.HIGHEST, as_sum=as_sum)

def drop_lowest(dice: int, sides: int, n: int, as_sum: bool = True) -> RollResult:
    return kernel(dice, sides, n, mode=Mode.DROP, target=Target.LOWEST, as_sum=as_sum)
