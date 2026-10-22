# Problem 05: Infinite Log Streamer & Aggregator

## 1. What This Solution Does (The 30-Second Pitch)
This module builds an end-to-end log processing and metrics aggregation engine that runs in strict $O(1)$ auxiliary memory regardless of whether it processes 10 lines or 10 billion lines. In massive high-throughput platforms like Stripe's payment routing or Rippling's audit trail, logs arrive continuously across multiple ingestion nodes.

Loading logs into memory using `readlines()` or storing parsed records in a list causes Out-Of-Memory (OOM) crashes. This pipeline demonstrates how to compose lazy generators (`yield`, `yield from`) and implement the formal Python Iterator Protocol (`__iter__`, `__next__`) to stream, parse, filter, and compute windowed aggregations without ever materializing datasets in RAM.

**Core Invariants Enforced:**
1. **Strict $O(1)$ Space Complexity:** Memory consumption remains constant throughout the execution life cycle.
2. **Lazy Push-Pull Evaluation:** Computation occurs strictly on-demand as downstream consumers invoke `next()`.
3. **Graceful Partial Windowing:** Correctly aggregates incomplete batches when an input stream terminates without dropping trailing records.

---

## 2. How to Think About This Problem (First-Principles Mental Model)

### The Trigger
Reach for this pattern when the interviewer says:
> *"We need to process gigabytes or potentially infinite streams of server logs across multiple sources, parse them, filter out noise, and emit rolling metric snapshots. Your solution must run with bounded, constant $O(1)$ memory."*

### Why Naive Approaches Fail
- **`file.readlines()` or List Comprehensions:** `[parse(line) for line in file]` eagerly allocates memory for every line, instantly crashing worker pods on multi-gigabyte logs.
- **Materializing Filter Buffers:** Writing `records = list(filter_logs(...))` defeats the entire purpose of generator pipelines.
- **Ignoring custom iterator state:** While generator functions handle pure transformations well, stateful multi-step aggregations that maintain window state and emit window summaries are best encapsulated using the formal Iterator Protocol (`__iter__`, `__next__`).

### The Architecture
```
Source 1 ──┐
Source 2 ──┼──> stream_multi_source()  [yield from source]
Source 3 ──┘           │
                       ▼
                 parse_logs()          [yield LogRecord]
                       │
                       ▼
                 filter_logs()         [yield matching LogRecord]
                       │
                       ▼
             WindowAggregator          [implements __iter__, __next__]
                       │
                       ▼
                 WindowMetrics         [Emitted every window_size items]
```

---

## 3. How to Read the Code (`solution.py` Walkthrough)

### Data Models & Regex Compilation (Lines 16–33)
- **Line 16 (`LOG_PATTERN`):** Uses named capture groups (`(?P<level>...)`) compiled once at the module level with `re.compile()` for performance.
- **Lines 21–33 (`LogRecord`, `WindowMetrics`):** Lightweight `NamedTuple` definitions. NamedTuples incur zero additional memory overhead compared to plain tuples while providing field access syntax.

### Generator Pipeline Stages (Lines 35–73)
- **Lines 35–38 (`stream_multi_source`):** Uses `yield from source` to transparently delegate iteration to each source iterable in sequence without nested loops or buffering.
- **Lines 41–55 (`parse_logs`):** Lazy generator filtering out comments and blank lines, parsing matched fields, and yielding typed `LogRecord` instances one at a time.
- **Lines 57–73 (`filter_logs`):** Applies predicate filtering (service name matching, log level severity ranking) on the incoming stream on-the-fly.

### `WindowAggregator` (Lines 75–112)
- **Lines 78–83 (`__init__` & `__iter__`):** Converts the source iterable to an iterator via `iter(source)` and returns `self` from `__iter__`.
- **Lines 85–111 (`__next__`):**
  Loops until `count == self.window_size` or the source raises `StopIteration`.
  - Notice lines 94–97: If `StopIteration` occurs and `count > 0`, it breaks the loop to yield the remaining partial window.
  - If `count == 0` on entry, it propagates `StopIteration` to signal full stream exhaustion.
  - Computes running metrics (`avg_latency_ms`, `max_latency_ms`, `error_count`) in $O(1)$ space without storing past records.

