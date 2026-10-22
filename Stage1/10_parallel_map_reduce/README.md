# Problem 10: Parallel Map-Reduce Framework

## 1. What This Solution Does (The 30-Second Pitch)
This module builds a multi-core parallel Map-Reduce computation engine using Python's `multiprocessing.Process` and inter-process communication (IPC) queues (`multiprocessing.Queue`). Python threads cannot achieve true CPU parallelism because CPython's Global Interpreter Lock (GIL) serializes bytecode execution onto a single CPU core.

For compute-intensive operations—such as cryptographic verification, large-scale financial reconciliations at Stripe, or org-wide tax calculations at Rippling—bypassing the GIL via multi-process parallelism is mandatory to scale linearly across all CPU cores. This engine implements balanced chunking, worker process pool lifecycle management, IPC error marshaling, and deterministic reduce aggregation.

**Core Invariants Enforced:**
1. **True Multicore Parallelism (GIL Bypass):** Work runs across discrete OS processes, enabling total CPU utilization to scale past 100% on multicore systems.
2. **Deterministic Output Ordering:** Intermediate mapped chunks are indexed by `chunk_id` and sorted before the reduction step, guaranteeing identical results regardless of worker scheduling order.
3. **Robust IPC & Exception Marshaling:** Worker exceptions are serialized across process boundaries and re-raised in the parent process as `WorkerProcessError`, ensuring errors never vanish silently into dead worker processes.
4. **Clean Process Lifecycle:** Workers and queues are systematically drained, joined, and closed, completely preventing zombie processes and IPC buffer deadlocks.

---

## 2. How to Think About This Problem (First-Principles Mental Model)

### The Trigger
Reach for this pattern when the interviewer says:
> *"We have a heavy, CPU-bound calculation that is too slow in a single thread. Implement a parallel Map-Reduce framework using `multiprocessing.Process` and IPC queues to distribute the work across multiple CPU cores, marshal errors back to the caller, and prevent deadlocks."*

### Why Naive Approaches Fail
- **Using `threading.Thread` for CPU tasks:** Threads in Python share the GIL. Running a CPU-heavy task across 4 threads is often *slower* than running it sequentially due to thread context-switching overhead.
- **The Queue-Join Deadlock Trap:** In Python's `multiprocessing.Queue`, calling `process.join()` *before* draining the queue causes a permanent deadlock if the queue's internal background feeding thread has buffered items waiting to flush to the underlying pipe. You must **drain the result queue first**, then join the processes.
- **Windows `spawn` Function Pickling Failure:** On Windows and macOS (Python 3.8+ default), child processes start via `spawn`. Passing inner functions or lambdas declared inside `__main__` or other functions fails with `AttributeError: Can't get attribute '...' on <module '__mp_main__'>`. All worker entrypoints must be declared at the module level.
- **Lost Exceptions in Child Processes:** If a child process crashes with an unhandled exception, the parent process hangs forever on `result_queue.get()`. Workers must catch exceptions and put structured error payloads into the result queue.

### The Architecture
```
Input Dataset: [0, 1, ..., N]
           │
           ▼
Chunker: Partition into K chunks: [(0, chunk_0), (1, chunk_1), ...]
           │
           ▼
Enqueue onto task_queue + Enqueue N poison pills (_POISON_PILL = None)
           │
           ├───────────────────────────────┐
           ▼                               ▼
    Worker Process 0                Worker Process 1
  _map_worker_entrypoint          _map_worker_entrypoint
           │                               │
           ▼                               ▼
    mapped_0 = map_fn(c0)           mapped_1 = map_fn(c1)
           │                               │
           └───────────────┬───────────────┘
                           ▼
                  result_queue (IPC)
                           │
                           ▼
Parent collects K results -> Sorts by chunk_id -> reduce_fn(ordered_results)
                           │
                    p.join() on all workers
```

---

## 3. How to Read the Code (`solution.py` Walkthrough)

### Worker Entrypoint & Exception Marshaling (Lines 33–55)
- **Line 26 (`_POISON_PILL = None`):** Sentinels to signal worker exit.
- **`_map_worker_entrypoint` (Lines 33–55):**
  Module-level function (required for `pickle` on Windows/macOS `spawn`).
  Loops on `task_queue.get()`. If item is `_POISON_PILL`, breaks and exits.
  **Lines 50–52:** Catches `Exception as exc`, serializes `err_info = (type(exc).__name__, str(exc))`, and puts `(chunk_id, None, err_info)` into the `result_queue`. The parent process will never be left hanging on missing results.

### CPU Task Workload (Lines 57–69)
- **`cpu_bound_hasher`:** Computes repetitive SHA-256 cryptographic hashes in a tight loop to simulate intense CPU work without any I/O sleep, ensuring true GIL contention.

### `ParallelMapReducer` Class (Lines 71–151)
- **Lines 80–88 (`_create_chunks`):** Partitions input data into `num_workers * 2` balanced slices using integer division ceiling math.
- **Lines 99–112 (Queue & Process Setup):**
  Creates `task_queue` and `result_queue`. Enqueues all chunks, followed by `self.num_workers` poison pills. Spawns and starts `mp.Process` workers with `p.daemon = True`.
