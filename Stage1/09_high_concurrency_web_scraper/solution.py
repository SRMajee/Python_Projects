"""
Problem 09: High-Concurrency Asynchronous Web Scraper
Phase: Modern AsyncIO (Target: 100-140 LOC)

Staff Engineer Design Notes:
- Concurrency Bounding: Guarantees active network connections strictly <= limit via `asyncio.Semaphore`.
- Python 3.11+ Primitives: Employs `asyncio.TaskGroup` for structured concurrency and `asyncio.timeout`
  for strict per-request deadline enforcement.
- Fault Tolerance: In-task exception isolation allows partial failures (HTTP errors, timeouts, flaky retries)
  to be recorded without causing catastrophic TaskGroup cancellation.
- Real-time Concurrency Invariant: Concurrency gauge dynamically verifies that the semaphore boundary
  is never breached under load.
"""

import asyncio
from dataclasses import dataclass
import random
import time
from typing import Any


@dataclass(frozen=True)
class FetchResult:
    url: str
    status: int
    data: dict[str, Any] | None
    error: str | None
    latency_seconds: float


@dataclass(frozen=True)
class ScrapeSummary:
    total_requests: int
    successful_count: int
    failed_count: int
    peak_concurrency: int
    results: list[FetchResult]


class SimulatedHttpClient:
    """Simulates realistic asynchronous HTTP network calls with varied latencies and errors."""

    async def get(self, url: str) -> tuple[int, dict[str, Any]]:
        # Simulate network latency
        if "slow" in url:
            await asyncio.sleep(0.3)
            return 200, {"url": url, "payload": "slow_data"}
        if "flaky" in url:
            # 50% chance of transient server error
            await asyncio.sleep(0.04)
            if random.random() < 0.5:
                raise ConnectionResetError("Remote server closed stream")
            return 200, {"url": url, "payload": "flaky_data"}
        if "not_found" in url:
            await asyncio.sleep(0.02)
            return 404, {"error": "Not Found"}

        # Normal fast response
        await asyncio.sleep(0.03)
        return 200, {"url": url, "payload": "ok"}


class HighConcurrencyScraper:
    """Bounded asynchronous scraper managing concurrency limits, timeouts, and retries."""

    def __init__(self, max_concurrency: int = 5, request_timeout: float = 0.15) -> None:
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.request_timeout = request_timeout
        self.client = SimulatedHttpClient()
        self._active_connections = 0
        self._peak_concurrency = 0
        self._lock = asyncio.Lock()

    async def _fetch_with_retry(self, url: str, max_retries: int = 2) -> FetchResult:
        start_time = time.monotonic()

        async with self.semaphore:
            # Track and assert active concurrency invariant
            async with self._lock:
                self._active_connections += 1
                if self._active_connections > self._peak_concurrency:
                    self._peak_concurrency = self._active_connections

            try:
                last_err: Exception | None = None
                for attempt in range(max_retries + 1):
                    try:
                        # Enforce per-request timeout using Python 3.11+ asyncio.timeout
                        async with asyncio.timeout(self.request_timeout):
                            status, data = await self.client.get(url)
                            elapsed = time.monotonic() - start_time
                            return FetchResult(
                                url=url,
                                status=status,
                                data=data if status < 400 else None,
                                error=None if status < 400 else f"HTTP {status}",
                                latency_seconds=elapsed,
                            )
                    except (TimeoutError, asyncio.TimeoutError):
                        last_err = TimeoutError(f"Request exceeded {self.request_timeout}s timeout")
                        break  # Do not retry on strict timeout expiry
                    except Exception as exc:
                        last_err = exc
                        if attempt < max_retries:
                            await asyncio.sleep(0.02 * (2**attempt))

                elapsed = time.monotonic() - start_time
                return FetchResult(
                    url=url,
                    status=0,
                    data=None,
                    error=str(last_err),
                    latency_seconds=elapsed,
                )
            finally:
                async with self._lock:
                    self._active_connections -= 1

    async def scrape_all(self, urls: list[str]) -> ScrapeSummary:
        """Fetch all URLs concurrently using modern structured concurrency (TaskGroup)."""
        results: list[FetchResult] = []

        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(self._fetch_with_retry(u)) for u in urls]

        for t in tasks:
            results.append(t.result())

        succeeded = sum(1 for r in results if r.status == 200 and r.error is None)
        failed = len(results) - succeeded

        return ScrapeSummary(
            total_requests=len(urls),
            successful_count=succeeded,
            failed_count=failed,
            peak_concurrency=self._peak_concurrency,
            results=results,
        )


# ---------------------------------------------------------------------------
# Verification & Test Scenarios
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    async def main():
        concurrency_limit = 4
        timeout = 0.1
        scraper = HighConcurrencyScraper(
            max_concurrency=concurrency_limit,
            request_timeout=timeout,
        )

        test_urls = (
            [f"https://api.stripe.com/v1/customers/{i}" for i in range(10)]
            + ["https://api.stripe.com/v1/slow/1", "https://api.stripe.com/v1/slow/2"]
            + [f"https://api.stripe.com/v1/flaky/{i}" for i in range(4)]
            + ["https://api.stripe.com/v1/not_found/404"]
        )

        summary = await scraper.scrape_all(test_urls)

        # 1. Strict concurrency invariant verification
        assert summary.peak_concurrency <= concurrency_limit, (
            f"Peak concurrency {summary.peak_concurrency} exceeded limit {concurrency_limit}"
        )

        # 2. Total request accounting
        assert summary.total_requests == len(test_urls)

        # 3. Timeout handling on slow endpoints
        slow_results = [r for r in summary.results if "slow" in r.url]
        assert len(slow_results) == 2
        for r in slow_results:
            assert r.status == 0
            assert "timeout" in (r.error or "").lower()

        # 4. 404 client error handling
        not_found = [r for r in summary.results if "not_found" in r.url][0]
        assert not_found.status == 404
        assert not_found.error == "HTTP 404"

        # 5. Fast endpoints succeeded
        fast_results = [r for r in summary.results if "/customers/" in r.url]
        assert all(r.status == 200 and r.error is None for r in fast_results)

        print("09_high_concurrency_web_scraper: All assertions passed successfully.")

    asyncio.run(main())
