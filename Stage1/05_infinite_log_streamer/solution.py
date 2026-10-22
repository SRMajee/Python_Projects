"""
Problem 05: Infinite Log Streamer & Aggregation Pipeline
Phase: Iterators & Contexts (Target: 50-70 LOC)

Staff Engineer Design Notes:
- Strict O(1) memory footprint: Lazy streaming via generator expressions and `yield from`.
- Custom Iterator Protocol implementation (`__iter__`, `__next__`) for stateful metric aggregation.
- Composable Unix-pipe style stages: Multi-source multiplexing -> Parsing -> Filtering -> Windowed Aggregation.
- Zero buffering of underlying datasets, resilient to infinite stream inputs.
"""

from collections.abc import Iterable, Iterator
import re
from typing import NamedTuple, Self

LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\S+)\s+(?P<level>DEBUG|INFO|WARN|ERROR)\s+(?P<service>\S+)\s+latency_ms=(?P<latency>\d+(?:\.\d+)?)"
)


class LogRecord(NamedTuple):
    timestamp: str
    level: str
    service: str
    latency_ms: float


class WindowMetrics(NamedTuple):
    count: int
    error_count: int
    avg_latency_ms: float
    max_latency_ms: float


def stream_multi_source(*sources: Iterable[str]) -> Iterator[str]:
    """Multiplex multiple log sources lazily using yield from."""
    for source in sources:
        yield from source


def parse_logs(lines: Iterable[str]) -> Iterator[LogRecord]:
    """Parse raw log lines into typed LogRecord tuples lazily."""
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = LOG_PATTERN.match(line)
        if match:
            yield LogRecord(
                timestamp=match.group("timestamp"),
                level=match.group("level"),
                service=match.group("service"),
                latency_ms=float(match.group("latency")),
            )


def filter_logs(
    stream: Iterable[LogRecord],
    *,
    service: str | None = None,
    min_level: str | None = None,
) -> Iterator[LogRecord]:
    """Filter records lazily based on service or level without loading items."""
    levels = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}
    min_rank = levels.get(min_level, 0) if min_level else 0

    for rec in stream:
        if service and rec.service != service:
            continue
        if min_level and levels.get(rec.level, 0) < min_rank:
            continue
        yield rec


class WindowAggregator:
    """Stateful iterator consuming streams in strict O(1) space across fixed windows."""

    def __init__(self, source: Iterable[LogRecord], window_size: int = 100) -> None:
        self._source_iter = iter(source)
        self.window_size = window_size

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> WindowMetrics:
        count = 0
        total_latency = 0.0
        max_latency = 0.0
        error_count = 0

        while count < self.window_size:
            try:
                rec = next(self._source_iter)
            except StopIteration:
                if count == 0:
                    raise
                break  # Yield final partial window

            count += 1
            total_latency += rec.latency_ms
            if rec.latency_ms > max_latency:
                max_latency = rec.latency_ms
            if rec.level == "ERROR":
                error_count += 1

        return WindowMetrics(
            count=count,
            error_count=error_count,
            avg_latency_ms=(total_latency / count) if count > 0 else 0.0,
            max_latency_ms=max_latency,
        )


# ---------------------------------------------------------------------------
# Verification & Test Scenarios
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    def infinite_dummy_source(limit: int, service: str):
        """Simulate a bounded generator producing streaming log lines."""
        for i in range(limit):
            level = "ERROR" if i % 4 == 0 else "INFO"
            latency = 10.0 + (i % 50)
            yield f"2026-10-22T10:{i:02d}:00 {level} {service} latency_ms={latency:.1f}\n"

    # 1. Lazy composition of infinite log pipeline
    src_auth = infinite_dummy_source(250, "auth-svc")
    src_billing = infinite_dummy_source(250, "billing-svc")

    raw_stream = stream_multi_source(src_auth, src_billing)
    parsed = parse_logs(raw_stream)
    filtered = filter_logs(parsed, service="auth-svc", min_level="INFO")
    aggregator = WindowAggregator(filtered, window_size=100)

    # 2. Window 1 validation
    w1 = next(aggregator)
    assert w1.count == 100
    assert w1.error_count == 25  # Every 4th entry is ERROR
    assert 10.0 <= w1.avg_latency_ms <= 60.0
    assert w1.max_latency_ms == 59.0

    # 3. Window 2 validation
    w2 = next(aggregator)
    assert w2.count == 100
    assert w2.error_count == 25

    # 4. Partial final window (50 remaining items for auth-svc)
    w3 = next(aggregator)
    assert w3.count == 50

    # 5. Stream exhaustion correctly raises StopIteration
    try:
        next(aggregator)
        assert False, "Should raise StopIteration on exhausted stream"
    except StopIteration:
        pass

    print("05_infinite_log_streamer: All assertions passed successfully.")
