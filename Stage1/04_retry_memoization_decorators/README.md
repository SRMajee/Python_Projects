# Problem 04: Retry & Memoization Decorators

## 1. What This Solution Does (The 30-Second Pitch)
This module provides two foundational production-grade decorators: a TTL/LRU memoization cache ([`lru_ttl_cache`](file:///c:/DRIVE%20D/Python_Projects/Stage1/04_retry_memoization_decorators/solution.py#L28)) and an exponential backoff retry mechanism ([`retry`](file:///c:/DRIVE%20D/Python_Projects/Stage1/04_retry_memoization_decorators/solution.py#L78)). In distributed systems at companies like Stripe and Rippling, remote API interactions are prone to transient network partitions and expensive downstream computations.

These decorators protect upstream callers by:
1. Memoizing function calls with deterministic argument hashing (handling permutations of `kwargs` cleanly) and automatically evicting both expired records and least-recently-used records.
2. Automatically retrying transient failures with exponential backoff and randomized jitter to prevent the "thundering herd" problem on downstream services.

**Core Invariants Enforced:**
1. **Signature & Introspection Preservation:** Uses `functools.wraps` so `__name__`, `__doc__`, and function signatures are preserved for debugging and documentation.
2. **Deterministic Argument Normalization:** Calling `fn(1, b=2)` and `fn(1, b=2)` with rearranged keyword order yields identical cache hits.
3. **Transient-Only Retries:** Retries strictly filter on allowed exception classes (e.g. `ConnectionError`), re-raising non-retryable exceptions immediately.

---

## 2. How to Think About This Problem (First-Principles Mental Model)

### The Trigger
Reach for this pattern when the interviewer asks:
> *"Implement a function caching decorator with bounded size and TTL expiration without using `functools.lru_cache`, and write an exponential backoff retry decorator with jitter and custom retryable exceptions."*

### Why Naive Approaches Fail
- **Using a standard dict for LRU:** Standard Python dicts preserve insertion order, but updating a key does not move it to the end without explicit `move_to_end()`. `collections.OrderedDict` is required.
- **Non-deterministic kwargs cache keys:** If kwargs are hashed directly without sorting (`tuple(kwargs.items())`), Python dictionary insertion ordering could cause `fn(a=1, b=2)` and `fn(b=2, a=1)` to generate different cache keys and compute twice.
- **Forgetting `functools.wraps`:** Strips docstrings and renames the wrapped function to `"wrapper"`, breaking monitoring and logging decorators.
- **Retry without Jitter:** Retrying simultaneously across hundreds of worker nodes on exact exponential multiples ($0.1s, 0.2s, 0.4s$) creates synchronized shockwaves (thundering herds) that repeatedly knock recovering servers back offline.

### The Architecture
```
lru_ttl_cache (OrderedDict)
  ├── Lookup key: (args, tuple(sorted(kwargs.items())))
  ├── If Hit:
  │     ├── Expired? (now >= expires_at) ──> del cache[key] ──> Compute fresh
  │     └── Valid? ──> cache.move_to_end(key) ──> return cached value
  └── If Miss:
        ├── Compute function result
        ├── len >= maxsize? ──> cache.popitem(last=False) [Evict LRU]
        └── cache[key] = (result, now + ttl)

retry
  └── Loop attempt in 0..max_retries:
        ├── try: return fn(*args, **kwargs)
        └── except retryable_exceptions:
              ├── if attempt == max_retries: raise
              └── sleep(base_delay * (factor ** attempt) * jitter)
```

---

## 3. How to Read the Code (`solution.py` Walkthrough)

### `CacheInfo` and `lru_ttl_cache` (Lines 21–76)
- **Line 21 (`CacheInfo`):** Mimics `functools._CacheInfo` with a typed named tuple returning `(hits, misses, maxsize, currsize)`.
- **Line 34 (`cache: OrderedDict`):** Stores `key -> (result, expires_at)`.
- **Line 42 (Deterministic Cache Key):**
  `key = (args, tuple(sorted(kwargs.items())))`. Sorting `kwargs.items()` guarantees that argument order invariance is maintained across invocations.
- **Lines 45–52 (Hit & Expiration Check):**
  Uses `time.monotonic()` (immune to system wall-clock jumps). If entry is expired, it is deleted immediately. If valid, `cache.move_to_end(key)` marks it as most recently used.
- **Lines 57–59 (Eviction):**
  `cache.popitem(last=False)` pops the first (oldest / least recently used) item from the `OrderedDict`.
- **Lines 63–73 (Attached Introspection Methods):**
  Attaches `.cache_clear()` and `.cache_info()` functions to the wrapper function object.

### `retry` Decorator (Lines 78–103)
- **Lines 89–100:** Loops from `0` to `max_retries`. If the error is an instance of `retryable_exceptions`, it checks if the retry budget is exhausted (`attempt == max_retries`); if so, it re-raises the original exception.
- **Lines 95–98 (Exponential Backoff with Full Jitter):**
  `delay = base_delay * (backoff_factor ** attempt)`. Jitter randomly scales the sleep between `50%` and `100%` of calculated delay using `random.uniform(0.5 * delay, delay)`.

---

## 4. How to Write It in a Live Interview (Step-by-Step Execution Order)

### Step 1: Skeleton & Core Data Structures (Mins 0–10)
Stub the decorator envelopes with `@functools.wraps`:
```python
import functools, time, random
from collections import OrderedDict

def lru_ttl_cache(maxsize=128, ttl_seconds=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

def retry(max_retries=3, base_delay=0.05, backoff_factor=2.0, retryable_exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### Step 2: The Happy Path Core Logic (Mins 10–22)
Implement the core mechanics:
- In `lru_ttl_cache`: create `cache = OrderedDict()`, build `key = (args, tuple(sorted(kwargs.items())))`, check existence, call `cache.move_to_end(key)`, and return.
- In `retry`: write `for attempt in range(max_retries + 1): try: return func(...) except retryable_exceptions: ...` with exponential sleep.

### Step 3: Edge Cases, Concurrency & Safety Invariants (Mins 22–35)
Now add the production-grade refinements:
- In `lru_ttl_cache`: add monotonic TTL expiration check (`time.monotonic() > expires_at`). If expired, `del cache[key]`.
- Add LRU capacity eviction: `if len(cache) >= maxsize: cache.popitem(last=False)`.
- Attach `.cache_clear()` and `.cache_info()` onto `wrapper`.
- In `retry`: add randomized jitter `random.uniform(0.5 * delay, delay)`. Ensure unhandled exception types immediately fall through without retry.

### Step 4: Verification Driver (Mins 35–45)
Write `assert` tests in `if __name__ == "__main__":`:
1. Metadata verification: `wrapper.__name__ == func.__name__` and docstring match.
2. LRU eviction: fill to `maxsize=2`, invoke 3rd distinct argument, verify first argument is evicted and recorded as miss.
3. TTL expiry: set `ttl_seconds=0.05`, sleep `0.06s`, assert cache miss.
4. Retry success: simulate flaky function failing twice before succeeding.
5. Retry failure: simulate non-retryable exception raising immediately.

---

## 5. Must-Memorize Syntax & Idioms (The Cheat Sheet)

```python
# 1. Signature-preserving parameterized decorator envelope
def my_decorator(param: int):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 2. Deterministic argument hashing
cache_key = (args, tuple(sorted(kwargs.items())))

# 3. OrderedDict LRU operations
cache.move_to_end(key)          # Mark key as Most Recently Used
oldest = cache.popitem(last=False)  # Evict Least Recently Used

# 4. Monotonic time for intervals/deadlines
now = time.monotonic()  # Always monotonic, never time.time()
```

---

## 6. Common Traps & Follow-Up Curveballs

### 3 Mistakes That Fail the Interview
1. **Using `time.time()` instead of `time.monotonic()`:** `time.time()` tracks wall-clock time and is subject to NTP clock sync steps or daylight saving adjustments, causing caches to prematurely expire or live forever.
2. **Unhashable Arguments in Cache Key:** If a caller passes `fn([1, 2, 3])`, `tuple(args)` will contain a mutable list and crash with `TypeError: unhashable type: 'list'`. Candidates should mention or implement recursive conversion of lists/dicts to tuples/frozensets.
3. **Catching `BaseException` in Retry:** Catching `BaseException` catches `KeyboardInterrupt` and `SystemExit`, preventing the user or orchestrator from terminating the script via Ctrl+C. Catch `Exception` or concrete subclasses.

### 2 Bar-Raiser Follow-Ups
1. **"How do you make this cache thread-safe?"**
   *Answer:* Wrap cache lookups and mutations in `threading.Lock()`, or use an `RLock` if the cached function might call itself recursively.
2. **"How would you handle memoizing a function that returns a generator or stream?"**
   *Answer:* Caching a generator directly caches an exhausted iterator. You must either materialize the generator into a tuple `tuple(func(*args, **kwargs))` before caching, or implement a teeing iterator.
