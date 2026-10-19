"""DAG-based Task Scheduler supporting Strategy and Observer design patterns."""

from __future__ import annotations

import collections
import concurrent.futures
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
import time
from typing import Any, Callable, Dict, List, Optional, Set


class TaskStatus(Enum):
    """Lifecycle states of an individual task."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class TaskEventType(Enum):
    """Event types published during task execution."""
    WORKFLOW_STARTED = auto()
    WORKFLOW_COMPLETED = auto()
    TASK_STARTED = auto()
    TASK_COMPLETED = auto()
    TASK_FAILED = auto()
    TASK_SKIPPED = auto()


@dataclass
class TaskEvent:
    """Event payload emitted to registered observers."""
    event_type: TaskEventType
    task_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    message: str = ""
    error: Optional[Exception] = None


class TaskObserver(ABC):
    """Observer interface for listening to task execution events."""

    @abstractmethod
    def on_event(self, event: TaskEvent) -> None:
        """Handle incoming task lifecycle event."""
        ...


class HistoryObserver(TaskObserver):
    """Records complete event sequence for auditing and inspection."""

    def __init__(self) -> None:
        self.events: List[TaskEvent] = []

    def on_event(self, event: TaskEvent) -> None:
        self.events.append(event)


class MetricsObserver(TaskObserver):
    """Tracks task state metrics and overall execution duration."""

    def __init__(self) -> None:
        self.counts: Dict[TaskStatus, int] = {s: 0 for s in TaskStatus}
        self.total_duration: float = 0.0
        self._start_time: Optional[float] = None

    def on_event(self, event: TaskEvent) -> None:
        if event.event_type == TaskEventType.WORKFLOW_STARTED:
            self._start_time = event.timestamp
        elif event.event_type == TaskEventType.WORKFLOW_COMPLETED and self._start_time is not None:
            self.total_duration = event.timestamp - self._start_time
        elif event.event_type in (TaskEventType.TASK_COMPLETED, TaskEventType.TASK_FAILED, TaskEventType.TASK_SKIPPED):
            status_map = {
                TaskEventType.TASK_COMPLETED: TaskStatus.COMPLETED,
                TaskEventType.TASK_FAILED: TaskStatus.FAILED,
                TaskEventType.TASK_SKIPPED: TaskStatus.SKIPPED,
            }
            self.counts[status_map[event.event_type]] += 1


class CycleDetectedError(ValueError):
    """Raised when dependency graph contains a cyclic dependency."""
    pass


@dataclass
class Task:
    """Represents an executable unit in the DAG with dependencies and priority."""
    task_id: str
    action: Callable[[], Any]
    dependencies: Set[str] = field(default_factory=set)
    priority: int = 0
    max_retries: int = 0
    interval: Optional[float] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    retry_count: int = 0
    last_run: Optional[float] = None

    def is_due(self, current_time: float) -> bool:
        """Check if periodic task is due to execute."""
        if self.interval is None:
            return False
        return self.last_run is None or (current_time - self.last_run) >= self.interval

    def reset(self) -> None:
        """Reset execution state for subsequent runs."""
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.retry_count = 0


class ExecutionStrategy(ABC):
    """Abstract Strategy defining how ready tasks are executed."""

    @abstractmethod
    def execute(self, scheduler: TaskScheduler) -> Dict[str, Any]:
        """Execute tasks within scheduler according to strategy policy."""
        ...


class SequentialStrategy(ExecutionStrategy):
    """Executes ready tasks sequentially, sorted by priority (descending)."""

    def execute(self, scheduler: TaskScheduler) -> Dict[str, Any]:
        while True:
            ready_tasks = scheduler.get_ready_tasks()
            if not ready_tasks:
                break
            ready_tasks.sort(key=lambda t: (-t.priority, t.task_id))
            for task in ready_tasks:
                scheduler.run_task(task)
        return {t.task_id: t.result for t in scheduler.tasks.values()}


class ConcurrentStrategy(ExecutionStrategy):
    """Executes independent ready tasks concurrently across a thread pool."""

    def __init__(self, max_workers: int = 4) -> None:
        self.max_workers = max_workers

    def execute(self, scheduler: TaskScheduler) -> Dict[str, Any]:
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            in_flight: Dict[concurrent.futures.Future[Any], Task] = {}
            while True:
                ready_tasks = scheduler.get_ready_tasks()
                ready_tasks.sort(key=lambda t: (-t.priority, t.task_id))
                for task in ready_tasks:
                    task.status = TaskStatus.RUNNING
                    scheduler.notify(TaskEvent(TaskEventType.TASK_STARTED, task.task_id))
                    future = executor.submit(scheduler.execute_action, task)
                    in_flight[future] = task

                if not in_flight:
                    break

                done, _ = concurrent.futures.wait(
                    in_flight.keys(), return_when=concurrent.futures.FIRST_COMPLETED
                )
                for future in done:
                    task = in_flight.pop(future)
                    try:
                        scheduler.complete_task(task, future.result())
                    except Exception as exc:
                        scheduler.fail_or_retry_task(task, exc)

        return {t.task_id: t.result for t in scheduler.tasks.values()}


class TaskScheduler:
    """DAG Task Scheduler orchestrating dependency resolution and notifications."""

    def __init__(self, strategy: Optional[ExecutionStrategy] = None) -> None:
        self.tasks: Dict[str, Task] = {}
        self.observers: List[TaskObserver] = []
        self.strategy: ExecutionStrategy = strategy if strategy is not None else SequentialStrategy()
        self._current_time: Optional[float] = None

    def add_task(self, task: Task) -> None:
        """Register a new task in the scheduler."""
        if task.task_id in self.tasks:
            raise ValueError(f"Task '{task.task_id}' is already registered.")
        self.tasks[task.task_id] = task

    def add_observer(self, observer: TaskObserver) -> None:
        """Register an observer for task lifecycle events."""
        self.observers.append(observer)

    def remove_observer(self, observer: TaskObserver) -> None:
        """Unregister an observer."""
        self.observers.remove(observer)

    def notify(self, event: TaskEvent) -> None:
        """Dispatch lifecycle event to all subscribed observers."""
        for obs in self.observers:
            obs.on_event(event)

    def validate_dag(self) -> List[str]:
        """Validate DAG: ensure dependencies exist and detect cycles via Kahn's algorithm."""
        for task in self.tasks.values():
            for dep in task.dependencies:
                if dep not in self.tasks:
                    raise KeyError(f"Dependency '{dep}' required by '{task.task_id}' not found.")

        in_degree = {t_id: len(t.dependencies) for t_id, t in self.tasks.items()}
        queue = collections.deque([t_id for t_id, deg in in_degree.items() if deg == 0])
        order: List[str] = []
        dependents: Dict[str, List[str]] = collections.defaultdict(list)
        for t_id, t in self.tasks.items():
            for dep in t.dependencies:
                dependents[dep].append(t_id)

        while queue:
            curr = queue.popleft()
            order.append(curr)
            for nxt in dependents[curr]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)

        if len(order) != len(self.tasks):
            raise CycleDetectedError("Cycle detected in task dependencies.")
        return order

    def get_ready_tasks(self) -> List[Task]:
        """Retrieve all PENDING tasks whose dependencies have successfully COMPLETED."""
        return [
            t for t in self.tasks.values()
            if t.status == TaskStatus.PENDING
            and all(self.tasks[d].status == TaskStatus.COMPLETED for d in t.dependencies)
        ]

    def skip_dependents(self, failed_task_id: str) -> None:
        """Recursively mark all downstream tasks dependent on failed_task_id as SKIPPED."""
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING and failed_task_id in task.dependencies:
                task.status = TaskStatus.SKIPPED
                self.notify(TaskEvent(TaskEventType.TASK_SKIPPED, task.task_id, message=f"Dep '{failed_task_id}' failed"))
                self.skip_dependents(task.task_id)

    def execute_action(self, task: Task) -> Any:
        """Execute task callable."""
        return task.action()

    def complete_task(self, task: Task, result: Any) -> None:
        """Mark task completed and dispatch observer notification."""
        task.result = result
        task.status = TaskStatus.COMPLETED
        task.last_run = self._current_time if self._current_time is not None else time.time()
        self.notify(TaskEvent(TaskEventType.TASK_COMPLETED, task.task_id, timestamp=task.last_run))

    def fail_or_retry_task(self, task: Task, exc: Exception) -> bool:
        """Retry task if retries remaining; otherwise mark failed and skip downstream."""
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.PENDING
            return True
        task.error = exc
        task.status = TaskStatus.FAILED
        self.notify(TaskEvent(TaskEventType.TASK_FAILED, task.task_id, error=exc))
        self.skip_dependents(task.task_id)
        return False

    def run_task(self, task: Task) -> None:
        """Run a single task sequentially, handling retries, failures, and notifications."""
        task.status = TaskStatus.RUNNING
        self.notify(TaskEvent(TaskEventType.TASK_STARTED, task.task_id))
        while True:
            try:
                self.complete_task(task, self.execute_action(task))
                break
            except Exception as exc:
                if not self.fail_or_retry_task(task, exc):
                    break

    def run(self) -> Dict[str, Any]:
        """Validate DAG and execute tasks using the configured strategy."""
        self.validate_dag()
        self.notify(TaskEvent(TaskEventType.WORKFLOW_STARTED))
        results = self.strategy.execute(self)
        self.notify(TaskEvent(TaskEventType.WORKFLOW_COMPLETED))
        return results

    def tick(self, current_time: Optional[float] = None) -> List[str]:
        """Periodic trigger: resets and executes tasks due at current_time."""
        now = current_time if current_time is not None else time.time()
        due_tasks = [t for t in self.tasks.values() if t.is_due(now)]
        if not due_tasks:
            return []
        for t in due_tasks:
            t.reset()
        self._current_time = now
        try:
            self.run()
        finally:
            self._current_time = None
        return [t.task_id for t in due_tasks]
