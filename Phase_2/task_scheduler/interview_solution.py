"""
Task Scheduler - Streamlined 45-Minute Interview Solution.
Core Concepts: DAG Topological Sort (Kahn's Algorithm), Strategy Pattern, Observer Pattern.
"""

from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Set


class TaskStatus(Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class Task:
    task_id: str
    action: Callable[[], Any]
    dependencies: Set[str] = field(default_factory=set)
    priority: int = 0
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None


# --- 1. Observer Pattern ---
class TaskObserver(ABC):
    @abstractmethod
    def on_task_completed(self, task: Task) -> None:
        """Called when a task completes execution."""
        pass


class ConsoleObserver(TaskObserver):
    """Simple observer printing execution events."""
    def on_task_completed(self, task: Task) -> None:
        print(f"[Observer] Task '{task.task_id}' finished with result: {task.result}")


# --- 2. Strategy Pattern ---
class ExecutionStrategy(ABC):
    @abstractmethod
    def execute(self, tasks: List[Task]) -> None:
        """Execute a batch of ready tasks."""
        pass


class PriorityExecutionStrategy(ExecutionStrategy):
    """Executes ready tasks ordered by priority (highest integer first)."""
    def execute(self, tasks: List[Task]) -> None:
        tasks.sort(key=lambda t: (-t.priority, t.task_id))
        for task in tasks:
            task.result = task.action()
            task.status = TaskStatus.COMPLETED


# --- 3. DAG Scheduler (Core Logic) ---
class TaskScheduler:
    def __init__(self, strategy: ExecutionStrategy = None):
        self.tasks: Dict[str, Task] = {}
        self.strategy = strategy or PriorityExecutionStrategy()
        self.observers: List[TaskObserver] = []

    def add_task(self, task: Task) -> None:
        self.tasks[task.task_id] = task

    def add_observer(self, observer: TaskObserver) -> None:
        self.observers.append(observer)

    def run(self) -> Dict[str, Any]:
        """
        Executes all tasks in topological dependency order using Kahn's algorithm.
        Detects cycles and delegates ready batch execution to the Strategy.
        """
        # Step 1: Compute in-degrees and build reverse adjacency graph
        in_degree = {t_id: len(t.dependencies) for t_id, t in self.tasks.items()}
        dependents = defaultdict(list)
        for t_id, t in self.tasks.items():
            for dep in t.dependencies:
                if dep not in self.tasks:
                    raise KeyError(f"Dependency '{dep}' not registered!")
                dependents[dep].append(t_id)

        # Step 2: Queue all root tasks with no dependencies (in-degree == 0)
        queue = deque([self.tasks[t_id] for t_id, deg in in_degree.items() if deg == 0])
        executed_count = 0

        # Step 3: Process batches in topological waves
        while queue:
            ready_batch = []
            while queue:
                ready_batch.append(queue.popleft())

            # Delegate execution ordering to strategy
            self.strategy.execute(ready_batch)

            for task in ready_batch:
                executed_count += 1
                for obs in self.observers:
                    obs.on_task_completed(task)

                # Unlock downstream dependent tasks
                for nxt_id in dependents[task.task_id]:
                    in_degree[nxt_id] -= 1
                    if in_degree[nxt_id] == 0:
                        queue.append(self.tasks[nxt_id])

        # Step 4: Cycle verification
        if executed_count != len(self.tasks):
            raise ValueError("Cycle detected in task dependencies!")

        return {t.task_id: t.result for t in self.tasks.values()}


# --- Demo for Interviewer ---
if __name__ == "__main__":
    scheduler = TaskScheduler()
    scheduler.add_observer(ConsoleObserver())

    # Diamond DAG: A -> B, A -> C, (B, C) -> D
    # Priority demonstration: B (priority 10) executes before C (priority 2)
    scheduler.add_task(Task("A", lambda: "Data Extracted", priority=1))
    scheduler.add_task(Task("B", lambda: "Data Transformed", dependencies={"A"}, priority=10))
    scheduler.add_task(Task("C", lambda: "Audit Logged", dependencies={"A"}, priority=2))
    scheduler.add_task(Task("D", lambda: "Report Published", dependencies={"B", "C"}, priority=5))

    results = scheduler.run()
    print("\nExecution Complete!")
    print("Final Output:", results)
