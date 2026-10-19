"""
Custom Thread Pool Executor - Complete Solution (Python)
ThreadPoolExecutor built from scratch using:
- Worker threads pulling from a shared task queue
- Future objects for result retrieval (blocking get, timeout, cancel)
- Graceful shutdown (wait for pending) and immediate shutdown
- Dynamic task submission with callable + args
Concurrency: Core design IS concurrent - queue.Queue + threading.Condition.
"""
import threading
import queue
import time
from enum import Enum, auto
from typing import Any, Callable


class FutureState(Enum):
    PENDING = auto()
    RUNNING = auto()
    DONE = auto()
    CANCELLED = auto()
    ERROR = auto()


class Future:
    """Represents the result of an async computation."""

    def __init__(self):
        self._state = FutureState.PENDING
        self._result: Any = None
        self._exception: Exception | None = None
        self._cond = threading.Condition()
        self._callbacks: list[Callable] = []

    @property
    def state(self) -> FutureState:
        with self._cond:
            return self._state

    def result(self, timeout: float | None = None) -> Any:
        """Block until result is ready or timeout expires."""
        with self._cond:
            if self._state == FutureState.CANCELLED:
                raise RuntimeError("Future was cancelled")
            if self._state not in (FutureState.DONE, FutureState.ERROR):
                self._cond.wait(timeout=timeout)
            if self._state == FutureState.ERROR:
                raise self._exception
            if self._state == FutureState.CANCELLED:
                raise RuntimeError("Future was cancelled")
            if self._state != FutureState.DONE:
                raise TimeoutError("Future not ready")
            return self._result

    def cancel(self) -> bool:
        """Attempt to cancel. Only works if still PENDING."""
        with self._cond:
            if self._state != FutureState.PENDING:
                return False
            self._state = FutureState.CANCELLED
            self._cond.notify_all()
            return True

    def done(self) -> bool:
        with self._cond:
            return self._state in (FutureState.DONE, FutureState.ERROR, FutureState.CANCELLED)

    def _set_running(self):
        with self._cond:
            if self._state == FutureState.CANCELLED:
                return False
            self._state = FutureState.RUNNING
            return True

    def _set_result(self, result: Any):
        with self._cond:
            self._result = result
            self._state = FutureState.DONE
            self._cond.notify_all()
        self._invoke_callbacks()

    def _set_exception(self, exc: Exception):
        with self._cond:
            self._exception = exc
            self._state = FutureState.ERROR
            self._cond.notify_all()
        self._invoke_callbacks()

    def add_callback(self, fn: Callable):
        with self._cond:
            if self._state in (FutureState.DONE, FutureState.ERROR):
                fn(self)
                return
            self._callbacks.append(fn)

    def _invoke_callbacks(self):
        for cb in self._callbacks:
            try:
                cb(self)
            except Exception:
                pass


class ThreadPool:
    """Custom thread pool executor."""

    def __init__(self, max_workers: int = 4):
        if max_workers <= 0:
            raise ValueError("max_workers must be positive")
        self._max_workers = max_workers
        self._task_queue: queue.Queue[tuple[Future, Callable, tuple, dict] | None] = queue.Queue()
        self._workers: list[threading.Thread] = []
        self._shutdown = False
        self._lock = threading.Lock()

        for i in range(max_workers):
            t = threading.Thread(target=self._worker, name=f"pool-worker-{i}", daemon=True)
            t.start()
            self._workers.append(t)

    def _worker(self):
        while True:
            item = self._task_queue.get()
            if item is None:
                self._task_queue.task_done()
                break
            future, fn, args, kwargs = item
            if not future._set_running():
                self._task_queue.task_done()
                continue
            try:
                result = fn(*args, **kwargs)
                future._set_result(result)
            except Exception as e:
                future._set_exception(e)
            finally:
                self._task_queue.task_done()

    def submit(self, fn: Callable, *args, **kwargs) -> Future:
        """Submit a callable for async execution. Returns a Future."""
        with self._lock:
            if self._shutdown:
                raise RuntimeError("Pool is shut down")
            future = Future()
            self._task_queue.put((future, fn, args, kwargs))
            return future

    def map(self, fn: Callable, *iterables, timeout: float | None = None) -> list:
        """Submit all items and collect results in order."""
        futures = [self.submit(fn, *args) for args in zip(*iterables)]
        return [f.result(timeout=timeout) for f in futures]

    def shutdown(self, wait: bool = True):
        """Gracefully shut down the pool."""
        with self._lock:
            self._shutdown = True
        for _ in self._workers:
            self._task_queue.put(None)
        if wait:
            for t in self._workers:
                t.join()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.shutdown(wait=True)
