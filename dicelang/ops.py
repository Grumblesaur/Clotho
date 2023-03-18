def cat(x, y):
    return int(f'{int(x)}{int(y)}')


icat = cat


def iand(x, y):
    return x and y


def ior(x, y):
    return x or y


def ixor(x, y):
    return x and not y or not x and y
