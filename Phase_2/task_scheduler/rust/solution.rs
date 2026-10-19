/**
 * Task Scheduler - Complete Solution with Tests (Rust)
 * Includes boxed closures, dynamic TaskObserver trait, and unit test assertions.
 */

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
    let mut deps_test = HashSet::new(); deps_test.insert("build".to_string());
    let mut deps_lint = HashSet::new(); deps_lint.insert("build".to_string());
    let mut deps_deploy = HashSet::new(); deps_deploy.insert("test".to_string()); deps_deploy.insert("lint".to_string());

    scheduler.add_task(Task {
        id: "build".to_string(), priority: 1, dependencies: HashSet::new(),
        action: Box::new(|| Ok(())), status: TaskStatus::Pending,
    });
    scheduler.add_task(Task {
        id: "test".to_string(), priority: 1, dependencies: deps_test,
        action: Box::new(|| Ok(())), status: TaskStatus::Pending,
    });
    scheduler.add_task(Task {
        id: "lint".to_string(), priority: 2, dependencies: deps_lint,
        action: Box::new(|| Ok(())), status: TaskStatus::Pending,
    });
    scheduler.add_task(Task {
        id: "deploy".to_string(), priority: 0, dependencies: deps_deploy,
        action: Box::new(|| Ok(())), status: TaskStatus::Pending,
    });

    let order = scheduler.execute().unwrap();
    assert_eq!(order, vec!["build", "lint", "test", "deploy"]);
    println!("Complete Rust TaskScheduler tests passed!");
}
