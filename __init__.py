from IndexedDictList import IndexedDictList
from StopWatch import StopWatch
import bz2
import codecs
from collections import defaultdict
import logging
import sys
LOG = logging.getLogger("g11pyutils")
from Connector import Connector


def is_str_type(o):
    return isinstance(o, str) or isinstance(o, unicode)


def print_bold(s):
    print '\033[1m' + s + '\033[0m'


def fout(s, enc="utf-8"):
    if not s or s.lower == 'stdout' or s == '-':
        return sys.stdout
    return codecs.open(s, 'w', enc)


def fopen(s, enc="utf-8"):
    """Opens the indicated file, handling special cases including None, "-", "stdin" (indicating stdin),
    and "stderr", indicating stderr.  For files that end in ".gz" or ".bz2", automatically handles
    decompression"""
    if not s:
        LOG.info("Returning sys.stdin")
        return sys.stdin
    ext = s.rsplit(".", 1)[-1]
    if ext == "bz2":
        fo = bz2.BZ2File(s, 'rb')
    else:
        fo = open(s, 'rb') # Encoding handled below

    # Wrap the raw file handle into one that can decode
    #return codecs.decode(fo, enc)
    return fo


def to_list(o):
    if type(o) is list:
        return o
    elif is_str_type(o):
        return [o]
    else:
        return list(o)  # Must be iterable

def to_dict(o):
    if is_str_type(o):
        return string_to_dict(o)
    elif hasattr(o, "tag"):
        return etree_to_dict(o)


def string_to_dict(s):
    """Takes a comma-delimited string of the form key1=val1,key2=val2 and returns a dict"""
    d = {}
    if s:
        for key, val in [item.split("=") for item in s.split(",")]:
            d[key] = val
    return d


def etree_to_dictx(t):
    """Converts an XML node from ElementTree to a dict"""
    d = {t.tag : map(etree_to_dict, t.iterchildren())}
    d.update(('@' + k, v) for k, v in t.attrib.iteritems())
    d['text'] = t.text
    return d


def bare(tag):
    """Returns a tag stripped of preceding namespace info"""
    n = tag.rfind('}')
    return tag[n+1:] if n >= 0 else tag


def etree_to_dict(t):
    strip_ns = True # Need to make this a param, but need to deal with recursion
    tag_name = bare(t.tag) if strip_ns else t.tag
    d = {tag_name: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.iteritems():
                dd[k].append(v)
        d = {tag_name: {k:v[0] if len(v) == 1 else v for k, v in dd.iteritems()}}
    if t.attrib:
        d[tag_name].update(('@' + k, v) for k, v in t.attrib.iteritems())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
              d[tag_name]['#text'] = text
        else:
            d[tag_name] = text
    return d


class HasNextIter:
    def __init__(self, it):
        self._it = it
        self._next = None

    def __iter__(self):
        return self

    def has_next(self):
        return self._fetchNext() != None

    def _fetchNext(self):
        if not self._next:
            try:
                self._next = self._it.next()
            except StopIteration:
                pass
        return self._next

    def next(self):
        n = self._fetchNext()
        if not n:
            raise StopIteration
        self._next = None
        return n


def select(d, keys):
    """
    Returns a new dict containing the indicated key(s) from the original.
    """
    if is_str_type(keys):
        keys = [keys]
    return dict((k, d[k]) for k in keys)


def has_all(d0, d1):
    """Indicates if d0 has all of the keys/values in d1 and they are equal.
    d0 may have additional keys, which are ignored. Great for unit tests
    where only some of the values returned are important."""
    to_check = [(d0, d1)]
    while len(to_check):
        d = to_check.pop()
        for k, v1 in d[1].iteritems():  # For each key/val in D1
            v0 = d[0].get(k)  # Get the corresponding val from D0
            if type(v1) in (str, unicode):  # If the type is string or uni, do equals
                if v0 != v1:
                    return False
            elif v0 is None:  # If the item is missing, we're done
                LOG.info("Missing expected key: %s", k)
            elif type(v1) is not type(v0):  # Else ensure same type
                LOG.info("Mismatched types: %s, %s", type(v1), type(v0))
                return False
            elif type(v1) is dict:  # If the item is a dict, add the values to the list
                to_check.append((v0, v1))
            elif type(v1) is list:  # If the value is a list, compare the ordered entries, up to length of expected
                LOG.info("Comparing lists: %s, %s", v0[0:len(v1)], v1)
                to_check += zip(v0[0:len(v1)], v1)
            elif v0 != v1:
                LOG.info("Mismatched values: %s, %s", v1, v0)
                return False
    return True