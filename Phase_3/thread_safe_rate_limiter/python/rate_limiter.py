"""
Thread-Safe Rate Limiter - Complete Solution (Python)
Implements Token Bucket and Sliding Window rate limiting algorithms.
Concurrency: All state guarded by threading.Lock for thread-safe access.
"""
import time
import threading
from collections import deque
from abc import ABC, abstractmethod


class RateLimiter(ABC):
    """Abstract base for rate limiters."""
    @abstractmethod
    def allow(self, key: str = "default") -> bool:
        """Return True if request is allowed, False otherwise."""
        ...


class TokenBucket(RateLimiter):
    """
    Token Bucket algorithm.
    - Bucket fills at `refill_rate` tokens/sec up to `capacity`.
    - Each allow() consumes 1 token.
    """
    def __init__(self, capacity: int, refill_rate: float):
        if capacity <= 0 or refill_rate < 0:
            raise ValueError("capacity and refill_rate must be positive")
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._lock = threading.Lock()
        self._buckets: dict[str, tuple[float, float]] = {}  # key -> (tokens, last_refill)

    def allow(self, key: str = "default") -> bool:
        with self._lock:
            now = time.monotonic()
            tokens, last = self._buckets.get(key, (self._capacity, now))
            elapsed = now - last
            tokens = min(self._capacity, tokens + elapsed * self._refill_rate)
            if tokens >= 1.0:
                self._buckets[key] = (tokens - 1.0, now)
                return True
            self._buckets[key] = (tokens, now)
            return False


class SlidingWindowLog(RateLimiter):
    """
    Sliding Window Log algorithm.
    - Allows up to `max_requests` in the trailing `window_sec` seconds.
    - Stores exact timestamps of each allowed request.
    """
    def __init__(self, max_requests: int, window_sec: float):
        if max_requests <= 0 or window_sec <= 0:
            raise ValueError("max_requests and window_sec must be positive")
        self._max = max_requests
        self._window = window_sec
        self._lock = threading.Lock()
        self._logs: dict[str, deque[float]] = {}

    def allow(self, key: str = "default") -> bool:
        with self._lock:
            now = time.monotonic()
            log = self._logs.setdefault(key, deque())
            cutoff = now - self._window
            while log and log[0] <= cutoff:
                log.popleft()
            if len(log) < self._max:
                log.append(now)
                return True
            return False


class SlidingWindowCounter(RateLimiter):
    """
    Sliding Window Counter (approximate) algorithm.
    - Two fixed windows: previous and current.
    - Weighted count = prev_count * overlap_ratio + current_count.
    """
    def __init__(self, max_requests: int, window_sec: float):
        if max_requests <= 0 or window_sec <= 0:
            raise ValueError("max_requests and window_sec must be positive")
        self._max = max_requests
        self._window = window_sec
        self._lock = threading.Lock()
        # key -> (prev_count, curr_count, window_start)
        self._state: dict[str, tuple[int, int, float]] = {}

    def allow(self, key: str = "default") -> bool:
        with self._lock:
            now = time.monotonic()
            prev_c, curr_c, win_start = self._state.get(key, (0, 0, now))
            # advance window(s)
            elapsed_windows = int((now - win_start) / self._window)
            if elapsed_windows >= 2:
                prev_c, curr_c = 0, 0
                win_start = now
            elif elapsed_windows == 1:
                prev_c = curr_c
                curr_c = 0
                win_start += self._window
            # weighted estimate
            position_in_window = (now - win_start) / self._window
            weight = max(0.0, 1.0 - position_in_window)
            estimated = prev_c * weight + curr_c
            if estimated < self._max:
                curr_c += 1
                self._state[key] = (prev_c, curr_c, win_start)
                return True
            self._state[key] = (prev_c, curr_c, win_start)
            return False
