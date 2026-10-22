# Problem 07: Thread-Safe Token Bucket Rate Limiter

## 1. What This Solution Does (The 30-Second Pitch)
This module implements a production-grade, thread-safe Token Bucket rate limiter using Python's `threading.Condition` and `time.monotonic()`. Rate limiters are ubiquitous at API-first companies like Stripe (protecting billing endpoints from payment abuse) and Rippling (protecting payroll submission services).

The algorithm permits instantaneous traffic bursts up to a configured `capacity` while continuously replenishing tokens at a steady `refill_rate` (tokens per second). It supports both **non-blocking** acquisition (`try_acquire` for immediate 429 throttling) and **blocking** acquisition (`acquire` with timeouts for client request pacing and queue smoothing).

**Core Invariants Enforced:**
1. **Zero Busy-Waiting (No Spin-Loops):** When tokens are unavailable, threads do not spin in CPU-intensive loops; they deterministically calculate the token deficit sleep duration and wait on a `threading.Condition`.
2. **Race-Condition-Free State Updates:** All balance refills and token subtractions are synchronized under a mutex lock.
3. **Clock-Drift Immunity:** Uses `time.monotonic()` to guarantee monotonic time deltas, preventing token miscalculations during system wall-clock or NTP adjustments.

---

## 2. How to Think About This Problem (First-Principles Mental Model)

### The Trigger
Reach for this pattern when the interviewer says:
> *"Design a thread-safe Token Bucket rate limiter. Support both non-blocking try-acquire and blocking acquire with timeouts. Eliminate race conditions and ensure threads do not busy-wait in spin-loops."*

### Why Naive Approaches Fail
- **Background Refill Threads:** Spawning a daemon thread that does `while True: time.sleep(1/rate); tokens += 1` is wasteful and drifts over time due to OS scheduling latency. Top candidates calculate refills **lazily on-demand** based on `elapsed = now - last_refill_time`.
- **Busy-Wait Spin Loops:** Writing `while not try_acquire(): time.sleep(0.01)` burns CPU cycles, creates unnecessary lock contention, and introduces random latency jitter.
- **Using `time.time()`:** Wall-clock time can jump backwards during NTP syncs, producing negative elapsed intervals that corrupt token calculations.

### The Architecture
```
Thread A ──┐
Thread B ──┼──> acquire(tokens, timeout)
Thread C ──┘           │
                       ▼
          [threading.Condition(lock)]
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
1. Lazy Refill                 2. Check Balance
   elapsed = now - last_time      tokens >= requested?
   tokens = min(cap, tokens +     ├── YES: tokens -= requested; RETURN TRUE
            elapsed * rate)       └── NO:
                                       ├── now >= deadline? RETURN FALSE
                                       ├── wait_time = deficit / refill_rate
                                       └── condition.wait(wait_time)
```

---

## 3. How to Read the Code (`solution.py` Walkthrough)

### Class Initialization & Synchronization Primitives (Lines 19–32)
- **Lines 26–31:**
  Initializes `capacity`, `refill_rate`, `tokens`, and records `last_refill_time = time.monotonic()`.
  Creates `self._lock = threading.Lock()` and wraps it with `self._condition = threading.Condition(self._lock)`.

### Lazy Refill Engine (Lines 33–40)
- **`_refill_unlocked()`:**
  Private helper that must be called while holding the lock.
  Calculates `elapsed = now - self.last_refill_time`.
  Caps accumulated tokens at `self.capacity` using `min(self.capacity, self.tokens + elapsed * self.refill_rate)`.
  Updates `self.last_refill_time = now`.

### Non-Blocking `try_acquire` (Lines 41–54)
- Acquires `self._condition` (which acquires the underlying lock).
- Lazily refills tokens.
- If `tokens >= requested`, deducts and returns `True`. Otherwise returns `False` immediately without blocking.

