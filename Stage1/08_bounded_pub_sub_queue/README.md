# Problem 08: Bounded Pub-Sub Worker Pool with Backpressure

## 1. What This Solution Does (The 30-Second Pitch)
This module implements a thread-safe, bounded Multi-Producer Multi-Consumer (MPMC) Pub-Sub worker pool with explicit backpressure and deterministic graceful shutdown. In high-velocity asynchronous architectures like Stripe's webhook delivery system or Rippling's payroll notification pipelines, unbounded queues inevitably cause memory ballooning when producers outpace consumers.

Using Python's standard `queue.Queue(maxsize=N)`, this system applies backpressure to producers, dispatches messages to topic subscribers, isolates handler failures, and guarantees zero message loss during shutdown via sentinel poison pills and `queue.join()`.

**Core Invariants Enforced:**
1. **Producer Backpressure:** If consumer workers fall behind and the queue reaches capacity, `publish()` blocks or times out rather than allocating unbounded memory.
2. **Zero Dropped In-Flight Messages:** The shutdown sequence executes `queue.join()` first, ensuring all published tasks complete processing before worker threads are terminated.
3. **Deadlock-Free Thread Termination:** Injects exactly one unique sentinel poison pill (`_SHUTDOWN_SENTINEL = object()`) per worker thread to break worker loops deterministically.

---

## 2. How to Think About This Problem (First-Principles Mental Model)

### The Trigger
Reach for this pattern when the interviewer says:
> *"Build an in-memory Pub-Sub worker pool with multiple worker threads and a bounded queue. Enforce backpressure on publishers when full. Implement a graceful shutdown mechanism that processes all remaining tasks and terminates threads cleanly without dropping messages or deadlocking."*

### Why Naive Approaches Fail
- **Using an unbounded queue (`queue.Queue()`):** Without `maxsize`, publishing 1,000,000 events when downstream workers are slow will consume gigabytes of memory until the OS terminates the process.
- **Using `thread.is_alive()` flags for shutdown:** Setting a `self._running = False` flag fails because idle worker threads are blocked on `self._queue.get()`! They will never wake up to check the boolean flag, creating a permanent deadlock.
- **Putting a single poison pill:** If you have 4 worker threads and put 1 poison pill, only the first worker receives it and exits. The other 3 remain blocked forever. You must enqueue **one sentinel per worker thread**.
- **Crashing the worker on handler exception:** If a subscriber throws an unhandled exception, a naive worker loop crashes, reducing your worker pool capacity until no workers remain.

### The Architecture
```
Producer 1 ──┐
Producer 2 ──┼──> publish(topic, payload) [queue.put(block=True, timeout=T)]
Producer 3 ──┘           │
                         ▼
             [ Bounded queue.Queue(maxsize) ]  <── BACKPRESSURE
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
    Worker 0         Worker 1         Worker 2
  _worker_loop()   _worker_loop()   _worker_loop()
        │
        ├── Item is _SHUTDOWN_SENTINEL? ──> break & exit thread
        └── Dispatch to topic subscribers:
              handlers = _subscribers[topic]
              for h in handlers: h(payload)  [isolated try/except]
              _queue.task_done()
```

---

## 3. How to Read the Code (`solution.py` Walkthrough)

### Sentinel & Pool Initialization (Lines 22–52)
- **Line 22 (`_SHUTDOWN_SENTINEL = object()`):**
  Uses a unique object reference. Using `None` as a sentinel is a classic bug because callers might want to publish `None` as a valid payload. `object()` identity is guaranteed unique.
- **Lines 31–51 (`__init__`):**
  Instantiates bounded `queue.Queue(maxsize=max_queue_size)`.
  Spawns `num_workers` daemon threads running `self._worker_loop`.
  Maintains subscriber registry protected by `_sub_lock`.

### Publishing with Backpressure (Lines 60–72)
- Checks `self._is_shutdown` to prevent post-shutdown ingestion.
- Calls `self._queue.put((topic, payload), block=True, timeout=timeout)`.
- If queue is saturated and `timeout` expires, catches `queue.Full` and returns `False` (backpressure signal to caller).

### Worker Loop & Fault Isolation (Lines 74–94)
- **Line 77 (`self._queue.get()`):** Blocks until a message or sentinel arrives.
- **Lines 80–81 (Poison Pill Check):** If `item is _SHUTDOWN_SENTINEL`, breaks loop to exit thread cleanly.
- **Lines 87–92 (Subscriber Error Containment):** Wraps handler execution in `try/except Exception`. A buggy subscriber cannot crash the worker thread.
- **Line 94 (`finally: self._queue.task_done()`):** Mandatory to decrement `queue.Queue`'s unfinished task counter, whether processing succeeded, failed, or was a sentinel.

