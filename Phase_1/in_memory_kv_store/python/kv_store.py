from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
import time
from typing import Any, Dict, Iterator, List, Optional


@dataclass
class Entry:
    """Represents a store entry with an optional TTL expiration timestamp."""
    value: Any
    expiry: Optional[float] = None

    def is_expired(self, current_time: Optional[float] = None) -> bool:
        now = current_time if current_time is not None else time.time()
        return self.expiry is not None and now >= self.expiry


class BaseKeyValueStore(ABC):
    """Abstract Base Class specifying the Key-Value Store interface."""

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None: ...

    @abstractmethod
    def get(self, key: str) -> Optional[Any]: ...

    @abstractmethod
    def delete(self, key: str) -> bool: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def begin(self) -> None: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...


class InMemoryKVStore(BaseKeyValueStore):
    """In-memory key-value store with TTL and nested transaction support."""

    def __init__(self) -> None:
        self._store: Dict[str, Entry] = {}
        self._transaction_stack: List[Dict[str, Optional[Entry]]] = []

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        expiry = time.time() + ttl if ttl is not None else None
        entry = Entry(value=value, expiry=expiry)
        if self._transaction_stack:
            self._transaction_stack[-1][key] = entry
        else:
            self._store[key] = entry

    def get(self, key: str) -> Optional[Any]:
        for tx in reversed(self._transaction_stack):
            if key in tx:
                entry = tx[key]
                return None if (entry is None or entry.is_expired()) else entry.value
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.is_expired():
            del self._store[key]
            return None
        return entry.value

    def delete(self, key: str) -> bool:
        if not self.exists(key):
            return False
        if self._transaction_stack:
            self._transaction_stack[-1][key] = None
        else:
            self._store.pop(key, None)
        return True

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def begin(self) -> None:
        self._transaction_stack.append({})

    def commit(self) -> None:
        if not self._transaction_stack:
            raise RuntimeError("No active transaction to commit.")
        current_tx = self._transaction_stack.pop()
        if self._transaction_stack:
            self._transaction_stack[-1].update(current_tx)
        else:
            for key, entry in current_tx.items():
                if entry is None:
                    self._store.pop(key, None)
                else:
                    self._store[key] = entry

    def rollback(self) -> None:
        if not self._transaction_stack:
            raise RuntimeError("No active transaction to rollback.")
        self._transaction_stack.pop()

    @contextmanager
    def transaction(self) -> Iterator["InMemoryKVStore"]:
        """Context manager for ACID-style transaction blocks."""
        self.begin()
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise
