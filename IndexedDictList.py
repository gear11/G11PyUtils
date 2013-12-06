__author__ = 'Andy Jenkins'

import logging

LOG = logging.getLogger("IndexedDictList")

class IndexedDictList(list):
    """A list of dicts that can return sublists based on matching
    of key values within the dict elements. BOO.
    """
    def __init__(self, l):
        list.__init__(self, l)
        self._indices = {}

    def __getslice__(self,i,j):
        return IndexedDictList(list.__getslice__(self, i, j))

    def __add__(self,other):
        return IndexedDictList(list.__add__(self,other))

    def __mul__(self,other):
        return IndexedDictList(list.__mul__(self,other))

    def find(self, key, value):
        """Returns an IndexedDictList containing all members with the given key, matching the given value"""
        index = self.get_index(key)
        return IndexedDictList(index.get(value)) if value in index else []

    def get_index(self, key):
        """Returns an index (dict) for the given key over all items, where each entry in the index is a list
         of matching elements"""
        index = self._indices.get(key)
        if index:
            return index # Already have it
        # Need to build it
        LOG.debug("Building index on property %s", key)
        index = {}
        for el in self:
            val = el.get(key)
            matches = index.get(val)
            if not matches:
                index[val] = matches = []
            matches.append(el)
        self._indices[key] = index
        return index




