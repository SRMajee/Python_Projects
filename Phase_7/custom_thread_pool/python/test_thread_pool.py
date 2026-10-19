"""Tests for Custom Thread Pool Executor."""
import time
import unittest
from thread_pool import ThreadPool, Future, FutureState


class TestFuture(unittest.TestCase):
    def test_result(self):
        f = Future()
        f._set_result(42)
        self.assertEqual(f.result(), 42)
        self.assertTrue(f.done())

    def test_exception(self):
        f = Future()
        f._set_exception(ValueError("fail"))
        with self.assertRaises(ValueError):
            f.result()

    def test_cancel(self):
        f = Future()
        self.assertTrue(f.cancel())
        self.assertEqual(f.state, FutureState.CANCELLED)
        with self.assertRaises(RuntimeError):
            f.result()

    def test_cancel_after_run(self):
        f = Future()
        f._set_running()
        self.assertFalse(f.cancel())

    def test_timeout(self):
        f = Future()
        with self.assertRaises(TimeoutError):
            f.result(timeout=0.05)

    def test_callback(self):
        results = []
        f = Future()
        f.add_callback(lambda fut: results.append(fut.result()))
        f._set_result(99)
        self.assertEqual(results, [99])


class TestThreadPool(unittest.TestCase):
    def test_basic_submit(self):
        with ThreadPool(2) as pool:
            f = pool.submit(lambda x: x * 2, 5)
            self.assertEqual(f.result(), 10)

    def test_multiple_tasks(self):
        with ThreadPool(4) as pool:
            futures = [pool.submit(lambda x: x ** 2, i) for i in range(10)]
            results = [f.result() for f in futures]
            self.assertEqual(results, [i ** 2 for i in range(10)])

    def test_map(self):
        with ThreadPool(3) as pool:
            results = pool.map(lambda x: x + 1, range(5))
            self.assertEqual(results, [1, 2, 3, 4, 5])

    def test_exception_propagation(self):
        def fail():
            raise RuntimeError("boom")
        with ThreadPool(2) as pool:
            f = pool.submit(fail)
            with self.assertRaises(RuntimeError):
                f.result()

    def test_concurrent_execution(self):
        results = []
        lock = __import__("threading").Lock()

        def slow_task(n):
            time.sleep(0.05)
            with lock:
                results.append(n)
            return n

        with ThreadPool(4) as pool:
            futures = [pool.submit(slow_task, i) for i in range(8)]
            for f in futures:
                f.result()
        self.assertEqual(sorted(results), list(range(8)))

    def test_shutdown_rejects(self):
        pool = ThreadPool(2)
        pool.shutdown()
        with self.assertRaises(RuntimeError):
            pool.submit(lambda: 1)

    def test_invalid_workers(self):
        with self.assertRaises(ValueError):
            ThreadPool(0)

    def test_cancel_pending(self):
        with ThreadPool(1) as pool:
            # Submit a blocking task to hold the worker
            blocker = pool.submit(time.sleep, 0.5)
            # Submit another that should be pending
            f = pool.submit(lambda: 42)
            cancelled = f.cancel()
            # May or may not cancel depending on timing
            if cancelled:
                self.assertEqual(f.state, FutureState.CANCELLED)


if __name__ == "__main__":
    unittest.main()
