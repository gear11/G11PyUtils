__author__ = 'Andy Jenkins'

from IndexedDictList import IndexedDictList
from StopWatch import StopWatch


def is_str_type(o):
    return isinstance(o, str) or isinstance(o, unicode)

def print_bold(s):
    print '\033[1m' + s + '\033[0m'
