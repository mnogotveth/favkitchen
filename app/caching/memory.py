from __future__ import annotations

import time
from typing import Dict, Generic, Hashable, TypeVar

T = TypeVar("T")


class SimpleTTLCache(Generic[T]):
    def __init__(self) -> None:
        self._store: Dict[Hashable, tuple[float, T]] = {}

    def get(self, key: Hashable) -> T | None:
        now = time.time()
        item = self._store.get(key)
        if not item:
            return None
        expires, value = item
        if expires > now:
            return value
        self._store.pop(key, None)
        return None

    def set(self, key: Hashable, value: T, ttl_seconds: int) -> None:
        self._store[key] = (time.time() + ttl_seconds, value)
