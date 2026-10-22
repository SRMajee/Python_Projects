# Problem 09: High-Concurrency Asynchronous Web Scraper

## 1. What This Solution Does (The 30-Second Pitch)
This module implements a production-grade, highly concurrent asynchronous scraper/fetcher using modern Python 3.11+ `asyncio.TaskGroup`, `asyncio.Semaphore`, and `asyncio.timeout`. In high-volume integrations at Stripe (polling bank gateways) or Rippling (syncing payroll data with insurance carriers), systems must fetch thousands of heterogeneous endpoints concurrently while strictly respecting partner rate limits.

Firing unconstrained asynchronous tasks crashes servers with connection exhaustion errors (e.g. `Too many open files` / socket exhaustion). This engine bounds active requests via a semaphore, enforces strict per-request deadlines, retries transient failures with backoff, and aggregates partial results without letting individual endpoint failures crash the scraping run.

**Core Invariants Enforced:**
1. **Strict Concurrency Bound:** Active in-flight network requests never exceed `max_concurrency` at any instant.
2. **Deterministic Request Deadlines:** Python 3.11+ `asyncio.timeout` cancels hanging requests cleanly without blocking the event loop.
3. **Structured Concurrency with Fault Isolation:** Individual task failures are caught inside the worker and encapsulated in a `FetchResult` rather than triggering catastrophic cancellation of sibling tasks in `TaskGroup`.

---

## 2. How to Think About This Problem (First-Principles Mental Model)

### The Trigger
Reach for this pattern when the interviewer says:
> *"Write an asynchronous web scraper or API fetcher in modern Python that queries hundreds of URLs concurrently. Enforce a strict maximum concurrency limit, handle timeouts and transient failures gracefully, and aggregate results."*

### Why Naive Approaches Fail
- **Unbounded `asyncio.gather(*tasks)`:** Launching 5,000 coroutines simultaneously opens 5,000 sockets at once, overwhelming the local OS network stack and triggering immediate 429 Too Many Requests responses from upstream hosts.
- **Unprotected `TaskGroup` cancellation:** In Python 3.11+ `TaskGroup`, if *any* task raises an uncaught exception, the `TaskGroup` immediately cancels all remaining sibling tasks and re-raises an `ExceptionGroup`. In web scraping, partial failures (e.g., 404 Not Found or a single timeout) are normal; failing the entire batch is unacceptable.
- **Using `asyncio.wait_for()` in Python 3.11+:** While functional, `asyncio.wait_for` has well-known cancellation race conditions when tasks mask cancellation. Modern code uses the asynchronous context manager `async with asyncio.timeout(...)`.

### The Architecture
```
URLs: [url_1, url_2, ..., url_N]
           │
           ▼
async with asyncio.TaskGroup() as tg:
    tg.create_task(_fetch_with_retry(url))
           │
           ▼
    [ asyncio.Semaphore(max_concurrency) ]  <── Hard concurrency ceiling
           │
           ├── Acquire permit
           ├── Try up to max_retries:
           │     async with asyncio.timeout(request_timeout):
           │         status, data = await client.get(url)
           │         return FetchResult(status=200, ...)
           │     except TimeoutError:
           │         break (no retry on timeout)
           │     except TransientError:
           │         await asyncio.sleep(backoff)
           ├── Release permit
           └── return FetchResult(status=0, error=...)
```

---

## 3. How to Read the Code (`solution.py` Walkthrough)

### Result DTOs (Lines 22–38)
- **`FetchResult`:** Strongly typed immutable record storing `url`, HTTP `status`, parsed `data`, `error` description, and `latency_seconds`.
- **`ScrapeSummary`:** Aggregate report including total counts, success/failure metrics, results list, and the recorded `peak_concurrency`.

### `HighConcurrencyScraper` (Lines 63–73)
- Initialized with `asyncio.Semaphore(max_concurrency)` and `request_timeout`.
- Tracks `self._active_connections` and `self._peak_concurrency` protected by an `asyncio.Lock()` to verify the concurrency boundary during runtime execution.

### `_fetch_with_retry` (Lines 74–118)
- **Line 77 (`async with self.semaphore`):** Blocks execution until a concurrency permit is available.
- **Lines 89–98 (`async with asyncio.timeout(self.request_timeout)`):**
  Python 3.11+ context manager. If the network call exceeds `self.request_timeout`, it cancels `client.get()` cleanly and raises `TimeoutError`.
- **Lines 99–105 (Failure Classification):**
  - Timeout errors break immediately (no point retrying if endpoint is unresponsive).
  - Transient network errors back off with exponential sleep (`await asyncio.sleep(0.02 * (2**attempt))`).
