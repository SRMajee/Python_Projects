"""Tests for O(1) LRU & LFU Cache."""
import threading
import unittest
from cache import LRUCache, LFUCache


class TestLRUCache(unittest.TestCase):
    def test_basic(self):
        c = LRUCache(2)
        c.put(1, "a")
        c.put(2, "b")
        self.assertEqual(c.get(1), "a")
        c.put(3, "c")  # evicts key=2 (LRU)
        self.assertIsNone(c.get(2))
        self.assertEqual(c.get(3), "c")

    def test_update(self):
        c = LRUCache(2)
        c.put(1, "a")
        c.put(1, "updated")
        self.assertEqual(c.get(1), "updated")
        self.assertEqual(len(c), 1)

    def test_access_refreshes(self):
        c = LRUCache(2)
        c.put(1, "a")
        c.put(2, "b")
        c.get(1)  # refresh key=1
        c.put(3, "c")  # evicts key=2 (now LRU)
        self.assertIsNone(c.get(2))
        self.assertEqual(c.get(1), "a")

    def test_capacity_one(self):
        c = LRUCache(1)
        c.put(1, "a")
        c.put(2, "b")
        self.assertIsNone(c.get(1))
        self.assertEqual(c.get(2), "b")

    def test_miss(self):
        c = LRUCache(3)
        self.assertIsNone(c.get(999))

    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            LRUCache(0)

    def test_thread_safety(self):
        c = LRUCache(1000)
        def writer(start):
            for i in range(start, start + 100):
                c.put(i, i * 10)
        threads = [threading.Thread(target=writer, args=(i * 100,)) for i in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(len(c), 500)


class TestLFUCache(unittest.TestCase):
    def test_basic(self):
        c = LFUCache(2)
        c.put(1, "a")
        c.put(2, "b")
        c.get(1)  # freq(1)=2, freq(2)=1
        c.put(3, "c")  # evicts key=2 (least freq)
        self.assertIsNone(c.get(2))
        self.assertEqual(c.get(1), "a")
        self.assertEqual(c.get(3), "c")

    def test_tie_breaking(self):
        c = LFUCache(2)
        c.put(1, "a")  # freq=1
        c.put(2, "b")  # freq=1
        c.put(3, "c")  # tie: evict key=1 (LRU among freq=1)
        self.assertIsNone(c.get(1))
        self.assertEqual(c.get(2), "b")

    def test_update_no_eviction(self):
        c = LFUCache(2)
        c.put(1, "a")
        c.put(2, "b")
        c.put(1, "updated")
        self.assertEqual(c.get(1), "updated")
        self.assertEqual(len(c), 2)

    def test_capacity_one(self):
        c = LFUCache(1)
        c.put(1, "a")
        c.get(1)  # freq=2
        c.put(2, "b")  # evicts key=1 (only key, even though freq=2)
        self.assertIsNone(c.get(1))
        self.assertEqual(c.get(2), "b")


if __name__ == "__main__":
    unittest.main()
