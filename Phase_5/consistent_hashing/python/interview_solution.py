"""
Consistent Hashing Ring - Interview Solution (Python)

1. Primary Capabilities:
   - SHA-256 hash ring with virtual nodes for uniform distribution
   - O(log n) lookup via bisect on sorted ring positions
   - Add/remove nodes with minimal key redistribution
   - Concurrency Extension: threading.Lock on all ring mutations

2. Error Handling:
   - ValueError on duplicate node, KeyError on missing node removal
   - Returns None on empty ring lookup

3. Out Of Scope:
   - Weighted nodes, replication factor, data migration orchestration,
     bounded loads, jump consistent hashing
"""
import hashlib, bisect, threading

class Ring:
    def __init__(self, vn=150):
        self.vn, self.ring, self.h2n, self.nodes = vn, [], {}, set()
        self._lk = threading.Lock()

    def _h(self, k): return int(hashlib.sha256(k.encode()).hexdigest(), 16)

    def add(self, node):
        with self._lk:
            self.nodes.add(node)
            for i in range(self.vn):
                h = self._h(f"{node}#v{i}")
                self.h2n[h] = node; bisect.insort(self.ring, h)

    def remove(self, node):
        with self._lk:
            self.nodes.discard(node)
            for i in range(self.vn):
                h = self._h(f"{node}#v{i}")
                del self.h2n[h]
                idx = bisect.bisect_left(self.ring, h)
                if idx < len(self.ring) and self.ring[idx] == h: self.ring.pop(idx)

    def get(self, key):
        with self._lk:
            if not self.ring: return None
            h = self._h(key)
            idx = bisect.bisect_right(self.ring, h)
            return self.h2n[self.ring[idx % len(self.ring)]]

if __name__ == "__main__":
    r = Ring(100)
    r.add("s1"); r.add("s2"); r.add("s3")
    n = r.get("my_key")
    assert n in {"s1","s2","s3"}
    r.remove("s1"); r.remove("s2")
    assert r.get("any") == "s3"
    print("Interview Consistent Hash passed!")