- **Lines 108–117:**
  Catches final errors, computes latency, and returns a typed `FetchResult`. Because exceptions are caught internally, the enclosing `TaskGroup` remains healthy.

### `scrape_all` (Lines 119–139)
- **Lines 123–125 (`async with asyncio.TaskGroup() as tg`):**
  Spawns tasks via `tg.create_task()`. Automatically joins all tasks when the context block exits.
- Extracts results and compiles the `ScrapeSummary`.

---

## 4. How to Write It in a Live Interview (Step-by-Step Execution Order)

### Step 1: Skeleton & Core Data Structures (Mins 0–10)
Define `FetchResult` and the scraper class skeleton:
```python
import asyncio, time
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class FetchResult:
    url: str; status: int; data: Any; error: str | None; latency_seconds: float

class HighConcurrencyScraper:
    def __init__(self, max_concurrency: int = 5, request_timeout: float = 0.2):
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.request_timeout = request_timeout
```

### Step 2: The Happy Path Core Logic (Mins 10–22)
Implement semaphore-bounded fetching and `scrape_all`:
```python
async def _fetch(self, url: str) -> FetchResult:
    start = time.monotonic()
    async with self.semaphore:
        async with asyncio.timeout(self.request_timeout):
            status, data = await self.client.get(url)
            return FetchResult(url, status, data, None, time.monotonic() - start)

async def scrape_all(self, urls: list[str]):
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(self._fetch(u)) for u in urls]
    return [t.result() for t in tasks]
```

### Step 3: Edge Cases, Concurrency & Safety Invariants (Mins 22–35)
Layer on the Staff-level fault tolerance:
- Catch exceptions inside `_fetch` so one failed endpoint does not cancel the entire `TaskGroup`.
- Add retry loop with exponential backoff on transient errors (`ConnectionError`).
- Differentiate between `TimeoutError` (do not retry) and transient server errors.
- Add an active connection gauge to prove peak concurrency never exceeds `max_concurrency`.

### Step 4: Verification Driver (Mins 35–45)
Write `main()` inside `if __name__ == "__main__":` testing:
1. Concurrency invariant: `summary.peak_concurrency <= max_concurrency`.
2. Total accounting: `summary.total_requests == len(test_urls)`.
3. Verify slow URLs time out without hanging the test.
4. Verify flaky URLs succeed on retry.
5. Verify 404 URLs are captured as client errors with HTTP 404 status.

---

## 5. Must-Memorize Syntax & Idioms (The Cheat Sheet)

```python
# 1. Bounding async concurrency with a Semaphore
sem = asyncio.Semaphore(10)
async with sem:
    await make_network_request()

# 2. Modern Python 3.11+ Structured Concurrency
async with asyncio.TaskGroup() as tg:
    task1 = tg.create_task(coro1())
    task2 = tg.create_task(coro2())
# All tasks are guaranteed to be awaited and cleaned up when leaving block

# 3. Modern Python 3.11+ Per-Operation Timeout
async with asyncio.timeout(seconds):
    await long_running_io()  # Automatically cancelled if time expires

# 4. Asynchronous sleep for non-blocking backoff
await asyncio.sleep(delay)  # Yields execution to event loop
```

---

## 6. Common Traps & Follow-Up Curveballs

### 3 Mistakes That Fail the Interview
1. **Calling `time.sleep()` inside an `async def`:** Calling synchronous `time.sleep()` blocks the entire event loop thread, stopping all other concurrent tasks from progressing. Always use `await asyncio.sleep()`.
2. **Allowing unhandled exceptions inside `TaskGroup` tasks:** If a task raises an uncaught exception, `TaskGroup` immediately cancels every other pending task in the group. In scraping tasks, catch exceptions inside the task coroutine.
3. **Acquiring the Semaphore outside the retry loop:** If you acquire the semaphore outside the retry loop, a sleeping task holding the semaphore consumes a concurrency slot while waiting to retry, starving other active tasks.

### 2 Bar-Raiser Follow-Ups
1. **"How would you implement domain-specific rate limiting (e.g., max 2 req/s to `google.com` but max 10 req/s to `stripe.com`)?"**
   *Answer:* Maintain a dictionary of semaphores or token buckets keyed by domain (`domain_limiters[domain] = asyncio.Semaphore(limit)`). Tasks extract the host from the URL and acquire both the global concurrency semaphore and the domain-specific limiter.
2. **"How do you process millions of URLs without loading all URLs into memory at once?"**
   *Answer:* Instead of creating a task for every URL in advance, use an `asyncio.Queue(maxsize=1000)`. Run a fixed worker pool of $N$ consumer coroutines pulling URLs from the queue, while a streaming producer reads URLs lazily from disk.
