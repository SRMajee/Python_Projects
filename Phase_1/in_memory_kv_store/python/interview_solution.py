"""
In-Memory Key-Value Store - Concise Interview Solution (Python)

1. Primary Capabilities:
- set(key, val, ttl=None): Insert or update key with optional expiration.
- get(key): Retrieve value; inspects active transaction frames top-down, then base store.
- delete(key): Tombstone key in current transaction or purge from base store.
- begin(), commit(), rollback(): Multi-level transaction stack.

2. Error Handling:
- Calling commit() or rollback() without active transactions raises RuntimeError.
- Accessing expired keys triggers lazy eviction and returns None.

3. Out Of Scope:
- AOF / RDB disk persistence.
- Redis Serialization Protocol (RESP) networking socket server.
- LRU/LFU memory eviction when memory capacity is reached.
"""

import time
from typing import Any, Dict, List, Optional


class InMemoryKVStore:
    def __init__(self) -> None:
        self.store: Dict[str, tuple] = {}  # key -> (value, expiry_timestamp)
        self.tx_stack: List[Dict[str, Optional[tuple]]] = []

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        expiry = time.time() + ttl if ttl else None
        entry = (value, expiry)
        if self.tx_stack:
            self.tx_stack[-1][key] = entry
        else:
            self.store[key] = entry

    def get(self, key: str) -> Optional[Any]:
        # Check active transactions top-down
        for tx in reversed(self.tx_stack):
            if key in tx:
                entry = tx[key]
                if entry is None or (entry[1] and time.time() >= entry[1]):
                    return None
                return entry[0]
        # Check base store
        if key in self.store:
            val, exp = self.store[key]
            if exp and time.time() >= exp:
                del self.store[key]
                return None
            return val
        return None

    def delete(self, key: str) -> bool:
        if self.get(key) is None:
            return False
        if self.tx_stack:
            self.tx_stack[-1][key] = None  # Tombstone
        else:
            del self.store[key]
        return True

    def begin(self) -> None:
        self.tx_stack.append({})

    def commit(self) -> None:
        if not self.tx_stack:
            raise RuntimeError("No active transaction")
        current_tx = self.tx_stack.pop()
        if self.tx_stack:
            self.tx_stack[-1].update(current_tx)
        else:
            for k, entry in current_tx.items():
                if entry is None:
                    self.store.pop(k, None)
                else:
                    self.store[k] = entry

    def rollback(self) -> None:
        if not self.tx_stack:
            raise RuntimeError("No active transaction")
        self.tx_stack.pop()


if __name__ == "__main__":
    kv = InMemoryKVStore()
    kv.set("a", 10)
    assert kv.get("a") == 10

    kv.begin()
    kv.set("a", 20)
    assert kv.get("a") == 20
    kv.rollback()
    assert kv.get("a") == 10

    kv.begin()
    kv.set("a", 30)
    kv.commit()
    assert kv.get("a") == 30
    print("Interview Python InMemoryKVStore passed!")
