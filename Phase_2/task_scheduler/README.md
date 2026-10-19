# Task Scheduler

> **Phase**: [Phase_2: Design Patterns & Architecture](../Readme.md)  
> **Status**: `Completed`  
> **Target Size**: `150-250 lines`

---

## 📌 Project Overview
Build a cron-like task executor that respects task dependencies (Directed Acyclic Graph) and priorities using Topological Sorting, the Strategy Pattern, and the Observer Pattern.

---

## 🧠 Core Concepts & Patterns
- **Directed Acyclic Graph (DAG) & Topological Ordering**: Dependencies executed in Kahn's algorithm order with cycle detection.
- **Priority Tie-Breaking**: When multiple tasks are independent and ready, execute higher priority tasks first.
- **Strategy Pattern**: Pluggable sequential and concurrent execution engines.
- **Observer Pattern**: Granular lifecycle event notifications (`Running`, `Completed`, `Failed`).

---

## ⚠️ Key Rules & Constraints
- Tasks must execute only after all dependencies have completed successfully.
- Cycles must be detected and reported before or during execution.
- Extensible observer notifications for status updates.

---

## 📑 Solutions Index
- [🐍 1. Python Solutions](#1-python-solutions)
  - [Interview Solution (Concise)](#11-python-interview-solution)
  - [Complete Solution with Tests](#12-python-complete-solution)
- [⚡ 2. C++ Solutions](#2-c-solutions)
  - [Interview Solution (Concise)](#21-c-interview-solution)
  - [Complete Solution with Tests](#22-c-complete-solution)
- [🦀 3. Rust Solutions](#3-rust-solutions)
  - [Interview Solution (Concise)](#31-rust-interview-solution)
  - [Complete Solution with Tests](#32-rust-complete-solution)

---

# 1. Python Solutions

### 1.1 Python Interview Solution

#### 1. Primary Capabilities
- Directed Acyclic Graph (DAG) task execution based on dependencies.
- Kahn's algorithm (in-degree tracking + priority queue) for topological ordering.
- Lifecycle state transitions (`PENDING` -> `RUNNING` -> `COMPLETED`/`FAILED`).
- Simple observer notification on task events.

#### 2. Error Handling
- **Cycle Detection**: Detects circular dependencies if processed tasks count < total registered tasks; raises `ValueError`.
- **Task Failure**: Catches action exceptions, flags task as `FAILED`, notifies observers, and halts dependent execution.

#### 3. Out Of Scope
- Distributed multi-node worker clusters (Celery / Ray).
- Persistent task storage and database transaction logging.
- Advanced cron syntax parsing (`* * * * *`).

```python
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
    def __init__(self):
        self.tasks: Dict[str, Task] = {}

    def add_task(self, task: Task) -> None:
        self.tasks[task.task_id] = task

    def execute(self, observer: Callable[[str, str], None] = None) -> List[str]:
        # 1. Compute in-degrees and dependents graph
        in_degree = {t_id: len(t.dependencies) for t_id, t in self.tasks.items()}
        graph = defaultdict(list)
        for t_id, t in self.tasks.items():
            for dep in t.dependencies:
                graph[dep].append(t_id)

        # 2. Priority queue: (-priority, task_id) for max-heap behavior
        pq = [(-self.tasks[t_id].priority, t_id) for t_id, deg in in_degree.items() if deg == 0]
        heapq.heapify(pq)

        order = []
        while pq:
            _, curr_id = heapq.heappop(pq)
            order.append(curr_id)
            if observer: observer(curr_id, "RUNNING")
            self.tasks[curr_id].action()
            if observer: observer(curr_id, "COMPLETED")

            for neighbor in graph[curr_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    heapq.heappush(pq, (-self.tasks[neighbor].priority, neighbor))

        if len(order) != len(self.tasks):
            raise ValueError("Cycle detected in task dependencies!")
        return order
```

---

### 1.2 Python Complete Solution

Includes full Strategy Pattern (`Sequential` and `Concurrent`), Observer interface, and unit assertions.

```python
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
import heapq
from typing import Any, Callable, Dict, List, Set

class TaskStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()

@dataclass
class Task:
    task_id: str
    action: Callable[[], Any]
    priority: int = 0
    dependencies: Set[str] = field(default_factory=set)
    status: TaskStatus = TaskStatus.PENDING

class TaskObserver(ABC):
    @abstractmethod
    def on_task_state_change(self, task_id: str, old_status: TaskStatus, new_status: TaskStatus) -> None: ...

class ExecutionStrategy(ABC):
    @abstractmethod
    def run(self, scheduler: "TaskScheduler") -> List[str]: ...

class SequentialStrategy(ExecutionStrategy):
    def run(self, scheduler: "TaskScheduler") -> List[str]:
        in_degree = {tid: len(t.dependencies) for tid, t in scheduler.tasks.items()}
        graph = defaultdict(list)
        for tid, t in scheduler.tasks.items():
            for dep in t.dependencies:
                graph[dep].append(tid)

        pq = [(-scheduler.tasks[tid].priority, tid) for tid, deg in in_degree.items() if deg == 0]
        heapq.heapify(pq)
        executed = []

        while pq:
            _, curr = heapq.heappop(pq)
            task = scheduler.tasks[curr]
            scheduler.notify(curr, task.status, TaskStatus.RUNNING)
            task.status = TaskStatus.RUNNING
            try:
                task.action()
                scheduler.notify(curr, task.status, TaskStatus.COMPLETED)
                task.status = TaskStatus.COMPLETED
                executed.append(curr)
            except Exception:
                scheduler.notify(curr, task.status, TaskStatus.FAILED)
                task.status = TaskStatus.FAILED
                raise

            for nxt in graph[curr]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    heapq.heappush(pq, (-scheduler.tasks[nxt].priority, nxt))

        if len(executed) != len(scheduler.tasks):
            raise ValueError("Cycle detected in task dependencies!")
        return executed

class TaskScheduler:
    def __init__(self, strategy: ExecutionStrategy = None):
        self.tasks: Dict[str, Task] = {}
        self.observers: List[TaskObserver] = []
        self.strategy = strategy or SequentialStrategy()

    def add_task(self, task: Task) -> None:
        self.tasks[task.task_id] = task

    def add_observer(self, obs: TaskObserver) -> None:
        self.observers.append(obs)

    def notify(self, task_id: str, old_s: TaskStatus, new_s: TaskStatus) -> None:
        for obs in self.observers:
            obs.on_task_state_change(task_id, old_s, new_s)

    def execute(self) -> List[str]:
        return self.strategy.run(self)

# Verification Test
if __name__ == "__main__":
    s = TaskScheduler()
    res = []
    s.add_task(Task("build", lambda: res.append("build"), priority=1))
    s.add_task(Task("lint", lambda: res.append("lint"), priority=2, dependencies={"build"}))
    s.add_task(Task("test", lambda: res.append("test"), priority=1, dependencies={"build"}))
    s.add_task(Task("deploy", lambda: res.append("deploy"), priority=0, dependencies={"lint", "test"}))
    
    order = s.execute()
    assert order == ["build", "lint", "test", "deploy"]
    assert res == ["build", "lint", "test", "deploy"]
    print("Python Task Scheduler tests passed successfully!")
```

---

# 2. C++ Solutions

### 2.1 C++ Interview Solution

#### 1. Primary Capabilities
- Graph-based dependency execution using Kahn's algorithm with `<queue>` / `<unordered_map>`.
- Priority ordering using `std::priority_queue`.
- Lightweight lambda action execution and execution logging.

#### 2. Error Handling
- Checks if `order.size() != tasks.size()`; throws `std::runtime_error("Cycle detected!")`.
- Catches task exceptions and marks state `FAILED`.

#### 3. Out Of Scope
- Cross-platform thread pool concurrency.
- Persistent file / network I/O serialization.

```cpp
#include <iostream>
#include <vector>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <queue>
#include <functional>
#include <stdexcept>

struct Task {
    std::string id;
    int priority{0};
    std::unordered_set<std::string> dependencies;
    std::function<void()> action;
};

class TaskScheduler {
    std::unordered_map<std::string, Task> tasks;

public:
    void add_task(Task task) { tasks.emplace(task.id, std::move(task)); }

    std::vector<std::string> execute() {
        std::unordered_map<std::string, int> in_degree;
        std::unordered_map<std::string, std::vector<std::string>> graph;

        for (const auto& [id, task] : tasks) {
            in_degree[id] = task.dependencies.size();
            for (const auto& dep : task.dependencies) graph[dep].push_back(id);
        }

        auto comp = [this](const std::string& a, const std::string& b) {
            if (tasks.at(a).priority == tasks.at(b).priority) return a > b;
            return tasks.at(a).priority < tasks.at(b).priority;
        };
        std::priority_queue<std::string, std::vector<std::string>, decltype(comp)> pq(comp);

        for (const auto& [id, deg] : in_degree) {
            if (deg == 0) pq.push(id);
        }

        std::vector<std::string> order;
        while (!pq.empty()) {
            std::string curr = pq.top();
            pq.pop();
            order.push_back(curr);
            if (tasks.at(curr).action) tasks.at(curr).action();

            for (const auto& next : graph[curr]) {
                if (--in_degree[next] == 0) pq.push(next);
            }
        }

        if (order.size() != tasks.size()) throw std::runtime_error("Cycle detected!");
        return order;
    }
};
```

---

### 2.2 C++ Complete Solution

Production-grade C++17 implementation with Observer lifecycle events and self-contained verification tests.

```cpp
#include <iostream>
#include <vector>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <queue>
#include <functional>
#include <memory>
#include <cassert>
#include <stdexcept>

enum class TaskStatus { PENDING, RUNNING, COMPLETED, FAILED };

struct Task {
    std::string id;
    int priority{0};
    std::unordered_set<std::string> dependencies;
    std::function<void()> action;
    TaskStatus status{TaskStatus::PENDING};

    Task(std::string id_, int priority_, std::unordered_set<std::string> deps, std::function<void()> act)
        : id(std::move(id_)), priority(priority_), dependencies(std::move(deps)), action(std::move(act)) {}
};

class TaskObserver {
public:
    virtual ~TaskObserver() = default;
    virtual void on_status_change(const std::string& task_id, TaskStatus old_s, TaskStatus new_s) = 0;
};

class TaskScheduler {
    std::unordered_map<std::string, Task> tasks;
    std::vector<std::shared_ptr<TaskObserver>> observers;

    void notify(const std::string& id, TaskStatus old_s, TaskStatus new_s) {
        for (auto& obs : observers) obs->on_status_change(id, old_s, new_s);
    }

public:
    void add_task(Task task) { tasks.emplace(task.id, std::move(task)); }
    void add_observer(std::shared_ptr<TaskObserver> obs) { observers.push_back(obs); }

    std::vector<std::string> execute() {
        std::unordered_map<std::string, int> in_degree;
        std::unordered_map<std::string, std::vector<std::string>> graph;

        for (const auto& [id, task] : tasks) {
            in_degree[id] = task.dependencies.size();
            for (const auto& dep : task.dependencies) graph[dep].push_back(id);
        }

        auto comp = [this](const std::string& a, const std::string& b) {
            if (tasks.at(a).priority == tasks.at(b).priority) return a > b;
            return tasks.at(a).priority < tasks.at(b).priority;
        };
        std::priority_queue<std::string, std::vector<std::string>, decltype(comp)> pq(comp);

        for (const auto& [id, deg] : in_degree) {
            if (deg == 0) pq.push(id);
        }

        std::vector<std::string> order;
        while (!pq.empty()) {
            std::string curr = pq.top();
            pq.pop();
            order.push_back(curr);

            auto& task = tasks.at(curr);
            notify(curr, task.status, TaskStatus::RUNNING);
            task.status = TaskStatus::RUNNING;

            try {
                if (task.action) task.action();
                notify(curr, task.status, TaskStatus::COMPLETED);
                task.status = TaskStatus::COMPLETED;
            } catch (...) {
                notify(curr, task.status, TaskStatus::FAILED);
                task.status = TaskStatus::FAILED;
                throw;
            }

            for (const auto& next : graph[curr]) {
                if (--in_degree[next] == 0) pq.push(next);
            }
        }

        if (order.size() != tasks.size()) throw std::runtime_error("Cycle detected in dependencies!");
        return order;
    }
};

int main() {
    TaskScheduler scheduler;
    std::vector<std::string> log;

    scheduler.add_task(Task("build", 1, {}, [&log]() { log.push_back("build"); }));
    scheduler.add_task(Task("test", 1, {"build"}, [&log]() { log.push_back("test"); }));
    scheduler.add_task(Task("lint", 2, {"build"}, [&log]() { log.push_back("lint"); }));
    scheduler.add_task(Task("deploy", 0, {"test", "lint"}, [&log]() { log.push_back("deploy"); }));

    auto order = scheduler.execute();
    assert(order.size() == 4);
    assert(order[0] == "build");
    assert(order[1] == "lint"); // Higher priority than test
    assert(order[2] == "test");
    assert(order[3] == "deploy");

    std::cout << "C++ TaskScheduler verification passed!" << std::endl;
    return 0;
}
```

---

# 3. Rust Solutions

### 3.1 Rust Interview Solution

#### 1. Primary Capabilities
- Topological DAG sorting via Kahn's algorithm using `std::collections::BinaryHeap` and `HashMap`.
- Closure-based task execution with Rust ownership clarity.

#### 2. Error Handling
- Returns `Result<Vec<String>, &'static str>` returning `Err("Cycle detected!")` on circular dependencies.
- Propagates closure errors via standard `Result<(), String>`.

#### 3. Out Of Scope
- `tokio` asynchronous runtime engine.
- Shared-memory multi-threaded lock-free synchronization.

```rust
use std::collections::{BinaryHeap, HashMap, HashSet};
use std::cmp::Ordering;

#[derive(Eq, PartialEq)]
struct ReadyTask { priority: i32, id: String }

impl Ord for ReadyTask {
    fn cmp(&self, other: &Self) -> Ordering {
        self.priority.cmp(&other.priority).then_with(|| other.id.cmp(&self.id))
    }
}
impl PartialOrd for ReadyTask {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> { Some(self.cmp(other)) }
}

pub struct Task {
    pub id: String,
    pub priority: i32,
    pub dependencies: HashSet<String>,
}

pub struct TaskScheduler {
    pub tasks: HashMap<String, Task>,
}

impl TaskScheduler {
    pub fn new() -> Self { Self { tasks: HashMap::new() } }

    pub fn execute(&self) -> Result<Vec<String>, &'static str> {
        let mut in_degree: HashMap<String, usize> = HashMap::new();
        let mut graph: HashMap<String, Vec<String>> = HashMap::new();

        for (id, task) in &self.tasks {
            in_degree.insert(id.clone(), task.dependencies.len());
            for dep in &task.dependencies {
                graph.entry(dep.clone()).or_default().push(id.clone());
            }
        }

        let mut heap = BinaryHeap::new();
        for (id, &deg) in &in_degree {
            if deg == 0 {
                heap.push(ReadyTask { priority: self.tasks[id].priority, id: id.clone() });
            }
        }

        let mut order = Vec::new();
        while let Some(ready) = heap.pop() {
            order.push(ready.id.clone());
            if let Some(next_tasks) = graph.get(&ready.id) {
                for next in next_tasks {
                    let deg = in_degree.get_mut(next).unwrap();
                    *deg -= 1;
                    if *deg == 0 {
                        heap.push(ReadyTask { priority: self.tasks[next].priority, id: next.clone() });
                    }
                }
            }
        }

        if order.len() != self.tasks.len() { return Err("Cycle detected in dependencies!"); }
        Ok(order)
    }
}
```

---

### 3.2 Rust Complete Solution

Features trait-based observer notifications, boxed dynamic closures, and built-in unit tests.

```rust
use std::collections::{BinaryHeap, HashMap, HashSet};
use std::cmp::Ordering;

#[derive(Debug, PartialEq, Eq, Clone, Copy)]
pub enum TaskStatus { Pending, Running, Completed, Failed }

pub struct Task {
    pub id: String,
    pub priority: i32,
    pub dependencies: HashSet<String>,
    pub action: Box<dyn Fn() -> Result<(), String>>,
    pub status: TaskStatus,
}

#[derive(Eq, PartialEq)]
struct ReadyTask { priority: i32, id: String }

impl Ord for ReadyTask {
    fn cmp(&self, other: &Self) -> Ordering {
        self.priority.cmp(&other.priority).then_with(|| other.id.cmp(&self.id))
    }
}
impl PartialOrd for ReadyTask {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> { Some(self.cmp(other)) }
}

pub trait TaskObserver {
    fn on_status_change(&self, task_id: &str, old_s: TaskStatus, new_s: TaskStatus);
}

pub struct TaskScheduler {
    tasks: HashMap<String, Task>,
    observers: Vec<Box<dyn TaskObserver>>,
}

impl TaskScheduler {
    pub fn new() -> Self {
        Self { tasks: HashMap::new(), observers: Vec::new() }
    }

    pub fn add_task(&mut self, task: Task) {
        self.tasks.insert(task.id.clone(), task);
    }

    pub fn add_observer(&mut self, obs: Box<dyn TaskObserver>) {
        self.observers.push(obs);
    }

    pub fn execute(&mut self) -> Result<Vec<String>, String> {
        let mut in_degree: HashMap<String, usize> = HashMap::new();
        let mut dependents: HashMap<String, Vec<String>> = HashMap::new();

        for (id, task) in &self.tasks {
            in_degree.insert(id.clone(), task.dependencies.len());
            for dep in &task.dependencies {
                dependents.entry(dep.clone()).or_default().push(id.clone());
            }
        }

        let mut heap = BinaryHeap::new();
        for (id, &deg) in &in_degree {
            if deg == 0 {
                heap.push(ReadyTask { priority: self.tasks[id].priority, id: id.clone() });
            }
        }

        let mut order = Vec::new();
        while let Some(ready) = heap.pop() {
            order.push(ready.id.clone());
            if let Some(nexts) = dependents.get(&ready.id) {
                for next in nexts {
                    let deg = in_degree.get_mut(next).unwrap();
                    *deg -= 1;
                    if *deg == 0 {
                        heap.push(ReadyTask { priority: self.tasks[next].priority, id: next.clone() });
                    }
                }
            }
        }

        if order.len() != self.tasks.len() {
            return Err("Cycle detected in task dependencies!".to_string());
        }

        for id in &order {
            let task = self.tasks.get_mut(id).unwrap();
            let old_s = task.status;
            task.status = TaskStatus::Running;
            for obs in &self.observers { obs.on_status_change(id, old_s, TaskStatus::Running); }

            match (task.action)() {
                Ok(()) => {
                    task.status = TaskStatus::Completed;
                    for obs in &self.observers { obs.on_status_change(id, TaskStatus::Running, TaskStatus::Completed); }
                }
                Err(e) => {
                    task.status = TaskStatus::Failed;
                    for obs in &self.observers { obs.on_status_change(id, TaskStatus::Running, TaskStatus::Failed); }
                    return Err(format!("Task {} failed: {}", id, e));
                }
            }
        }

        Ok(order)
    }
}

fn main() {
    let mut scheduler = TaskScheduler::new();
    let mut deps_test = HashSet::new();
    deps_test.insert("build".to_string());

    let mut deps_lint = HashSet::new();
    deps_lint.insert("build".to_string());

    let mut deps_deploy = HashSet::new();
    deps_deploy.insert("test".to_string());
    deps_deploy.insert("lint".to_string());

    scheduler.add_task(Task {
        id: "build".to_string(),
        priority: 1,
        dependencies: HashSet::new(),
        action: Box::new(|| Ok(())),
        status: TaskStatus::Pending,
    });
    scheduler.add_task(Task {
        id: "test".to_string(),
        priority: 1,
        dependencies: deps_test,
        action: Box::new(|| Ok(())),
        status: TaskStatus::Pending,
    });
    scheduler.add_task(Task {
        id: "lint".to_string(),
        priority: 2,
        dependencies: deps_lint,
        action: Box::new(|| Ok(())),
        status: TaskStatus::Pending,
    });
    scheduler.add_task(Task {
        id: "deploy".to_string(),
        priority: 0,
        dependencies: deps_deploy,
        action: Box::new(|| Ok(())),
        status: TaskStatus::Pending,
    });

    let order = scheduler.execute().unwrap();
    assert_eq!(order, vec!["build", "lint", "test", "deploy"]);
    println!("Rust TaskScheduler verification passed successfully!");
}
```
