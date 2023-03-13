from random import shuffle
import statistics
import more_itertools


def shuffled(iterable):
    new = list(iterable)
    shuffle(new)
    return new


def stats(iterable):
    items = iterable.values() if isinstance(iterable, dict) else iterable
    out = {'average': statistics.mean(items), 'minimum': min(items),
           'maximum': max(items), 'median': statistics.median(items),
           'size': len(items), 'sum': sum(items)}
    out['stddev'] = statistics.pstdev(items, out['average'])
    out['q1'] = statistics.median(x for x in items if x < out['median'])
    out['q3'] = statistics.median(x for x in items if x > out['median'])
    return out


def flatten(items):
    return list(more_itertools.collapse(items))
