# Task Scheduler: 45-Minute Interview Blueprint

A practical guide on **what to actually write** in a Low-Level Design (LLD) / Machine Coding interview, what to deliberately leave out, and how to address standard follow-ups.

---

## 1. The 45-Minute Reality Check

In an LLD interview, candidates often fail by trying to build an entire production engine (multithreaded thread pools, dynamic retry backoffs, complex metrics, cron parsers) and running out of time.

| Category | What to Code Live (See [`interview_solution.py`](./interview_solution.py)) | What to State Verbally (Leave out of initial code) |
| :--- | :--- | :--- |
| **Data Models** | Simple `Task` dataclass (`task_id`, `action`, `dependencies`, `priority`, `status`, `result`). | Complex state machines, persistent DB schemas, metadata dicts. |
| **Core Algorithm** | **Kahn's Algorithm** with an in-degree map and dependency queue for topological order + cycle detection. | Recursive graph traversal or DFS tarjan strongly connected components. |
| **Strategy Pattern** | `ExecutionStrategy` interface + `PriorityExecutionStrategy` sorting ready tasks. | Full thread pool executor, distributed task queue (Celery/RabbitMQ). |
| **Observer Pattern** | `TaskObserver` interface + `ConsoleObserver` with `on_task_completed()`. | Event buses, async websockets, persistent audit databases. |
| **Cron / Scheduling** | Verbal explanation with a `next_run_time` min-heap. | Full cron expression parsers or continuous sleep loops. |

---

## 2. Step-by-Step Interview Game Plan

### Phase 1: Clarify & Scope (Minutes 0 – 5)

Tell the interviewer:

> *"I'll structure the system around three key architectural components:*
>
> 1. *A **DAG Task Graph** using **Kahn's Algorithm (Topological Sort)** to resolve dependencies and detect cycles.*
> 2. *The **Strategy Pattern** to decouple how ready tasks are executed (e.g., priority-based ordering vs. concurrent execution).*
> 3. *The **Observer Pattern** to broadcast execution lifecycle events to external listeners (logging, metrics).*
>
> *I will focus on the core in-memory algorithm first, and we can discuss concurrency and cron intervals as follow-ups."*

### Phase 2: Core Data Models & Interfaces (Minutes 5 – 15)

Write the minimal `TaskStatus` enum, `Task` dataclass, and pattern interfaces:

```python
@dataclass
class Task:
    task_id: str
    action: Callable[[], Any]
    dependencies: Set[str] = field(default_factory=set)
    priority: int = 0
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None

class TaskObserver(ABC):
    @abstractmethod
    def on_task_completed(self, task: Task) -> None: ...

class ExecutionStrategy(ABC):
    @abstractmethod
    def execute(self, tasks: List[Task]) -> None: ...
```

### Phase 3: Kahn's Algorithm & Scheduler Core (Minutes 15 – 30)

Implement the core resolution logic in `TaskScheduler.run()`:

1. **In-Degrees**: Count how many uncompleted dependencies each task has.
2. **Dependents Map**: Reverse adjacency map (`dep -> [downstream_tasks]`).
3. **Queue**: Seed with all tasks having `in_degree == 0`.
4. **Batch Execution**: Pop all currently ready tasks, pass to `self.strategy.execute(ready_batch)`.
5. **Unlock Downstream**: For each finished task, decrement dependent in-degrees. When in-degree reaches `0`, enqueue.
6. **Cycle Check**: If `executed_count != len(self.tasks)`, raise `ValueError("Cycle detected")`.

### Phase 4: Strategy & Observer Concrete Classes (Minutes 30 – 38)

Implement `PriorityExecutionStrategy` and `ConsoleObserver`.

### Phase 5: Demo Verification (Minutes 38 – 45)

Write a Diamond DAG demo (`A -> B, A -> C, (B, C) -> D`) with different priorities and execute it live.

---

## 3. High-Probability Follow-Up Questions

### Q1: How do you detect circular dependencies (deadlocks)?

**Answer**:

> *"Kahn's algorithm naturally detects cycles. If there is a cycle, the tasks involved in the cycle will never reach an `in_degree` of 0 and will never enter the queue. Therefore, if `executed_count < len(self.tasks)` when the queue empties, a cycle exists."*

### Q2: How would you make independent tasks execute concurrently?

**Answer**:

> *"Thanks to the Strategy Pattern, we can swap in a `ConcurrentExecutionStrategy` without modifying the scheduler. When a batch of tasks has `in_degree == 0`, we submit them to a `ThreadPoolExecutor`. When a future completes, we decrement downstream in-degrees under a threading Lock."*

### Q3: What happens if an upstream task fails?

**Answer**:

> *"We catch the exception, mark the failing task as `FAILED`, and trigger a cascade skip: all downstream dependent tasks are recursively marked as `SKIPPED` and not scheduled. Independent branches in the DAG continue to execute normally."*

### Q4: How would you support Cron / Periodic tasks?

**Answer**:

> *"Instead of a simple FIFO queue, we store scheduled tasks in a **Min-Heap (Priority Queue)** keyed by `(next_run_timestamp, task)`. The scheduler loop inspects `heap[0]`:*
>
> - *If `current_time >= next_run_timestamp`, pop the task, execute the DAG, and push it back with `next_run_timestamp += interval`.*
> - *If not due, `time.sleep(next_run_timestamp - current_time)`."*

### Q5: How would you scale this to a distributed system?

**Answer**:

> *"We separate the **Scheduler / Coordinator** from the **Workers**:*
>
> 1. *Store task states and DAG graph in a database (e.g. Postgres or Redis).*
> 2. *When a task's dependencies are satisfied, the coordinator publishes a task message to a distributed message queue (RabbitMQ / Kafka / Celery).*
> 3. *Worker nodes pull tasks, execute the action, and publish completion events back to unlock the next wave."*
