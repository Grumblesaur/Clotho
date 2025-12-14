from enum import IntEnum
import random
from dicelang.exceptions import ImpossibleDice
RollResult = int | list[int]


class Mode(IntEnum):
    """Dice-rolling modes:
      - KEEP – Dice will be selected based on which ones should be kept.
      - DROP – Dice will be selected based on which ones should be dropped."""
    DROP = 0
    KEEP = 1

class Target(IntEnum):
    """Dice-rolling targets:
      - LOWEST – Dice will be dropped or kept according to the Mode when they are the lowest.
      - HIGHEST – Dice will be dropped or kept according to the Mode when they are the highest.
      - ALL – All dice will be kept regardless of value or mode."""
    LOWEST = -1
    ALL = 0
    HIGHEST = 1


def kernel(dice: int, sides: int, n: int = 1, mode: Mode = Mode.KEEP, target: Target = Target.ALL, as_sum: bool = True) -> RollResult:
    if mode is Mode.KEEP and n > dice or mode is Mode.DROP and n >= dice:
        raise ImpossibleDice(f'tried to {"keep" if mode else "drop"} {n} {"die" if n == 1 else "dice"},'
                             + f' but only {dice} {"die was" if n == 1 else "dice were"} rolled.')
    if n < 1:
        raise ImpossibleDice(f'tried to {"keep" if mode else "drop"} non-positive number of dice ({n})')

    rolls = sorted(random.randint(1, sides) for _ in range(dice))
    match (mode, target):
        case Mode.KEEP, Target.LOWEST:
            rolls = rolls[:n]
        case Mode.DROP, Target.LOWEST:
            rolls = rolls[n:]
        case Mode.KEEP, Target.HIGHEST:
            rolls = rolls[-n:]
        case Mode.DROP, Target.HIGHEST:
            rolls = rolls[:-n]

    return sum(rolls) if as_sum else rolls


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
