import os

INFINITY = float('+inf')

if os.name.lower() == 'nt':
    os.system('color')

WHITE   = '\033[0m'
RED     = '\033[31m'
GREEN   = '\033[32m'
BLUE    = '\033[34m'
MAGENTA = '\033[35m'


def _colour(text, colour):
    return f'{colour}{text}{WHITE}'


def red(text):
    return _colour(text, RED)


def green(text):
    return _colour(text, GREEN)


def blue(text):
    return _colour(text, BLUE)


def magenta(text):
    return _colour(text, MAGENTA)