---

## 4. How to Write It in a Live Interview (Step-by-Step Execution Order)

### Step 1: Skeleton & Core Data Structures (Mins 0–10)
Define the tuples and stub the generator pipeline:
```python
from typing import NamedTuple, Iterator, Iterable, Self
import re

class LogRecord(NamedTuple):
    timestamp: str; level: str; service: str; latency_ms: float

class WindowMetrics(NamedTuple):
    count: int; error_count: int; avg_latency_ms: float; max_latency_ms: float

def stream_multi_source(*sources: Iterable[str]) -> Iterator[str]:
    for src in sources: yield from src
```

### Step 2: The Happy Path Core Logic (Mins 10–22)
Implement the parsing and filtering generators:
- Write `parse_logs` extracting fields using regex and `yield LogRecord(...)`.
- Write `filter_logs` checking criteria and yielding downstream.

### Step 3: Edge Cases, Concurrency & Safety Invariants (Mins 22–35)
Implement `WindowAggregator` enforcing the Iterator protocol:
- Implement `__iter__(self) -> Self: return self`.
- Implement `__next__`: accumulate running totals (`total_latency += rec.latency_ms`) without appending records to a list.
- Handle stream exhaustion carefully:
  - If stream ends on an exact window boundary (`count == 0`), raise `StopIteration`.
  - If stream ends mid-window (`count > 0`), break and return the partial `WindowMetrics`.
  - Guard against division by zero: `avg = (total / count) if count > 0 else 0.0`.

### Step 4: Verification Driver (Mins 35–45)
Write streaming assertions in `if __name__ == "__main__":`:
1. Create a dummy generator simulating an infinite source.
2. Pipe multi-source -> parse -> filter -> window aggregator.
3. Validate metrics on Window 1, Window 2, and the trailing partial window.
4. Verify that calling `next()` after stream exhaustion raises `StopIteration`.

---

## 5. Must-Memorize Syntax & Idioms (The Cheat Sheet)

```python
# 1. Delegating iteration to sub-generators cleanly
def multiplex(*iterables):
    for it in iterables:
        yield from it

# 2. Formal Python Iterator Protocol implementation
class CustomIterator:
    def __iter__(self) -> Self:
        return self
    def __next__(self) -> Result:
        val = next(self.source) # raises StopIteration automatically
        return transform(val)

# 3. Converting any iterable to an iterator safely
self._source_iter = iter(source)

# 4. Compiling regex with named capture groups
PATTERN = re.compile(r"(?P<level>INFO|ERROR)\s+latency=(?P<lat>\d+)")
```

---

## 6. Common Traps & Follow-Up Curveballs

### 3 Mistakes That Fail the Interview
1. **Calling `len(stream)` or `list(stream)`:** Calling `len()` or `list()` on a generator consumes the entire stream into memory, completely destroying the $O(1)$ memory invariant and hanging forever on infinite streams.
2. **Dropping Partial Windows:** If a log file contains 250 records with a window size of 100, a naive loop will drop the last 50 records when `next(self._source_iter)` raises `StopIteration`. You must yield partial batches if `count > 0`.
3. **Forgetting `return self` in `__iter__`:** An iterator that implements `__next__` but forgets `__iter__` fails Python's iterable protocol and cannot be used in `for item in aggregator:`.

### 2 Bar-Raiser Follow-Ups
1. **"How would you handle multiplexing streams ordered by timestamp?"**
   *Answer:* Instead of sequential `yield from`, use `heapq.merge(*sources, key=extract_timestamp)`. It maintains a min-heap of size $K$ (number of sources), streaming globally sorted items in $O(K)$ space and $O(\log K)$ time per item.
2. **"How do you process logs in real-time with backpressure across threads?"**
   *Answer:* Connect the generator pipeline to a bounded `queue.Queue(maxsize=N)`. The producer generator puts parsed records into the queue, blocking when downstream consumer threads are slow.
