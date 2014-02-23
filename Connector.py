import logging
import time
import pymongo

LOG = logging.getLogger("Connector")

class Connector(object):
    """Encapsulates connection attempt/re-attempt logic for a remote service"""

    def __init__(self, do_connect, do_close=None, retries=100, sleep=30):
        self.do_connect = do_connect
        self.do_close = do_close
        self.retries = retries
        self.sleep = sleep
        self.conn = None # Connection implementation

    def c(self):
        return self.conn

    def connect(self, is_reconnect=False):
        if self.conn:
            LOG.warn("Already connected!")
            return
        if is_reconnect:
            LOG.info("Reconnecting...")
        else:
            LOG.info("Connecting...")
        attempt = 0
        while not self.conn:
            attempt += 1
            try:
                self.conn = self.do_connect()
                LOG.warn("Connection: %s", self.conn)
                return self.conn
            except Exception, ex:
                LOG.warn("Failure connecting: %s", ex)
                if attempt > self.retries:
                    LOG.warn("Failed to connect after %s attempts.", attempt)
                    break
                LOG.warn("Retrying after %s sec (%s attempts left)", self.sleep, self.retries - attempt)
                time.sleep(self.sleep)

    def reconnect(self):
        self.conn = None
        self.connect(True)

    def close(self):
        LOG.info("Closing...")
        if self.do_close:
            self.do_close(self.conn)
        self.conn = None