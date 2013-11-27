__author__ = 'Andy Jenkins'

import logging
import unittest
import sys
from g11pyutils import IndexedDictList, StopWatch


LOG = logging.getLogger("test_IndexedDictList")


class test_IndexedDictList(unittest.TestCase):

    def setUp(self):
        logging.basicConfig(level=logging.INFO, stream = sys.stdout)
        self.watch = StopWatch().start()
        self.list = IndexedDictList([
        {"first_name":"Mary", "last_name":"Smith", "occupation":"Scientist"},
        {"first_name":"Mary", "last_name":"Jones", "occupation":"Teacher"},
        {"first_name":"Davy", "last_name":"Jones", "occupation":"Sailor"},
        {"first_name":"Popeye", "occupation":"Sailor"},
        {"first_name":"Neil", "last_name":"DeGrasse-Tyson", "occupation":"Scientist"},
        ])

    def tearDown(self):
        LOG.debug("Finished %s in %s sec", self.id(), self.watch.readSec())
        pass

    def test_find(self):
        r = self.list.find("first_name", "Mary")
        self.assertEquals(2, len(r))

        r = self.list.find("occupation", "Sailor")
        self.assertEquals(2, len(r))

    def test_none(self):
        r = self.list.find("last_name", None)
        self.assertEquals(1, len(r))
        self.assertEquals(r[0]["first_name"], "Popeye")

if __name__ == '__main__':
    unittest.main()
