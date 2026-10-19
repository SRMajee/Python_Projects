"""
Distributed Task Worker - Complete Solution (Python)
Celery-like multi-process task execution:
- Broker: in-memory queue dispatching tasks to workers
- Worker processes bypass GIL for CPU-bound work
- Result backend for collecting results
- Task decorator for registration
- Retry with exponential backoff
Concurrency: multiprocessing.Queue + Process for true parallelism.
"""
import multiprocessing as mp
import time
import traceback
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Callable
import queue


class TaskState(Enum):
    PENDING = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILURE = auto()
    RETRY = auto()


@dataclass
class TaskResult:
    task_id: str
    state: TaskState
    result: Any = None
    error: str = ""
    retries: int = 0


class ResultBackend:
    """Thread/process-safe result storage using Manager dict."""
    def __init__(self, manager: mp.Manager):
        self._store = manager.dict()
        self._lock = manager.Lock()

    def store(self, task_id: str, result: TaskResult):
        with self._lock:
            self._store[task_id] = {
                "task_id": result.task_id,
                "state": result.state.name,
                "result": result.result,
                "error": result.error,
                "retries": result.retries,
            }

    def get(self, task_id: str) -> dict | None:
        with self._lock:
            return dict(self._store.get(task_id, {})) or None

    def wait_for(self, task_id: str, timeout: float = 30.0) -> dict | None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            result = self.get(task_id)
            if result and result.get("state") in ("SUCCESS", "FAILURE"):
                return result
            time.sleep(0.05)
        return None


class TaskRegistry:
    """Registry for task functions."""
    _tasks: dict[str, Callable] = {}

    @classmethod
    def register(cls, name: str | None = None):
        def decorator(fn: Callable) -> Callable:
            task_name = name or fn.__name__
            cls._tasks[task_name] = fn
            fn.task_name = task_name
            return fn
        return decorator

    @classmethod
    def get(cls, name: str) -> Callable | None:
        return cls._tasks.get(name)


def _worker_process(task_queue: mp.Queue, result_backend_store: dict,
                    result_lock, worker_id: int, registry_tasks: dict):
    """Worker process main loop."""
    while True:
        try:
            item = task_queue.get(timeout=1.0)
        except queue.Empty:
            continue
        if item is None:
            break

        task_id, task_name, args, kwargs, max_retries = item
        fn = registry_tasks.get(task_name)
        if not fn:
            with result_lock:
                result_backend_store[task_id] = {
                    "task_id": task_id, "state": "FAILURE",
                    "result": None, "error": f"Unknown task: {task_name}", "retries": 0
                }
            continue

        retries = 0
        while retries <= max_retries:
            try:
                with result_lock:
                    result_backend_store[task_id] = {
                        "task_id": task_id, "state": "RUNNING",
                        "result": None, "error": "", "retries": retries
                    }
                result = fn(*args, **kwargs)
                with result_lock:
                    result_backend_store[task_id] = {
                        "task_id": task_id, "state": "SUCCESS",
                        "result": result, "error": "", "retries": retries
                    }
                break
            except Exception as e:
                retries += 1
                if retries > max_retries:
                    with result_lock:
                        result_backend_store[task_id] = {
                            "task_id": task_id, "state": "FAILURE",
                            "result": None, "error": str(e), "retries": retries - 1
                        }
                else:
                    time.sleep(min(0.1 * (2 ** retries), 2.0))  # exponential backoff


class DistributedTaskWorker:
    """Main coordinator: broker + worker pool."""

    def __init__(self, num_workers: int = 4):
        if num_workers <= 0:
            raise ValueError("num_workers must be positive")
        self._num_workers = num_workers
        self._manager = mp.Manager()
        self._task_queue = mp.Queue()
        self._result_store = self._manager.dict()
        self._result_lock = self._manager.Lock()
        self._workers: list[mp.Process] = []
        self._task_counter = 0
        self._counter_lock = mp.Lock()
        self._started = False

    def start(self, registry_tasks: dict[str, Callable] | None = None):
        """Start worker processes."""
        tasks = registry_tasks or TaskRegistry._tasks
        for i in range(self._num_workers):
            p = mp.Process(
                target=_worker_process,
                args=(self._task_queue, self._result_store,
                      self._result_lock, i, tasks),
                daemon=True
            )
            p.start()
            self._workers.append(p)
        self._started = True

    def submit(self, task_name: str, *args, max_retries: int = 0, **kwargs) -> str:
        """Submit a task. Returns task_id."""
        if not self._started:
            raise RuntimeError("Workers not started")
        with self._counter_lock:
            self._task_counter += 1
            task_id = f"task_{self._task_counter}"
        with self._result_lock:
            self._result_store[task_id] = {
                "task_id": task_id, "state": "PENDING",
                "result": None, "error": "", "retries": 0
            }
        self._task_queue.put((task_id, task_name, args, kwargs, max_retries))
        return task_id

    def get_result(self, task_id: str, timeout: float = 10.0) -> dict | None:
        """Wait for and return result."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._result_lock:
                result = self._result_store.get(task_id)
            if result and result.get("state") in ("SUCCESS", "FAILURE"):
                return dict(result)
            time.sleep(0.05)
        return None

    def shutdown(self):
        """Send poison pills and join workers."""
        for _ in self._workers:
            self._task_queue.put(None)
        for p in self._workers:
            p.join(timeout=5)
            if p.is_alive():
                p.terminate()
        self._manager.shutdown()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.shutdown()
