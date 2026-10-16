"""
Mentora – Simple TTL Cache
Avoids hammering the database on every request for data that changes slowly
(e.g. weekly analytics, user preferences).

Backed by a dict with per-key expiry.  Thread-safe for Uvicorn workers
(each worker has its own process-local cache – fine for read-heavy data).
"""

import time
import threading
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TTLCache:
    """
    A simple in-process TTL cache.

    Usage::

        cache = TTLCache(default_ttl=300)   # 5-minute default

        # Store
        cache.set("weekly:uid123", data, ttl=600)

        # Retrieve  (None if missing or expired)
        data = cache.get("weekly:uid123")

        # Invalidate
        cache.delete("weekly:uid123")
        cache.delete_prefix("weekly:")
    """

    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        self._store:   dict[str, tuple[Any, float]] = {}  # key → (value, expires_at)
        self._lock     = threading.Lock()
        self._default  = default_ttl
        self._max_size = max_size
        self._hits     = 0
        self._misses   = 0

    # ── Core ops ──────────────────────────────────────────────────────────────

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            value, expires_at = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                self._misses += 1
                return None
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl if ttl is not None else self._default
        with self._lock:
            # Evict oldest entry if at capacity
            if len(self._store) >= self._max_size and key not in self._store:
                oldest = min(self._store, key=lambda k: self._store[k][1])
                del self._store[oldest]
            self._store[key] = (value, time.monotonic() + ttl)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def delete_prefix(self, prefix: str) -> int:
        """Delete all keys starting with prefix. Returns count deleted."""
        with self._lock:
            keys = [k for k in self._store if k.startswith(prefix)]
            for k in keys:
                del self._store[k]
            return len(keys)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    # ── Stats ─────────────────────────────────────────────────────────────────

    @property
    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "size":      len(self._store),
            "hits":      self._hits,
            "misses":    self._misses,
            "hit_rate":  round(self._hits / total, 3) if total else 0,
        }

    def __repr__(self) -> str:
        return f"TTLCache(size={len(self._store)}, hits={self._hits}, misses={self._misses})"


# ── Module-level singleton ────────────────────────────────────────────────────
_cache = TTLCache(default_ttl=300, max_size=2000)

# Convenience wrappers
def cache_get(key: str) -> Optional[Any]:
    return _cache.get(key)

def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    _cache.set(key, value, ttl=ttl)

def cache_delete(key: str) -> None:
    _cache.delete(key)

def cache_bust(prefix: str) -> int:
    return _cache.delete_prefix(prefix)

def cache_stats() -> dict:
    return _cache.stats


