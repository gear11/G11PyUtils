__author__ = 'Andy Jenkins'

import logging
from datetime import datetime, timedelta

LOG = logging.getLogger("StopWatch")

class StopWatch():
    """A simple stopwatch that can be started, stopped, and read.
    Useful for logging times for code execution."""
    def __init__(self):
        self._started = None
        self._stopped = None

    # Test
    def start(self):
        now = datetime.now()
        if not self._started:
            self._started = now
        elif self._stopped:
            self._started += now - self._stopped
            self._stopped = None
        return self

    def stop(self):
        self._stopped = datetime.now()
        return self

    def read(self):
        if not self._started:
            return timedelta()
        return datetime.now() - self._started

    def readSec(self):
        dur = self.read()
        return dur.seconds + (dur.microseconds / 1000) / 1000.0

    def reset(self):
        self._started = None
        self._stopped = None
        return self