### Blocking `acquire` with Zero Busy-Waiting (Lines 55–90)
- **Line 65 (`deadline`):** Computes absolute deadline `time.monotonic() + timeout`.
- **Lines 67–89 (`while True` with Condition.wait):**
  - Refills tokens and checks availability.
  - If tokens are insufficient, checks whether `now >= deadline`.
  - **The Key Calculation (Lines 79–80):** Computes `deficit = tokens - self.tokens` and `wait_time = deficit / self.refill_rate`.
  - Clamps `wait_time = min(wait_time, remaining_to_deadline)`.
  - Calls `self._condition.wait(timeout=wait_time)`. This atomically releases the lock, puts the thread to sleep, and wakes up when the timeout expires or when notified.

---

## 4. How to Write It in a Live Interview (Step-by-Step Execution Order)

### Step 1: Skeleton & Core Data Structures (Mins 0–10)
Stub class with `Condition` and explain lazy refill:
```python
import threading, time

class TokenBucketRateLimiter:
    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self.tokens = float(capacity)
        self.last_refill_time = time.monotonic()
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
```

### Step 2: The Happy Path Core Logic (Mins 10–22)
Implement lazy refill and non-blocking `try_acquire`:
```python
def _refill_unlocked(self):
    now = time.monotonic()
    elapsed = now - self.last_refill_time
    if elapsed > 0:
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill_time = now

def try_acquire(self, tokens=1.0) -> bool:
    with self._condition:
        self._refill_unlocked()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
```

### Step 3: Edge Cases, Concurrency & Safety Invariants (Mins 22–35)
Implement blocking `acquire` using condition variables:
- Reject `tokens > capacity` immediately (can never be fulfilled).
- Loop with condition wait: calculate exact deficit duration `wait_time = deficit / refill_rate`.
- Handle deadline expiration: `if deadline and now >= deadline: return False`.
- Avoid spin-waiting by calling `self._condition.wait(timeout=wait_time)`.

### Step 4: Verification Driver (Mins 35–45)
Write concurrent test scenarios in `if __name__ == "__main__":`:
1. Burst capacity: verify acquiring capacity succeeds and the next instant acquire fails.
2. Refill precision: sleep 0.15s and verify exact partial token recovery.
3. Timeout behavior: request token with tight timeout and verify timeout expires within expected delta.
4. Concurrent multi-threading test: spawn 8 worker threads competing for tokens and verify zero race conditions.

---

## 5. Must-Memorize Syntax & Idioms (The Cheat Sheet)

```python
# 1. Condition Variable initialized with an explicit Lock
lock = threading.Lock()
condition = threading.Condition(lock)

# 2. Waiting on Condition with timeout (releases lock while sleeping)
with condition:
    # must re-check predicate in a while loop to guard against spurious wakeups
    while not predicate():
        if timeout_expired():
            return False
        condition.wait(timeout=calculated_duration)

# 3. Monotonic time calculations
start = time.monotonic()
elapsed = time.monotonic() - start

# 4. Lazy token bucket accumulation
tokens = min(capacity, tokens + elapsed * refill_rate)
```

---

## 6. Common Traps & Follow-Up Curveballs

### 3 Mistakes That Fail the Interview
1. **Busy-waiting with `time.sleep()` inside the lock:** Writing `with self.lock: while not ready: time.sleep(0.01)` holds the mutex lock while sleeping! No other thread can acquire or query tokens.
2. **Spurious Wakeup Vulnerability:** Using `if not condition:` instead of `while not condition:` before consuming tokens. Condition variables can wake up spuriously or another thread might acquire the tokens first.
3. **Allowing `tokens > capacity` to block indefinitely:** If bucket capacity is 5 and a caller requests 10 tokens, it will wait forever unless guarded upfront.

### 2 Bar-Raiser Follow-Ups
1. **"How do you implement fair queuing (FIFO) so starving threads don't get bypassed by newer threads?"**
   *Answer:* Maintain a wait-queue of tickets or `threading.Event` objects in a deque. A thread enters the queue, and only the head of the queue is signaled when sufficient tokens accumulate.
2. **"How do you adapt this Token Bucket to a distributed system across 50 server nodes?"**
   *Answer:* Use Redis with a Lua script executing the identical lazy-refill calculation atomically. Store `{ "last_updated": timestamp, "tokens": current_tokens }` under the client's Redis key, running the delta math on every call in Redis single-threaded memory.
