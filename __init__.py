from IndexedDictList import IndexedDictList
from StopWatch import StopWatch
import bz2
import gzip
import codecs
from collections import defaultdict
import logging
import sys
import glob
LOG = logging.getLogger("g11pyutils")
from Connector import Connector
import itertools


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
    if not s or s == '-':
        LOG.info("Returning sys.stdin")
        return sys.stdin
    fos = []
    fnames = glob.glob(s)
    if not fnames:
        raise IOError("No such file: %s" % s)
    for f in fnames:
        ext = f.rsplit(".", 1)[-1]
        if ext == "bz2":
            fo =  bz2.BZ2File(f, 'rb')
        elif ext == "gz":
            fo = gzip.open(f, 'rb')
        else:
            fo = open(f, 'rb') # Encoding handled below
        fos = itertools.chain(fos, fo) if len(fnames) > 1 else fo

    # Wrap the raw file handle into one that can decode
    #return codecs.decode(fo, enc)
    return fos


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