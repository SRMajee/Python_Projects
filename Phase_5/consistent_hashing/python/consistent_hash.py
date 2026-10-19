"""
Consistent Hashing Ring - Complete Solution (Python)
Distributes keys across nodes with virtual nodes for uniform load.
- Add/remove nodes with minimal key redistribution
- Configurable virtual nodes per physical node
- SHA-256 based hash function for uniform distribution
Concurrency: threading.Lock for thread-safe add/remove/lookup.
"""
import hashlib
import bisect
import threading
from typing import Any


class ConsistentHashRing:
    """Consistent hash ring with virtual nodes."""

    def __init__(self, num_virtual: int = 150):
        if num_virtual <= 0:
            raise ValueError("num_virtual must be positive")
        self._num_virtual = num_virtual
        self._ring: list[int] = []         # sorted hash positions
        self._hash_to_node: dict[int, str] = {}
        self._nodes: set[str] = set()
        self._lock = threading.Lock()

    def _hash(self, key: str) -> int:
        return int(hashlib.sha256(key.encode()).hexdigest(), 16)

    def add_node(self, node: str) -> None:
        """Add a physical node with virtual replicas."""
        with self._lock:
            if node in self._nodes:
                raise ValueError(f"Node '{node}' already exists")
            self._nodes.add(node)
            for i in range(self._num_virtual):
                vkey = f"{node}#v{i}"
                h = self._hash(vkey)
                self._hash_to_node[h] = node
                bisect.insort(self._ring, h)

    def remove_node(self, node: str) -> None:
        """Remove a physical node and all its virtual replicas."""
        with self._lock:
            if node not in self._nodes:
                raise KeyError(f"Node '{node}' not found")
            self._nodes.discard(node)
            for i in range(self._num_virtual):
                vkey = f"{node}#v{i}"
                h = self._hash(vkey)
                del self._hash_to_node[h]
                idx = bisect.bisect_left(self._ring, h)
                if idx < len(self._ring) and self._ring[idx] == h:
                    self._ring.pop(idx)

    def get_node(self, key: str) -> str | None:
        """Find which node a key maps to (clockwise from hash position)."""
        with self._lock:
            if not self._ring:
                return None
            h = self._hash(key)
            idx = bisect.bisect_right(self._ring, h)
            if idx >= len(self._ring):
                idx = 0  # wrap around
            return self._hash_to_node[self._ring[idx]]

    def get_nodes(self) -> set[str]:
        with self._lock:
            return set(self._nodes)

    def get_distribution(self, keys: list[str]) -> dict[str, int]:
        """Compute key distribution across nodes."""
        dist: dict[str, int] = {n: 0 for n in self._nodes}
        for key in keys:
            node = self.get_node(key)
            if node:
                dist[node] += 1
        return dist
