from enum import Enum
from random import randint
from dicelang.exceptions import ImpossibleDice
RollResult = int | list[int]


class Keep(Enum):
    LOW = -1
    ALL = 0
    HIGH = 1


def kernel(dice: int, sides: int, mode: Keep = Keep.ALL, kept: int = 1, as_sum: bool = True) -> RollResult:
    rolls = (randint(1, sides) for _ in range(dice))
    if mode == Keep.ALL:
        return (sum if as_sum else list)(rolls)
    rolls = sorted(rolls)
    if not (1 <= kept < len(rolls)):
        raise ImpossibleDice(f'tried to keep {kept} dice instead of [1, {dice}] dice.')
    results = rolls[-kept:] if mode == Keep.HIGH else rolls[:kept]
    return sum(results) if as_sum else results


def keep_all(dice: int, sides: int, as_sum: bool = True) -> RollResult:
    return kernel(dice, sides, Keep.ALL, as_sum=as_sum)


def keep_highest(dice: int, sides: int, kept: int, as_sum: bool = True) -> RollResult:
    return kernel(dice, sides, Keep.HIGH, kept, as_sum)


def keep_lowest(dice: int, sides: int, kept: int, as_sum: bool = True) -> RollResult:
    return kernel(dice, sides, Keep.LOW, kept, as_sum)
