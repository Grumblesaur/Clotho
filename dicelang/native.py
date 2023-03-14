from random import shuffle
import statistics
import more_itertools


class PrintQueue:
    _instance = None

    def __new__(cls, queue=None):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
        cls._instance.queued = queue or []
        return cls._instance

    def _print_kernel(self, *args, sep=' ', end='\n'):
        msg = sep.join(str(a) for a in args) + end
        self.queued.append(msg)
        return msg

    def print(self, *args):
        return self._print_kernel(*args, end='')

    def print0(self, *args):
        return self._print_kernel(*args, sep='', end='')

    def println(self, *args):
        return self._print_kernel(*args)

    def println0(self, *args):
        return self._print_kernel(*args, sep='')

    def flush(self):
        flushed = ''.join(self.queued)
        self.queued.clear()
        return flushed


PrintQueue = PrintQueue()


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


def lzip(*iterables):
    return list(zip(*iterables))

