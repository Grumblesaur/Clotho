import math
import cmath
import re
from random import random as rand
from fractions import Fraction
from native import PrintQueue as pq, lzip, shuffled, flatten, stats

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
}

exposed['builtins'] = sorted(exposed.keys())