- **Lines 125–132 (Parent Collection & Error Propagation):**
  Parent reads exactly `total_chunks` items from `result_queue`. If `error is not None`, raises `WorkerProcessError` with the marshaled worker error message.
- **Lines 133–144 (`finally` Cleanup Protocol):**
  Crucial for preventing deadlocks:
  1. `p.join(timeout=3.0)` on all workers.
  2. `task_queue.close()` and `result_queue.close()`.
  3. `join_thread()` to ensure the background feeder thread flushes.
- **Lines 146–150 (Deterministic Reduction):**
  Sorts `intermediate_results` by `chunk_id` so map output order matches original input order, then executes `reduce_fn`.

---

## 4. How to Write It in a Live Interview (Step-by-Step Execution Order)

### Step 1: Skeleton & Core Data Structures (Mins 0–10)
Set up module-level worker entrypoint and `ParallelMapReducer` class:
```python
import multiprocessing as mp, os
from typing import Callable, Any

_POISON_PILL = None
class WorkerProcessError(Exception): pass

def _map_worker(worker_id, task_q, res_q, map_fn):
    while True:
        task = task_q.get()
        if task is _POISON_PILL: break
        chunk_id, data = task
        try:
            res_q.put((chunk_id, map_fn(data), None))
        except Exception as exc:
            res_q.put((chunk_id, None, (type(exc).__name__, str(exc))))
```

### Step 2: The Happy Path Core Logic (Mins 10–22)
Implement balanced chunking and basic process spawning:
- Write `_create_chunks(items, count)` calculating slice indices.
- In `run()`: instantiate `task_q` and `res_q`, enqueue chunks and poison pills, spawn `mp.Process(target=_map_worker, ...)`, start workers, and collect from `res_q`.

### Step 3: Edge Cases, Concurrency & Safety Invariants (Mins 22–35)
Now implement the Staff-level safety guarantees:
- **Windows `spawn` compatibility:** Ensure `mp.freeze_support()` is placed in `__main__` and all worker/reducer callables are at module level.
- **The IPC Deadlock Guard:** In `finally:`, join worker processes *after* draining the queue, and explicitly close and join queue feeder threads.
- **Error Propagation:** Check for worker exceptions in the parent collection loop and re-raise `WorkerProcessError`.
- **Input Ordering Preservation:** Sort collected map outputs by `chunk_id` before passing to `reduce_fn`.

### Step 4: Verification Driver (Mins 35–45)
Write parallel vs sequential benchmark in `if __name__ == "__main__":`:
1. Use `mp.freeze_support()`.
2. Compute CPU task across 6,000 items in parallel vs sequentially.
3. Assert `parallel_result == sequential_result`.
4. Test worker failure: pass `failing_worker` and assert `WorkerProcessError` is raised in parent.

---

## 5. Must-Memorize Syntax & Idioms (The Cheat Sheet)

```python
# 1. Windows/Mac freeze_support guard in test driver
if __name__ == "__main__":
    mp.freeze_support()  # Mandatory for multiprocessing on Windows / frozen binaries

# 2. Creating and launching an isolated OS Process
p = mp.Process(target=worker_fn, args=(arg1, arg2), daemon=True)
p.start()
p.join(timeout=3.0)

# 3. Proper Multiprocessing Queue Cleanup Sequence
# Always drain results from the queue BEFORE joining worker processes!
results = [result_queue.get() for _ in range(num_tasks)]
for p in processes: p.join()
result_queue.close()
result_queue.join_thread()

# 4. Balanced chunking formula
chunk_size = (total + num_chunks - 1) // num_chunks
chunks = [data[i:i + chunk_size] for i in range(0, total, chunk_size)]
```

---

## 6. Common Traps & Follow-Up Curveballs

### 3 Mistakes That Fail the Interview
1. **Joining Processes Before Reading the Queue:** If a child process writes a large result to `multiprocessing.Queue`, the OS pipe buffer fills up. The child blocks inside `put()` waiting for the buffer to drain. If the parent calls `process.join()`, both processes wait on each other forever (Deadlock!).
2. **Defining Worker Functions Inside `__main__` or Methods:** Under `spawn` (Windows/macOS default), the interpreter re-imports the main file. Functions defined inside closures or `if __name__ == "__main__":` cannot be found by pickle, crashing the entire run.
3. **Missing `mp.freeze_support()`:** On Windows, omitting `mp.freeze_support()` causes endless recursive process spawning forks.

### 2 Bar-Raiser Follow-Ups
1. **"How would you eliminate IPC queue serialization overhead for multi-gigabyte numerical arrays?"**
   *Answer:* Use `multiprocessing.shared_memory.SharedMemory` or `multiprocessing.Array`. Allocate a shared block of memory once; worker processes receive pointer offsets to their assigned slice, eliminating serialization and memory duplication.
2. **"How do you handle worker crashes caused by OS-level segfaults or OOM killer (SIGKILL) where Python exceptions cannot be caught?"**
   *Answer:* The parent process monitors `process.exitcode`. If a worker terminates with non-zero exit code or `exitcode < 0` (killed by signal), the orchestrator identifies the unfulfilled `chunk_id` and restarts a fresh worker process to retry the chunk.
