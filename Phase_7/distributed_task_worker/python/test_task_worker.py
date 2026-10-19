"""Tests for Distributed Task Worker."""
import time
import unittest
from task_worker import DistributedTaskWorker


def square(x):
    return x * x


def slow_add(a, b):
    time.sleep(0.1)
    return a + b


def failing_task():
    raise ValueError("intentional failure")


def flaky_task(state):
    """Succeeds on 3rd attempt via shared state workaround."""
    # In real scenario, external state would track retries
    return "success"


class TestDistributedTaskWorker(unittest.TestCase):
    def test_basic_submit(self):
        dtw = DistributedTaskWorker(num_workers=2)
        dtw.start({"square": square})
        tid = dtw.submit("square", 7)
        result = dtw.get_result(tid, timeout=5)
        self.assertIsNotNone(result)
        self.assertEqual(result["state"], "SUCCESS")
        self.assertEqual(result["result"], 49)
        dtw.shutdown()

    def test_multiple_tasks(self):
        dtw = DistributedTaskWorker(num_workers=4)
        dtw.start({"square": square})
        tids = [dtw.submit("square", i) for i in range(10)]
        results = [dtw.get_result(tid, timeout=5) for tid in tids]
        for i, r in enumerate(results):
            self.assertEqual(r["result"], i * i)
        dtw.shutdown()

    def test_slow_concurrent(self):
        dtw = DistributedTaskWorker(num_workers=4)
        dtw.start({"slow_add": slow_add})
        tids = [dtw.submit("slow_add", i, i + 1) for i in range(8)]
        results = [dtw.get_result(tid, timeout=10) for tid in tids]
        for i, r in enumerate(results):
            self.assertEqual(r["result"], i + (i + 1))
        dtw.shutdown()

    def test_failure(self):
        dtw = DistributedTaskWorker(num_workers=2)
        dtw.start({"fail": failing_task})
        tid = dtw.submit("fail")
        result = dtw.get_result(tid, timeout=5)
        self.assertEqual(result["state"], "FAILURE")
        self.assertIn("intentional", result["error"])
        dtw.shutdown()

    def test_unknown_task(self):
        dtw = DistributedTaskWorker(num_workers=1)
        dtw.start({"square": square})
        tid = dtw.submit("nonexistent")
        result = dtw.get_result(tid, timeout=5)
        self.assertEqual(result["state"], "FAILURE")
        self.assertIn("Unknown", result["error"])
        dtw.shutdown()

    def test_invalid_workers(self):
        with self.assertRaises(ValueError):
            DistributedTaskWorker(num_workers=0)


if __name__ == "__main__":
    unittest.main()
