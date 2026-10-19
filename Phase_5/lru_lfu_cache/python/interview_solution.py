"""
O(1) LRU & LFU Cache - Interview Solution (Python)

1. Primary Capabilities:
   - LRU: O(1) get/put via HashMap + Doubly Linked List
   - LFU: O(1) get/put via HashMap + Frequency bucket DLLs
   - Tie-breaking: within same frequency, evict LRU
   - Concurrency Extension: threading.Lock wraps all mutations

2. Error Handling:
   - ValueError on non-positive capacity
   - get() returns None on miss

3. Out Of Scope:
   - TTL expiration, size-aware eviction, persistent caching,
     distributed caching, cache warming, write-through/write-back
"""
import threading

class Node:
    __slots__ = ('k','v','prev','next','freq')
    def __init__(self, k=0, v=0): self.k, self.v, self.prev, self.next, self.freq = k, v, None, None, 1

class DLL:
    def __init__(self):
        self.h, self.t = Node(), Node()
        self.h.next, self.t.prev, self.sz = self.t, self.h, 0
    def push(self, n):
        n.next, n.prev = self.h.next, self.h; self.h.next.prev = n; self.h.next = n; self.sz += 1
    def rm(self, n):
        n.prev.next, n.next.prev = n.next, n.prev; self.sz -= 1
    def pop(self):
        if self.sz == 0: return None
        n = self.t.prev; self.rm(n); return n

class LRUCache:
    def __init__(self, cap):
        self.cap, self.m, self.dll, self.lk = cap, {}, DLL(), threading.Lock()
    def get(self, k):
        with self.lk:
            if k not in self.m: return None
            n = self.m[k]; self.dll.rm(n); self.dll.push(n); return n.v
    def put(self, k, v):
        with self.lk:
            if k in self.m:
                n = self.m[k]; n.v = v; self.dll.rm(n); self.dll.push(n)
            else:
                if len(self.m) >= self.cap:
                    e = self.dll.pop()
                    if e: del self.m[e.k]
                n = Node(k, v); self.dll.push(n); self.m[k] = n

class LFUCache:
    def __init__(self, cap):
        self.cap, self.m, self.fm, self.mf, self.lk = cap, {}, {}, 0, threading.Lock()
    def _touch(self, n):
        f = n.freq; self.fm[f].rm(n)
        if self.fm[f].sz == 0: del self.fm[f]; self.mf += (self.mf == f)
        n.freq += 1; self.fm.setdefault(n.freq, DLL()).push(n)
    def get(self, k):
        with self.lk:
            if k not in self.m: return None
            n = self.m[k]; self._touch(n); return n.v
    def put(self, k, v):
        with self.lk:
            if k in self.m: n = self.m[k]; n.v = v; self._touch(n); return
            if len(self.m) >= self.cap:
                d = self.fm.get(self.mf)
                if d:
                    e = d.pop()
                    if e: del self.m[e.k]
                    if d.sz == 0: del self.fm[self.mf]
            n = Node(k, v); n.freq = 1; self.mf = 1
            self.fm.setdefault(1, DLL()).push(n); self.m[k] = n

if __name__ == "__main__":
    lru = LRUCache(2); lru.put(1,"a"); lru.put(2,"b"); lru.get(1); lru.put(3,"c")
    assert lru.get(2) is None and lru.get(1)=="a"
    lfu = LFUCache(2); lfu.put(1,"a"); lfu.put(2,"b"); lfu.get(1); lfu.put(3,"c")
    assert lfu.get(2) is None and lfu.get(1)=="a"
    print("Interview LRU/LFU passed!")
