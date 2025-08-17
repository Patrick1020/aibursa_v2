from __future__ import annotations
import time
from typing import Any, Dict, Tuple

class TTLCache:
    def __init__(self, ttl_seconds: int = 5, maxsize: int = 2048):
        self.ttl = ttl_seconds
        self.maxsize = maxsize
        self._store: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str):
        item = self._store.get(key)
        if not item: return None
        ts, val = item
        if time.time() - ts > self.ttl:
            self._store.pop(key, None)
            return None
        return val

    def set(self, key: str, value: Any):
        if len(self._store) >= self.maxsize:
            # remove oldest
            oldest = min(self._store.items(), key=lambda kv: kv[1][0])[0]
            self._store.pop(oldest, None)
        self._store[key] = (time.time(), value)

    def clear(self): self._store.clear()
