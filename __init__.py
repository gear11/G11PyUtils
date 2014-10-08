from .IndexedDictList import IndexedDictList
from .StopWatch import StopWatch
import bz2
import gzip
import codecs
from collections import defaultdict
import logging
import sys
import glob
LOG = logging.getLogger("g11pyutils")
from .Connector import Connector
import itertools
import datetime
import requests

def is_str_type(o):
    return isinstance(o, str) or (sys.version_info < (3,0,0) and type(o) is unicode)


def print_bold(s):
    print('\033[1m' + s + '\033[0m')


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
    # Handle http(s):
    if s.startswith('http://') or s.startswith('https://'):
        r = requests.get(s, stream=True)
        return r.raw if enc == 'b' else codecs.getreader(enc)(r.raw)
    fos = []
    fnames = glob.glob(s)
    if not fnames:
        raise IOError("No such file: %s" % s)
    for f in fnames:
        ext = f.rsplit(".", 1)[-1]
        if ext == "bz2":
            fo = bz2.BZ2File(f, 'r', 10*1024)
        elif ext == "gz":
            fo = gzip.open(f, 'rb')
        else:
            fo = open(f, 'rb') # Encoding handled below
        fos = itertools.chain(fos, fo) if len(fnames) > 1 else fo

    # Wrap the raw file handle into one that can decode
    # Wikipedia needs this
    return fos if enc == 'b' else codecs.getreader(enc)(fos)
    #return fos


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


def bare(tag):
    """Returns a tag stripped of preceding namespace info"""
    n = tag.rfind('}')
    return tag[n+1:] if n >= 0 else tag


def etree_to_dict(t, strip_ns=True, prefix_attr=False, ignore=[]):
    ignore = set(ignore) if ignore else []
    tag_name = bare(t.tag) if strip_ns else t.tag
    d = {tag_name: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for c in children:
            dc = etree_to_dict(c, strip_ns, prefix_attr, ignore)
            for k, v in dc.items():
                dd[k].append(v)
        d = {tag_name: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[tag_name].update(('@'+k if prefix_attr else k, v) for k, v in t.attrib.items() if not k in ignore)
    if t.text:
        text = t.text.strip()
        #if children or t.attrib:
        if children or (t.attrib and d[tag_name]):  # Condense elements w/ text and w/o attr into a list
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
        return self._fetch_next() is not None

    def _fetch_next(self):
        if not self._next:
            try:
                self._next = self._it.next()
            except StopIteration:
                pass
        return self._next

    def next(self):
        n = self._fetch_next()
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
            if type(v1) is str or (sys.version_info < (3,0,0) and type(v1) is unicode):  # If the type is string or uni, do equals
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


def default_json_encoder(self, obj):
    if isinstance(obj, datetime.datetime):
        return obj.strftime('%Y-%m-%dT%H:%M:%SZ')
    return obj.__dict__


def to_epoch_seconds(dt):
    return int((dt - datetime.datetime(1970, 1, 1)).total_seconds())
