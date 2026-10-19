"""Tests for Consistent Hashing Ring."""
import threading
import unittest
from consistent_hash import ConsistentHashRing


class TestConsistentHashRing(unittest.TestCase):
    def test_basic_routing(self):
        ring = ConsistentHashRing(num_virtual=100)
        ring.add_node("server1")
        ring.add_node("server2")
        ring.add_node("server3")
        node = ring.get_node("my_key")
        self.assertIn(node, {"server1", "server2", "server3"})

    def test_consistency(self):
        ring = ConsistentHashRing(num_virtual=100)
        ring.add_node("s1")
        ring.add_node("s2")
        n1 = ring.get_node("key_a")
        n2 = ring.get_node("key_a")
        self.assertEqual(n1, n2)

    def test_minimal_redistribution(self):
        ring = ConsistentHashRing(num_virtual=100)
        ring.add_node("s1")
        ring.add_node("s2")
        keys = [f"key_{i}" for i in range(1000)]
        before = {k: ring.get_node(k) for k in keys}
        ring.add_node("s3")
        after = {k: ring.get_node(k) for k in keys}
        unchanged = sum(1 for k in keys if before[k] == after[k])
        # Most keys should remain on same node
        self.assertGreater(unchanged, 500)

    def test_remove_node(self):
        ring = ConsistentHashRing(num_virtual=100)
        ring.add_node("s1")
        ring.add_node("s2")
        ring.remove_node("s1")
        for i in range(100):
            self.assertEqual(ring.get_node(f"k{i}"), "s2")

    def test_empty_ring(self):
        ring = ConsistentHashRing()
        self.assertIsNone(ring.get_node("anything"))

    def test_uniform_distribution(self):
        ring = ConsistentHashRing(num_virtual=200)
        for i in range(5):
            ring.add_node(f"node_{i}")
        keys = [f"item_{i}" for i in range(10000)]
        dist = ring.get_distribution(keys)
        avg = 10000 / 5
        for count in dist.values():
            self.assertGreater(count, avg * 0.5)
            self.assertLess(count, avg * 1.5)

    def test_duplicate_node(self):
        ring = ConsistentHashRing()
        ring.add_node("s1")
        with self.assertRaises(ValueError):
            ring.add_node("s1")

    def test_remove_missing(self):
        ring = ConsistentHashRing()
        with self.assertRaises(KeyError):
            ring.remove_node("phantom")

    def test_thread_safety(self):
        ring = ConsistentHashRing(num_virtual=50)
        def add_nodes(prefix, start, count):
            for i in range(start, start + count):
                try: ring.add_node(f"{prefix}_{i}")
                except ValueError: pass
        threads = [threading.Thread(target=add_nodes, args=(f"g{g}", g * 10, 10)) for g in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(len(ring.get_nodes()), 50)


if __name__ == "__main__":
    unittest.main()
