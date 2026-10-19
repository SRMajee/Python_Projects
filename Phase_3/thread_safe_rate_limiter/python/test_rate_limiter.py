"""Tests for Thread-Safe Rate Limiter."""
import time
import threading
import unittest
from rate_limiter import TokenBucket, SlidingWindowLog, SlidingWindowCounter


class TestTokenBucket(unittest.TestCase):
    def test_basic_allow_and_deny(self):
        tb = TokenBucket(capacity=3, refill_rate=1.0)
        self.assertTrue(tb.allow())
        self.assertTrue(tb.allow())
        self.assertTrue(tb.allow())
        self.assertFalse(tb.allow())  # exhausted

    def test_refill(self):
        tb = TokenBucket(capacity=2, refill_rate=10.0)
        self.assertTrue(tb.allow())
        self.assertTrue(tb.allow())
        self.assertFalse(tb.allow())
        time.sleep(0.15)  # refill ~1.5 tokens
        self.assertTrue(tb.allow())

    def test_per_key_isolation(self):
        tb = TokenBucket(capacity=1, refill_rate=0.1)
        self.assertTrue(tb.allow("a"))
        self.assertFalse(tb.allow("a"))
        self.assertTrue(tb.allow("b"))  # independent

    def test_thread_safety(self):
        tb = TokenBucket(capacity=100, refill_rate=0.0)
        results = []
        def burst():
            for _ in range(20):
                results.append(tb.allow())
        threads = [threading.Thread(target=burst) for _ in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(sum(results), 100)


class TestSlidingWindowLog(unittest.TestCase):
    def test_basic_window(self):
        sw = SlidingWindowLog(max_requests=3, window_sec=0.5)
        self.assertTrue(sw.allow())
        self.assertTrue(sw.allow())
        self.assertTrue(sw.allow())
        self.assertFalse(sw.allow())
        time.sleep(0.55)
        self.assertTrue(sw.allow())

    def test_per_key(self):
        sw = SlidingWindowLog(max_requests=1, window_sec=1.0)
        self.assertTrue(sw.allow("x"))
        self.assertFalse(sw.allow("x"))
        self.assertTrue(sw.allow("y"))


class TestSlidingWindowCounter(unittest.TestCase):
    def test_basic(self):
        sc = SlidingWindowCounter(max_requests=5, window_sec=1.0)
        for _ in range(5):
            self.assertTrue(sc.allow())
        self.assertFalse(sc.allow())

    def test_window_advance(self):
        sc = SlidingWindowCounter(max_requests=2, window_sec=0.3)
        self.assertTrue(sc.allow())
        self.assertTrue(sc.allow())
        self.assertFalse(sc.allow())
        time.sleep(0.65)
        self.assertTrue(sc.allow())


class TestInvalidArgs(unittest.TestCase):
    def test_token_bucket_invalid(self):
        with self.assertRaises(ValueError):
            TokenBucket(0, 1.0)
        with self.assertRaises(ValueError):
            TokenBucket(5, -1.0)

    def test_sliding_window_invalid(self):
        with self.assertRaises(ValueError):
            SlidingWindowLog(-1, 1.0)
        with self.assertRaises(ValueError):
            SlidingWindowCounter(5, 0)


if __name__ == "__main__":
    unittest.main()
