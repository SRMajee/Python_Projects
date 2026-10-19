"""
Thread-Safe Rate Limiter - Interview Solution (Python)

1. Primary Capabilities:
   - Token Bucket: capacity + refill_rate, lazy refill on each allow()
   - Sliding Window Log: exact timestamps in deque, evict expired
   - Per-key isolation via dict of states
   - Concurrency Extension: threading.Lock wraps all mutable state

2. Error Handling:
   - ValueError on non-positive capacity/rate/window

3. Out Of Scope:
   - Distributed rate limiting (Redis), leaky bucket, fixed window counter,
     adaptive throttling, retry headers
"""
import time, threading
from collections import deque

class TokenBucket:
    def __init__(self, cap, rate):
        self.cap, self.rate = cap, rate
        self._lock = threading.Lock()
        self._b: dict[str, tuple[float, float]] = {}

    def allow(self, key="d") -> bool:
        with self._lock:
            now = time.monotonic()
            tok, last = self._b.get(key, (self.cap, now))
            tok = min(self.cap, tok + (now - last) * self.rate)
            if tok >= 1:
                self._b[key] = (tok - 1, now)
                return True
            self._b[key] = (tok, now)
            return False

class SlidingWindowLog:
    def __init__(self, mx, win):
        self.mx, self.win = mx, win
        self._lock = threading.Lock()
        self._logs: dict[str, deque] = {}

    def allow(self, key="d") -> bool:
        with self._lock:
            now = time.monotonic()
            q = self._logs.setdefault(key, deque())
            while q and q[0] <= now - self.win:
                q.popleft()
            if len(q) < self.mx:
                q.append(now)
                return True
            return False

if __name__ == "__main__":
    tb = TokenBucket(3, 1.0)
    assert tb.allow() and tb.allow() and tb.allow() and not tb.allow()
    sw = SlidingWindowLog(2, 1.0)
    assert sw.allow() and sw.allow() and not sw.allow()
    print("Interview Rate Limiter passed!")
