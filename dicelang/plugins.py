import cmath
import math
import re
from fractions import Fraction
from random import random as rand

from native import PrintQueue as pq, flatten, lzip, shuffled, stats, typename, typeof
from bonus import dnd

exposed = {
    'math': math,
    'cmath': cmath,
    're': re,
    'str': str,
    'int': int,
    'float': float,
    'dict': dict,
    'tuple': tuple,
    'set': set,
    'frozenset': frozenset,
    'abs': abs,
    'sorted': sorted,
    'min': min,
    'max': max,
    'sum': sum,
    'isinstance': isinstance,
    'typeof': typeof,
    'typename': typename,
    'zip': lzip,
    'shuffled': shuffled,
    'stats': stats,
    'flatten': flatten,
    'rand': rand,
    'print': pq.print,
    'print0': pq.print0,
    'println': pq.println,
    'println0': pq.println0,
    'Fraction': Fraction,
    'dnd': dnd.DND,
}

exposed['builtins'] = sorted(exposed.keys())
