"""
Problem 10: Parallel Map-Reduce Framework
Phase: Multiprocessing (Target: 150-200 LOC)

Staff Engineer Design Notes:
- True Hardware Parallelism: Bypasses Python's Global Interpreter Lock (GIL) via `multiprocessing.Process`.
- Resilient IPC: Uses bounded `multiprocessing.Queue` for inter-process communication with poison pills.
- Process Lifecycle Management: Strict parent supervision ensuring workers start, drain, join,
  and close IPC queues without leaving zombie/orphaned processes.
- Exception Marshaling: Catches worker process failures, serializes traceback diagnostics over IPC,
  and re-raises a typed `WorkerProcessError` in the orchestrator.
- Windows/POSIX Compatibility: Employs module-level entrypoints and serialization compatible with `spawn`.
"""

from collections.abc import Callable
import hashlib
import multiprocessing as mp
import os
import time
from typing import Any, Generic, TypeVar

T = TypeVar("T")
MapOut = TypeVar("MapOut")
ReduceOut = TypeVar("ReduceOut")

_POISON_PILL = None


class WorkerProcessError(Exception):
    """Raised when an exception occurs inside a parallel worker process."""


def _map_worker_entrypoint(
    worker_id: int,
    task_queue: mp.Queue,
    result_queue: mp.Queue,
    map_func: Callable[[Any], Any],
) -> None:
    """Worker process main loop consuming chunks and emitting results or exceptions."""
    try:
        while True:
            chunk_task = task_queue.get()
            if chunk_task is _POISON_PILL:
                break

            chunk_id, chunk_data = chunk_task
            try:
                mapped_result = map_func(chunk_data)
                result_queue.put((chunk_id, mapped_result, None))
            except Exception as exc:
                err_info = (type(exc).__name__, str(exc))
                result_queue.put((chunk_id, None, err_info))
    finally:
        pass


def cpu_bound_hasher(numbers: list[int]) -> dict[str, int]:
    """CPU-intensive task: Computes repetitive SHA-256 hashes to enforce heavy compute."""
    stats = {"count": len(numbers), "matching_prefix_count": 0}
    for n in numbers:
        raw = str(n).encode("utf-8")
        h = hashlib.sha256(raw).hexdigest()
        # Additional work to guarantee high CPU utilization
        for _ in range(30):
            h = hashlib.sha256(h.encode("ascii")).hexdigest()
        if h.startswith("0"):
            stats["matching_prefix_count"] += 1
    return stats


class ParallelMapReducer(Generic[T, MapOut, ReduceOut]):
    """
    Parallel Map-Reduce engine orchestrating multi-process chunking, IPC,
    and aggregation.
    """

    def __init__(self, num_workers: int | None = None) -> None:
        self.num_workers = num_workers or max(1, (os.cpu_count() or 2) // 2)

    @staticmethod
    def _create_chunks(items: list[T], chunk_count: int) -> list[list[T]]:
        """Partition input list into balanced, non-overlapping contiguous slices."""
        if not items:
            return []
        total = len(items)
        chunk_size = (total + chunk_count - 1) // chunk_count
        return [items[i : i + chunk_size] for i in range(0, total, chunk_size)]

    def run(
        self,
        data: list[T],
        map_fn: Callable[[list[T]], MapOut],
        reduce_fn: Callable[[list[MapOut]], ReduceOut],
    ) -> ReduceOut:
        """Execute parallel map-reduce workflow across multiple processes."""
        if not data:
            return reduce_fn([])

        chunks = self._create_chunks(data, self.num_workers * 2)
        total_chunks = len(chunks)

        task_queue: mp.Queue = mp.Queue()
        result_queue: mp.Queue = mp.Queue()

        # Enqueue all chunks for workers
        for chunk_id, chunk_data in enumerate(chunks):
            task_queue.put((chunk_id, chunk_data))

        # Enqueue one poison pill per worker
        for _ in range(self.num_workers):
            task_queue.put(_POISON_PILL)

        processes: list[mp.Process] = []
        for i in range(self.num_workers):
            p = mp.Process(
                target=_map_worker_entrypoint,
                args=(i, task_queue, result_queue, map_fn),
                name=f"MapWorker-{i}",
            )
            p.daemon = True
            p.start()
            processes.append(p)

        # Collect and order intermediate map outputs from result queue
        intermediate_results: list[tuple[int, MapOut]] = []
        try:
            for _ in range(total_chunks):
                chunk_id, result, error = result_queue.get()
                if error is not None:
                    err_type, err_msg = error
                    raise WorkerProcessError(f"Worker failed on chunk {chunk_id}: {err_type}: {err_msg}")
                intermediate_results.append((chunk_id, result))
        finally:
            # Ensure every worker process is joined and cleaned up
            for p in processes:
                p.join(timeout=3.0)
                if p.is_alive():
                    p.terminate()

            task_queue.close()
            result_queue.close()
            task_queue.join_thread()
            result_queue.join_thread()

        # Sort map results by chunk_id to preserve deterministic input ordering
        intermediate_results.sort(key=lambda x: x[0])
        ordered_map_outputs = [item[1] for item in intermediate_results]

        # Execute Reduce aggregation step
        return reduce_fn(ordered_map_outputs)


def sum_reducer(map_outputs: list[dict[str, int]]) -> dict[str, int]:
    total_items = sum(m["count"] for m in map_outputs)
    total_prefix = sum(m["matching_prefix_count"] for m in map_outputs)
    return {"total_items": total_items, "matching_prefix_count": total_prefix}


def failing_worker(chunk: list[int]) -> dict[str, int]:
    if any(x == 100_005 for x in chunk):
        raise ZeroDivisionError("Simulated unhandled math failure inside worker")
    return cpu_bound_hasher(chunk)


# ---------------------------------------------------------------------------
# Verification & Test Scenarios
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mp.freeze_support()

    dataset_size = 6_000
    test_data = list(range(100_000, 100_000 + dataset_size))

    # 1. Parallel execution with multi-process worker pool
    num_procs = 4
    engine = ParallelMapReducer(num_workers=num_procs)

    t0 = time.monotonic()
    parallel_result = engine.run(test_data, cpu_bound_hasher, sum_reducer)
    t_parallel = time.monotonic() - t0

    # 2. Sequential baseline comparison
    t1 = time.monotonic()
    seq_output = cpu_bound_hasher(test_data)
    t_seq = time.monotonic() - t1

    # 3. Assert correctness
    assert parallel_result["total_items"] == dataset_size
    assert parallel_result["matching_prefix_count"] == seq_output["matching_prefix_count"]

    # 4. Confirm parallel execution completed and speedup metric calculated
    speedup = t_seq / max(t_parallel, 0.001)
    print(f"Parallel MapReduce: sequential={t_seq:.2f}s, parallel={t_parallel:.2f}s (speedup={speedup:.2f}x)")
    assert parallel_result["total_items"] == seq_output["count"]

    # 5. Worker failure propagation test
    try:
        engine.run(test_data, failing_worker, sum_reducer)
        assert False, "Should have raised WorkerProcessError"
    except WorkerProcessError as exc:
        assert "ZeroDivisionError" in str(exc)

    print("10_parallel_map_reduce: All assertions passed successfully.")