### Graceful Shutdown Lifecycle (Lines 96–116)
1. Acquires lock and sets `self._is_shutdown = True`.
2. Calls `self._queue.join()`: blocks until every task has had its `task_done()` called.
3. Enqueues `_SHUTDOWN_SENTINEL` exactly `num_workers` times.
4. Calls `worker.join(timeout=2.0)` on every thread.

---

## 4. How to Write It in a Live Interview (Step-by-Step Execution Order)

### Step 1: Skeleton & Core Data Structures (Mins 0–10)
Set up sentinel, queue, and worker thread spawning:
```python
import queue, threading

_SENTINEL = object()

class BoundedPubSubPool:
    def __init__(self, num_workers=4, max_queue_size=16):
        self.num_workers = num_workers
        self._queue = queue.Queue(maxsize=max_queue_size)
        self._subscribers = {}
        self._is_shutdown = False
        self._workers = []
        for i in range(num_workers):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            self._workers.append(t)
```

### Step 2: The Happy Path Core Logic (Mins 10–22)
Implement topic subscription, publishing, and the worker loop:
- In `publish`: call `self._queue.put((topic, payload))`.
- In `_worker_loop`: `item = self._queue.get()`, check sentinel, dispatch to handlers, call `self._queue.task_done()`.

### Step 3: Edge Cases, Concurrency & Safety Invariants (Mins 22–35)
Now add the Staff-level safety guarantees:
- Backpressure: accept optional `timeout` in `publish()` and catch `queue.Full`.
- Error isolation: wrap subscriber invocation in `try...except Exception` so rogue handlers don't crash workers.
- Graceful shutdown:
  1. `self._queue.join()` (drains all user work).
  2. Enqueue `_SENTINEL` `num_workers` times.
  3. `worker.join()` on each thread.
  4. Ensure `self._queue.task_done()` is also called for the sentinel!

### Step 4: Verification Driver (Mins 35–45)
Write concurrent test scenarios in `if __name__ == "__main__":`:
1. Publish/subscribe happy path.
2. Backpressure test: block consumers via an event, fill queue to capacity, verify overflow publish returns `False`.
3. Multi-producer stress test: spawn 4 concurrent producer threads publishing 25 tasks each (100 total).
4. Call `shutdown(drain=True)` and assert exactly 100 tasks were processed with zero loss and all threads joined.

---

## 5. Must-Memorize Syntax & Idioms (The Cheat Sheet)

```python
# 1. Unique object identity for poison-pill sentinels
_SHUTDOWN_SENTINEL = object()
if item is _SHUTDOWN_SENTINEL:  # Fast identity check; cannot collide with user data
    break

# 2. Bounded Queue with backpressure
q = queue.Queue(maxsize=10)
try:
    q.put(item, block=True, timeout=0.1)
except queue.Full:
    # apply backpressure / shed load
    pass

# 3. Draining work before shutdown
q.join()  # Blocks until every item put into queue has called q.task_done()

# 4. Terminating N worker threads cleanly
for _ in range(num_workers):
    q.put(_SHUTDOWN_SENTINEL)
for w in workers:
    w.join()
```

---

## 6. Common Traps & Follow-Up Curveballs

### 3 Mistakes That Fail the Interview
1. **Forgetting `task_done()` on Sentinel Consumption:** If you put sentinels into the queue and exit without calling `task_done()`, any subsequent `queue.join()` will hang indefinitely.
2. **Calling `queue.join()` AFTER Enqueuing Sentinels:** If you enqueue sentinels *before* `queue.join()`, workers might process sentinels first and exit while pending user tasks are still waiting in the queue! Always drain user tasks with `queue.join()` *before* enqueuing sentinels (or count remaining tasks).
3. **Using `None` as a Sentinel:** If a user publishes `broker.publish("alerts", None)`, a worker treating `None` as a shutdown signal will exit prematurely.

### 2 Bar-Raiser Follow-Ups
1. **"What happens if a subscriber handler hangs indefinitely?"**
   *Answer:* The worker thread remains blocked. To mitigate, either execute handlers within a `concurrent.futures.ThreadPoolExecutor` with a timeout, or enforce per-handler deadline timeouts using non-blocking futures.
2. **"How do you implement topic wildcard routing (e.g., `orders.*` or `orders.eu.#`)?"**
   *Answer:* Store subscriptions in a Trie or prefix tree where nodes represent topic tokens. When publishing `orders.eu.created`, traverse the Trie matching both exact tokens and wildcard tokens (`*` for single word, `#` for recursive subtree).
