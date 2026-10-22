"""
Problem 07: Thread-Safe Token Bucket Rate Limiter
Phase: GIL & Threading (Target: 80-120 LOC)

Staff Engineer Design Notes:
- Concurrency & Thread-Safety: Explicitly synchronizes state mutations using `threading.Condition`.
- Elimination of Busy-Waiting: Computes deterministic sleep durations based on required token deficits,
  waiting on the condition variable instead of burning CPU cycles in spin-loops.
- Precision Timing: Employs `time.monotonic()` to guard against system wall-clock adjustments / NTP shifts.
- Dual Ingestion Modes:
  1. Non-blocking `try_acquire(tokens)` for fast shedding / 429 Too Many Requests responses.
  2. Blocking `acquire(tokens, timeout)` with precise deadline expiration for queueing / pacing clients.
"""

import threading
import time


class TokenBucketRateLimiter:
    """Thread-safe Token Bucket rate limiter supporting blocking and non-blocking acquisition."""

    def __init__(self, capacity: float, refill_rate: float) -> None:
        if capacity <= 0 or refill_rate <= 0:
            raise ValueError("Capacity and refill_rate must be strictly positive")

        self.capacity: float = float(capacity)
        self.refill_rate: float = float(refill_rate)
        self.tokens: float = float(capacity)
        self.last_refill_time: float = time.monotonic()
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)

    def _refill_unlocked(self) -> None:
        """Recalculate token balance based on monotonic elapsed time. Must be called with lock held."""
        now = time.monotonic()
        elapsed = now - self.last_refill_time
        if elapsed > 0:
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill_time = now

    def try_acquire(self, tokens: float = 1.0) -> bool:
        """Non-blocking token acquisition. Returns True if acquired, False otherwise."""
        if tokens <= 0:
            raise ValueError("Tokens to acquire must be positive")
        if tokens > self.capacity:
            return False

        with self._condition:
            self._refill_unlocked()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def acquire(self, tokens: float = 1.0, timeout: float | None = None) -> bool:
        """
        Blocking token acquisition with zero busy-waiting.
        Calculates required sleep interval and sleeps via Condition.wait().
        """
        if tokens <= 0:
            raise ValueError("Tokens to acquire must be positive")
        if tokens > self.capacity:
            return False  # Cannot ever satisfy a request larger than bucket capacity

        deadline = (time.monotonic() + timeout) if timeout is not None else None

        with self._condition:
            while True:
                self._refill_unlocked()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                now = time.monotonic()
                if deadline is not None and now >= deadline:
                    return False

                # Calculate exact seconds until enough tokens will have refilled
                deficit = tokens - self.tokens
                wait_time = deficit / self.refill_rate

                if deadline is not None:
                    remaining = deadline - now
                    if remaining <= 0:
                        return False
                    wait_time = min(wait_time, remaining)

                # Sleep on condition variable; releases lock so other threads can operate
                self._condition.wait(timeout=wait_time)


# ---------------------------------------------------------------------------
# Verification & Test Scenarios
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # 1. Non-blocking acquisition & burst capacity exhaustion
    limiter = TokenBucketRateLimiter(capacity=5.0, refill_rate=10.0)

    # Burst take 5 tokens immediately
    assert limiter.try_acquire(5.0) is True
    # Immediate next acquisition must fail
    assert limiter.try_acquire(1.0) is False

    # Wait 0.15s -> should refill ~1.5 tokens
    time.sleep(0.15)
    assert limiter.try_acquire(1.0) is True
    assert limiter.try_acquire(1.0) is False  # Only ~0.5 tokens left

    # 2. Blocking acquire with timeout
    slow_limiter = TokenBucketRateLimiter(capacity=2.0, refill_rate=2.0)
    assert slow_limiter.try_acquire(2.0) is True

    # Needs 1 token -> takes 0.5s. Timeout of 0.1s must fail.
    start = time.monotonic()
    acquired = slow_limiter.acquire(1.0, timeout=0.1)
    duration = time.monotonic() - start
    assert acquired is False
    assert 0.09 <= duration <= 0.2

    # Timeout of 0.6s must succeed in ~0.5s
    start = time.monotonic()
    acquired = slow_limiter.acquire(1.0, timeout=0.6)
    duration = time.monotonic() - start
    assert acquired is True
    assert 0.4 <= duration <= 0.7

    # 3. High-contention concurrent threads test
    # 8 threads competing for 8 tokens at refill rate 20 tokens/sec
    concurrent_limiter = TokenBucketRateLimiter(capacity=4.0, refill_rate=20.0)
    successful_acquisitions = 0
    lock = threading.Lock()

    def worker():
        global successful_acquisitions
        if concurrent_limiter.acquire(1.0, timeout=0.5):
            with lock:
                successful_acquisitions += 1

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All 8 threads should have acquired tokens cleanly without deadlocks or race conditions
    assert successful_acquisitions == 8

    print("07_thread_safe_token_bucket: All assertions passed successfully.")
