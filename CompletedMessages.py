from collections import OrderedDict
from threading import Lock


class CompletedMessages:
    def __init__(self, maxsize: int):
        self._cache = OrderedDict()
        self._maxsize = maxsize
        self._lock = Lock()

    def add(self, messageid: bytes):
        with self._lock:
            self._cache[messageid] = None
            if len(self._cache) > self._maxsize:
                self._cache.popitem(last=False)

    def __contains__(self, item) -> bool:
        with self._lock:
            return item in self._cache
