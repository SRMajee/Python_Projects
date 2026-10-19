"""
O(1) LRU & LFU Cache - Complete Solution (Python)
Strict O(1) time complexity for get and put operations.
- LRU: HashMap + Doubly Linked List
- LFU: HashMap + Frequency buckets (each a DLL)
Concurrency: threading.Lock guards all cache mutations.
"""
import threading
from typing import Any


class _DLLNode:
    """Doubly linked list node."""
    __slots__ = ('key', 'value', 'prev', 'next', 'freq')
    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.prev = self.next = None
        self.freq = 1


class _DLL:
    """Doubly linked list with sentinel head/tail."""
    def __init__(self):
        self.head = _DLLNode()
        self.tail = _DLLNode()
        self.head.next = self.tail
        self.tail.prev = self.head
        self.size = 0

    def push_front(self, node: _DLLNode):
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node
        self.size += 1

    def remove(self, node: _DLLNode):
        node.prev.next = node.next
        node.next.prev = node.prev
        self.size -= 1

    def pop_back(self) -> _DLLNode | None:
        if self.size == 0:
            return None
        node = self.tail.prev
        self.remove(node)
        return node

    def is_empty(self) -> bool:
        return self.size == 0


class LRUCache:
    """
    O(1) LRU Cache using HashMap + Doubly Linked List.
    - get: move to front (MRU), return value
    - put: insert at front, evict tail (LRU) if over capacity
    """
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self._capacity = capacity
        self._map: dict[Any, _DLLNode] = {}
        self._dll = _DLL()
        self._lock = threading.Lock()

    def get(self, key: Any) -> Any | None:
        with self._lock:
            node = self._map.get(key)
            if not node:
                return None
            self._dll.remove(node)
            self._dll.push_front(node)
            return node.value

    def put(self, key: Any, value: Any) -> None:
        with self._lock:
            if key in self._map:
                node = self._map[key]
                node.value = value
                self._dll.remove(node)
                self._dll.push_front(node)
            else:
                if len(self._map) >= self._capacity:
                    evicted = self._dll.pop_back()
                    if evicted:
                        del self._map[evicted.key]
                node = _DLLNode(key, value)
                self._dll.push_front(node)
                self._map[key] = node

    def __len__(self):
        return len(self._map)

    def __contains__(self, key):
        return key in self._map


class LFUCache:
    """
    O(1) LFU Cache using HashMap + Frequency buckets.
    Each frequency maps to a DLL (within same freq, LRU eviction).
    """
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self._capacity = capacity
        self._map: dict[Any, _DLLNode] = {}
        self._freq_map: dict[int, _DLL] = {}
        self._min_freq = 0
        self._lock = threading.Lock()

    def _touch(self, node: _DLLNode):
        """Move node to next frequency bucket."""
        freq = node.freq
        self._freq_map[freq].remove(node)
        if self._freq_map[freq].is_empty():
            del self._freq_map[freq]
            if self._min_freq == freq:
                self._min_freq += 1
        node.freq += 1
        if node.freq not in self._freq_map:
            self._freq_map[node.freq] = _DLL()
        self._freq_map[node.freq].push_front(node)

    def get(self, key: Any) -> Any | None:
        with self._lock:
            node = self._map.get(key)
            if not node:
                return None
            self._touch(node)
            return node.value

    def put(self, key: Any, value: Any) -> None:
        with self._lock:
            if key in self._map:
                node = self._map[key]
                node.value = value
                self._touch(node)
            else:
                if len(self._map) >= self._capacity:
                    dll = self._freq_map.get(self._min_freq)
                    if dll:
                        evicted = dll.pop_back()
                        if evicted:
                            del self._map[evicted.key]
                        if dll.is_empty():
                            del self._freq_map[self._min_freq]
                node = _DLLNode(key, value)
                node.freq = 1
                self._min_freq = 1
                if 1 not in self._freq_map:
                    self._freq_map[1] = _DLL()
                self._freq_map[1].push_front(node)
                self._map[key] = node

    def __len__(self):
        return len(self._map)
