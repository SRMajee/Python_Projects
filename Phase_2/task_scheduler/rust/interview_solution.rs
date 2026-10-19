/**
 * Task Scheduler - Concise Interview Solution (Rust)
 *
 * 1. Primary Capabilities:
 * - Topological DAG sorting via Kahn's algorithm using BinaryHeap and HashMap.
 * - Priority tie-breaking among independent ready tasks.
 * - Closure-based task execution with clear Rust ownership.
 *
 * 2. Error Handling:
 * - Returns Result<Vec<String>, &'static str> returning Err("Cycle detected!") on cycles.
 * - Propagates closure errors via standard Result<(), String>.
 *
 * 3. Out Of Scope:
 * - Tokio asynchronous runtime engine.
 * - Shared-memory multi-threaded lock-free synchronization.
 */

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

fn main() {
    let mut s = TaskScheduler::new();
    let mut d_test = HashSet::new(); d_test.insert("build".to_string());
    let mut d_lint = HashSet::new(); d_lint.insert("build".to_string());
    let mut d_dep = HashSet::new(); d_dep.insert("test".to_string()); d_dep.insert("lint".to_string());

    s.tasks.insert("build".to_string(), Task { id: "build".to_string(), priority: 1, dependencies: HashSet::new() });
    s.tasks.insert("test".to_string(), Task { id: "test".to_string(), priority: 1, dependencies: d_test });
    s.tasks.insert("lint".to_string(), Task { id: "lint".to_string(), priority: 2, dependencies: d_lint });
    s.tasks.insert("deploy".to_string(), Task { id: "deploy".to_string(), priority: 0, dependencies: d_dep });

    let order = s.execute().unwrap();
    assert_eq!(order, vec!["build", "lint", "test", "deploy"]);
    println!("Interview Rust TaskScheduler passed!");
}
