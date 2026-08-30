from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from time import monotonic
from typing import Any


@dataclass
class _CacheEntry:
    value: Any
    expires_at: float


class IntelligenceCache:
    """
    Small in-memory TTL cache for reusable AwareOn
    intelligence results.

    Intended for development and single-process
    runtime reuse. Cache misses simply recompute.
    """

    def __init__(
        self,
        default_ttl_seconds: float = 300.0,
        max_entries: int = 256,
    ) -> None:
        if default_ttl_seconds <= 0:
            raise ValueError(
                "default_ttl_seconds must be greater than 0."
            )

        if max_entries <= 0:
            raise ValueError(
                "max_entries must be greater than 0."
            )

        self.default_ttl_seconds = float(
            default_ttl_seconds
        )

        self.max_entries = int(
            max_entries
        )

        self._entries: dict[Any, _CacheEntry] = {}
        self._lock = RLock()

        self.hits = 0
        self.misses = 0

    def _remove_expired(self) -> None:
        now = monotonic()

        expired = [
            key
            for key, entry in self._entries.items()
            if entry.expires_at <= now
        ]

        for key in expired:
            self._entries.pop(
                key,
                None,
            )

    def get(
        self,
        key: Any,
    ) -> Any | None:

        with self._lock:

            entry = self._entries.get(
                key
            )

            if entry is None:
                self.misses += 1
                return None

            if entry.expires_at <= monotonic():

                self._entries.pop(
                    key,
                    None,
                )

                self.misses += 1
                return None

            self.hits += 1

            return entry.value

    def set(
        self,
        key: Any,
        value: Any,
        ttl_seconds: float | None = None,
    ) -> None:

        ttl = (
            self.default_ttl_seconds
            if ttl_seconds is None
            else float(ttl_seconds)
        )

        if ttl <= 0:
            raise ValueError(
                "ttl_seconds must be greater than 0."
            )

        with self._lock:

            self._remove_expired()

            if (
                key not in self._entries
                and
                len(self._entries)
                >= self.max_entries
            ):
                oldest_key = min(
                    self._entries,
                    key=lambda item:
                        self._entries[item].expires_at,
                )

                self._entries.pop(
                    oldest_key,
                    None,
                )

            self._entries[key] = _CacheEntry(
                value=value,
                expires_at=(
                    monotonic()
                    + ttl
                ),
            )

    def get_or_set(
        self,
        key: Any,
        factory,
        ttl_seconds: float | None = None,
    ) -> Any:

        cached = self.get(
            key
        )

        if cached is not None:
            return cached

        value = factory()

        self.set(
            key,
            value,
            ttl_seconds,
        )

        return value

    def clear(self) -> None:

        with self._lock:
            self._entries.clear()

    def stats(self) -> dict[str, Any]:

        with self._lock:

            self._remove_expired()

            total = (
                self.hits
                +
                self.misses
            )

            hit_rate = (
                self.hits / total
                if total
                else 0.0
            )

            return {
                "entries":
                    len(
                        self._entries
                    ),

                "hits":
                    self.hits,

                "misses":
                    self.misses,

                "hit_rate":
                    hit_rate,

                "max_entries":
                    self.max_entries,

                "default_ttl_seconds":
                    self.default_ttl_seconds,
            }


intelligence_cache = IntelligenceCache(
    default_ttl_seconds=300.0,
    max_entries=256,
)
