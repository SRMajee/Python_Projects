"""Tests for Pub-Sub Message Broker."""
import threading
import unittest
from broker import Broker


class TestBroker(unittest.TestCase):
    def setUp(self):
        self.broker = Broker()
        self.broker.create_topic("orders", num_partitions=3)

    def test_publish_and_consume(self):
        self.broker.publish("orders", "user1", {"item": "laptop", "qty": 1})
        self.broker.publish("orders", "user2", {"item": "phone", "qty": 2})
        cg = self.broker.subscribe("orders", "analytics")
        msgs = cg.poll()
        self.assertEqual(len(msgs), 2)
        values = [m.value for m in msgs]
        self.assertIn({"item": "laptop", "qty": 1}, values)

    def test_consumer_group_isolation(self):
        self.broker.publish("orders", None, "msg1")
        self.broker.publish("orders", None, "msg2")
        cg1 = self.broker.subscribe("orders", "group_a")
        cg2 = self.broker.subscribe("orders", "group_b")
        msgs1 = cg1.poll()
        msgs2 = cg2.poll()
        self.assertEqual(len(msgs1), 2)
        self.assertEqual(len(msgs2), 2)

    def test_offset_tracking(self):
        for i in range(5):
            self.broker.publish("orders", "k", f"val_{i}")
        cg = self.broker.subscribe("orders", "tracker")
        batch1 = cg.poll(max_msgs=2)
        batch2 = cg.poll(max_msgs=10)
        all_vals = [m.value for m in batch1 + batch2]
        self.assertEqual(all_vals, ["val_0", "val_1", "val_2", "val_3", "val_4"])

    def test_key_partitioning(self):
        topic = self.broker.get_topic("orders")
        p1, _ = self.broker.publish("orders", "same_key", "a")
        p2, _ = self.broker.publish("orders", "same_key", "b")
        self.assertEqual(p1, p2)  # same key -> same partition

    def test_seek(self):
        for i in range(3):
            self.broker.publish("orders", "k", f"v{i}")
        cg = self.broker.subscribe("orders", "seeker")
        cg.poll()
        pid = hash("k") % 3
        cg.seek(pid, 0)
        msgs = cg.poll()
        vals = [m.value for m in msgs]
        self.assertIn("v0", vals)

    def test_duplicate_topic(self):
        with self.assertRaises(ValueError):
            self.broker.create_topic("orders")

    def test_missing_topic(self):
        with self.assertRaises(KeyError):
            self.broker.publish("nonexistent", None, "x")

    def test_thread_safety(self):
        results = []
        def producer(n):
            for i in range(50):
                self.broker.publish("orders", None, f"p{n}_{i}")
        def consumer(group):
            import time
            time.sleep(0.05)
            cg = self.broker.subscribe("orders", group)
            msgs = cg.poll(max_msgs=200)
            results.append(len(msgs))
        threads = []
        for i in range(4):
            threads.append(threading.Thread(target=producer, args=(i,)))
        threads.append(threading.Thread(target=consumer, args=("test_group",)))
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # Consumer should have gotten some messages (timing dependent)
        self.assertGreater(sum(results), 0)


if __name__ == "__main__":
    unittest.main()
