"""
Problem 08: Bounded Pub-Sub Worker Pool with Backpressure
Phase: GIL & Threading (Target: 100-150 LOC)

Staff Engineer Design Notes:
- Multi-Producer, Multi-Consumer architecture with bounded queue backpressure (`queue.Queue(maxsize)`).
- Dedicated worker pool initialized with daemon threads.
- Graceful shutdown lifecycle:
  1. Blocks until all pending tasks are processed (`queue.join()`).
  2. Injects deterministic poison-pill sentinels (one per worker).
  3. Joins all worker threads cleanly, ensuring zero dropped messages or deadlocks.
- Thread-safe topic dispatching with isolated subscriber error containment.
"""

from collections import defaultdict
from collections.abc import Callable
import queue
import threading
import time
from typing import Any

_SHUTDOWN_SENTINEL = object()


class BoundedPubSubPool:
    """
    Thread-safe Bounded Pub-Sub broker and worker pool.
    Exerts backpressure on producers when queue capacity is saturated.
    """

    def __init__(self, num_workers: int = 4, max_queue_size: int = 16) -> None:
        if num_workers <= 0 or max_queue_size <= 0:
            raise ValueError("num_workers and max_queue_size must be positive integers")

        self.max_queue_size = max_queue_size
        self.num_workers = num_workers
        self._queue: queue.Queue[Any] = queue.Queue(maxsize=max_queue_size)
        self._subscribers: dict[str, list[Callable[[Any], None]]] = defaultdict(list)
        self._sub_lock = threading.Lock()
        self._is_shutdown = False
        self._workers: list[threading.Thread] = []

        # Spawn worker threads
        for i in range(num_workers):
            t = threading.Thread(
                target=self._worker_loop,
                name=f"PubSubWorker-{i}",
                daemon=True,
            )
            t.start()
            self._workers.append(t)

    def subscribe(self, topic: str, handler: Callable[[Any], None]) -> None:
        """Register a subscriber callback for a given topic."""
        with self._sub_lock:
            if self._is_shutdown:
                raise RuntimeError("Cannot subscribe to a shutdown broker")
            self._subscribers[topic].append(handler)

    def publish(self, topic: str, payload: Any, timeout: float | None = None) -> bool:
        """
        Publish message to bounded queue.
        Enforces backpressure: blocks if queue is full until space is freed or timeout elapses.
        """
        if self._is_shutdown:
            raise RuntimeError("Cannot publish to a shutdown broker")

        try:
            self._queue.put((topic, payload), block=True, timeout=timeout)
            return True
        except queue.Full:
            return False

    def _worker_loop(self) -> None:
        """Worker event loop consuming tasks until sentinel poison-pill is received."""
        while True:
            item = self._queue.get()
            try:
                # Poison-pill check for graceful shutdown
                if item is _SHUTDOWN_SENTINEL:
                    break

                topic, payload = item
                with self._sub_lock:
                    handlers = list(self._subscribers.get(topic, []))

                for handler in handlers:
                    try:
                        handler(payload)
                    except Exception as err:
                        # Log / contain subscriber failure without crashing worker thread
                        pass
            finally:
                self._queue.task_done()

    def shutdown(self, drain: bool = True) -> None:
        """
        Gracefully stop worker pool.
        Drains all queued items before sending poison pills and joining threads.
        """
        with self._sub_lock:
            if self._is_shutdown:
                return
            self._is_shutdown = True

        if drain:
            # Wait for all published tasks to finish processing
            self._queue.join()

        # Dispatch one poison pill per worker to exit their event loop
        for _ in range(self.num_workers):
            self._queue.put(_SHUTDOWN_SENTINEL)

        for worker in self._workers:
            worker.join(timeout=2.0)

    @property
    def pending_count(self) -> int:
        return self._queue.qsize()


# ---------------------------------------------------------------------------
# Verification & Test Scenarios
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    broker = BoundedPubSubPool(num_workers=3, max_queue_size=5)

    processed_orders: list[str] = []
    processed_audit: list[str] = []
    order_lock = threading.Lock()

    def order_handler(payload: str) -> None:
        with order_lock:
            processed_orders.append(payload)
        time.sleep(0.01)  # Simulate small work

    def audit_handler(payload: str) -> None:
        with order_lock:
            processed_audit.append(payload)

    # 1. Topic subscriptions
    broker.subscribe("orders:created", order_handler)
    broker.subscribe("orders:created", audit_handler)
    broker.subscribe("system:alert", audit_handler)

    # 2. Publish burst within queue bounds
    for i in range(5):
        assert broker.publish("orders:created", f"ord_{i}") is True

    # 3. Deterministically verify backpressure when consumers and bounded queue are full
    block_event = threading.Event()
    broker.subscribe("backpressure:test", lambda _: block_event.wait(timeout=2.0))

    # Saturate 3 workers + 5 queue capacity slots = 8 tasks
    for k in range(8):
        broker.publish("backpressure:test", f"task_{k}", timeout=0.5)

    # The 9th publish must hit backpressure and return False on timeout
    hit_backpressure = not broker.publish("backpressure:test", "overflow_task", timeout=0.02)
    assert hit_backpressure is True, "Backpressure must reject when bounded buffer is saturated"

    # Unblock consumers to drain tasks
    block_event.set()

    # 4. Multi-producer concurrency test
    producer_count = 4
    items_per_producer = 25
    delivered_payloads: set[str] = set()
    delivered_lock = threading.Lock()

    def tracking_handler(payload: str) -> None:
        with delivered_lock:
            delivered_payloads.add(payload)

    broker.subscribe("payments:settled", tracking_handler)

    def producer_task(prod_id: int):
        for idx in range(items_per_producer):
            # Blocking publish with adequate timeout
            broker.publish("payments:settled", f"prod_{prod_id}_{idx}", timeout=2.0)

    threads = [
        threading.Thread(target=producer_task, args=(p,))
        for p in range(producer_count)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 5. Graceful shutdown drains all tasks and joins workers
    broker.shutdown(drain=True)

    # Verify zero message loss for concurrent producers
    expected_total = producer_count * items_per_producer
    assert len(delivered_payloads) == expected_total

    # Verify workers exited cleanly
    for worker in broker._workers:
        assert not worker.is_alive()

    # Verify publishing after shutdown is disallowed
    try:
        broker.publish("orders:created", "late_message")
        assert False, "Should reject publish after shutdown"
    except RuntimeError as e:
        assert "Cannot publish to a shutdown broker" in str(e)

    print("08_bounded_pub_sub_queue: All assertions passed successfully.")
