"""
Problem 04: Advanced Retry and Memoization Decorators
Phase: Advanced OOP (Target: 60-90 LOC)

Staff Engineer Design Notes:
- Idiomatic closures and signature preservation using `functools.wraps`.
- `lru_ttl_cache`: Deterministic cache key generation with kwargs sorting,
  TTL expiration, LRU eviction via `collections.OrderedDict`, and introspectable stats.
- `retry`: Exponential backoff with optional full jitter, configurable attempt budget,
  and fine-grained retryable exception filtering.
"""

from collections import OrderedDict
from collections.abc import Callable
import functools
import random
import time
from typing import Any, NamedTuple


class CacheInfo(NamedTuple):
    hits: int
    misses: int
    maxsize: int
    currsize: int


def lru_ttl_cache(
    maxsize: int = 128,
    ttl_seconds: float | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """LRU Cache decorator with deterministic key hashing and TTL expiration."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        cache: OrderedDict[tuple[Any, tuple[tuple[str, Any], ...]], tuple[Any, float | None]] = OrderedDict()
        hits = 0
        misses = 0

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal hits, misses
            # Generate deterministic hashable key
            key = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()

            if key in cache:
                val, expires_at = cache[key]
                if expires_at is None or now < expires_at:
                    cache.move_to_end(key)
                    hits += 1
                    return val
                del cache[key]

            misses += 1
            result = func(*args, **kwargs)
            expires_at = now + ttl_seconds if ttl_seconds is not None else None

            if len(cache) >= maxsize and key not in cache:
                cache.popitem(last=False)  # Evict oldest entry

            cache[key] = (result, expires_at)
            return result

        def cache_clear() -> None:
            nonlocal hits, misses
            cache.clear()
            hits = misses = 0

        def cache_info() -> CacheInfo:
            return CacheInfo(hits=hits, misses=misses, maxsize=maxsize, currsize=len(cache))

        wrapper.cache_clear = cache_clear  # type: ignore[attr-defined]
        wrapper.cache_info = cache_info  # type: ignore[attr-defined]
        return wrapper

    return decorator


def retry(
    max_retries: int = 3,
    base_delay: float = 0.05,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Exponential backoff retry decorator with configurable jitter and exceptions."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions:
                    if attempt == max_retries:
                        raise
                    delay = base_delay * (backoff_factor ** attempt)
                    if jitter:
                        delay = random.uniform(0.5 * delay, delay)
                    time.sleep(delay)

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Verification & Test Scenarios
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # 1. Metadata and docstring preservation
    @lru_ttl_cache(maxsize=4, ttl_seconds=0.2)
    def fetch_user_data(user_id: int, include_meta: bool = False) -> str:
        """Simulate fetching remote user profile."""
        return f"user_{user_id}_{include_meta}"

    assert fetch_user_data.__name__ == "fetch_user_data"
    assert fetch_user_data.__doc__ == "Simulate fetching remote user profile."

    # 2. Cache hit / miss & deterministic kwargs order
    call_counter = 0

    @lru_ttl_cache(maxsize=2, ttl_seconds=1.0)
    def compute(a: int, b: int) -> int:
        global call_counter
        call_counter += 1
        return a + b

    assert compute(1, b=2) == 3
    assert compute(1, b=2) == 3  # Hit
    assert call_counter == 1
    info = compute.cache_info()  # type: ignore
    assert info.hits == 1 and info.misses == 1

    # 3. LRU Eviction: maxsize=2
    compute(2, b=3)  # len=2, miss 2
    compute(3, b=4)  # len=2, miss 3, evicts (1, b=2)
    assert compute.cache_info().currsize == 2
    compute(1, b=2)  # Evicted entry causes miss 4
    assert compute.cache_info().misses == 4

    # 4. TTL Expiration
    @lru_ttl_cache(maxsize=10, ttl_seconds=0.05)
    def fast_expiring() -> float:
        return time.monotonic()

    t1 = fast_expiring()
    assert fast_expiring() == t1  # Cache hit
    time.sleep(0.06)
    t2 = fast_expiring()  # Expired, new value
    assert t2 > t1

    # 5. Retry with exponential backoff on transient errors
    failures = 0

    @retry(max_retries=3, base_delay=0.01, backoff_factor=1.5, retryable_exceptions=(ConnectionError,))
    def flaky_network_call() -> str:
        global failures
        if failures < 2:
            failures += 1
            raise ConnectionError("Temporary DNS resolution failure")
        return "success"

    assert flaky_network_call() == "success"
    assert failures == 2

    # 6. Retry terminates and raises when budget exceeded
    @retry(max_retries=2, base_delay=0.01, retryable_exceptions=(ValueError,))
    def always_fails() -> None:
        raise ValueError("Permanent invalid argument")

    try:
        always_fails()
        assert False, "Should have raised after retry exhaustion"
    except ValueError as e:
        assert "Permanent invalid argument" in str(e)

    print("04_retry_memoization_decorators: All assertions passed successfully.")
