"""
Task Scheduler - Concise Interview Solution (Python)

1. Primary Capabilities:
- Directed Acyclic Graph (DAG) task execution based on dependencies.
- Kahn's algorithm (in-degree tracking + priority queue) for topological ordering.
- Lifecycle state transitions (PENDING -> RUNNING -> COMPLETED/FAILED).
- Simple observer callback on task execution events.

2. Error Handling:
- Cycle Detection: Detects circular dependencies if processed tasks < total tasks; raises ValueError.
- Task Failure: Catches action exceptions, flags task as FAILED, notifies observer, and halts execution.

3. Out Of Scope:
- Distributed multi-worker cluster (Celery / Ray).
- Persistent task storage and database transaction logging.
- Advanced cron syntax parsing (* * * * *).
"""

from collections import defaultdict
from dataclasses import dataclass, field
import heapq
from typing import Callable, Dict, List, Set, Any


@dataclass
class Task:
    task_id: str
    action: Callable[[], Any]
    priority: int = 0
    dependencies: Set[str] = field(default_factory=set)


class TaskScheduler:
    def __init__(self) -> None:
        self.tasks: Dict[str, Task] = {}

    def add_task(self, task: Task) -> None:
        self.tasks[task.task_id] = task

    def execute(self, observer: Callable[[str, str], None] = None) -> List[str]:
        # 1. Compute In-Degrees and Dependents Graph
        in_degree = {t_id: len(t.dependencies) for t_id, t in self.tasks.items()}
        graph = defaultdict(list)
        for t_id, t in self.tasks.items():
            for dep in t.dependencies:
                graph[dep].append(t_id)

        # 2. Priority Queue: (-priority, task_id) for max-heap behavior
        pq = [(-self.tasks[t_id].priority, t_id) for t_id, deg in in_degree.items() if deg == 0]
        heapq.heapify(pq)

        order = []
        while pq:
            _, curr_id = heapq.heappop(pq)
            order.append(curr_id)
            if observer:
                observer(curr_id, "RUNNING")
            try:
                self.tasks[curr_id].action()
                if observer:
                    observer(curr_id, "COMPLETED")
            except Exception:
                if observer:
                    observer(curr_id, "FAILED")
                raise

            for neighbor in graph[curr_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    heapq.heappush(pq, (-self.tasks[neighbor].priority, neighbor))

        if len(order) != len(self.tasks):
            raise ValueError("Cycle detected in task dependencies!")
        return order


if __name__ == "__main__":
    s = TaskScheduler()
    res = []
    s.add_task(Task("build", lambda: res.append("build"), priority=1))
    s.add_task(Task("lint", lambda: res.append("lint"), priority=2, dependencies={"build"}))
    s.add_task(Task("test", lambda: res.append("test"), priority=1, dependencies={"build"}))
    s.add_task(Task("deploy", lambda: res.append("deploy"), priority=0, dependencies={"lint", "test"}))

    order = s.execute(lambda tid, st: print(f"[{st}] {tid}"))
    assert order == ["build", "lint", "test", "deploy"]
    print("Interview Python TaskScheduler passed!")
