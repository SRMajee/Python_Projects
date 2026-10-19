//! Distributed Task Worker - Complete Solution (Rust)
//! Multi-threaded task execution with result backend.
//! Uses channels for task dispatch, Arc<Mutex<HashMap>> for results.
//! Concurrency: Core design IS concurrent.

use std::collections::HashMap;
use std::sync::{Arc, Mutex, Condvar, mpsc};
use std::thread;
use std::time::{Duration, Instant};

#[derive(Debug, Clone, PartialEq)]
enum TaskState { Pending, Running, Success, Failure }

#[derive(Debug, Clone)]
struct TaskResult {
    task_id: String,
    state: TaskState,
    result: i64,
    error: String,
}

type TaskFn = Box<dyn Fn(Vec<i64>) -> i64 + Send + Sync>;

struct TaskRegistry {
    tasks: HashMap<String, Arc<TaskFn>>,
}
impl TaskRegistry {
    fn new() -> Self { Self { tasks: HashMap::new() } }
    fn register(&mut self, name: &str, f: impl Fn(Vec<i64>) -> i64 + Send + Sync + 'static) {
        self.tasks.insert(name.into(), Arc::new(Box::new(f)));
    }
}

struct DistributedWorker {
    sender: mpsc::Sender<(String, String, Vec<i64>, u32)>,
    results: Arc<Mutex<HashMap<String, TaskResult>>>,
    workers: Vec<thread::JoinHandle<()>>,
    counter: Mutex<u32>,
}

impl DistributedWorker {
    fn new(num_workers: usize, registry: TaskRegistry) -> Self {
        let (tx, rx) = mpsc::channel::<(String, String, Vec<i64>, u32)>();
        let rx = Arc::new(Mutex::new(rx));
        let results = Arc::new(Mutex::new(HashMap::new()));
        let reg = Arc::new(registry.tasks);

        let mut workers = Vec::new();
        for _ in 0..num_workers {
            let rx_c = Arc::clone(&rx);
            let res_c = Arc::clone(&results);
            let reg_c = Arc::clone(&reg);
            workers.push(thread::spawn(move || {
                loop {
                    let item = {
                        let rx = rx_c.lock().unwrap();
                        rx.recv()
                    };
                    match item {
                        Ok((tid, name, args, max_retries)) => {
                            let func = reg_c.get(&name);
                            if func.is_none() {
                                res_c.lock().unwrap().insert(tid.clone(), TaskResult {
                                    task_id: tid, state: TaskState::Failure, result: 0,
                                    error: format!("Unknown task: {}", name),
                                });
                                continue;
                            }
                            let func = func.unwrap();
                            let mut last_err = String::new();
                            let mut success = false;
                            for attempt in 0..=max_retries {
                                res_c.lock().unwrap().insert(tid.clone(), TaskResult {
                                    task_id: tid.clone(), state: TaskState::Running, result: 0, error: String::new(),
                                });
                                match std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| func(args.clone()))) {
                                    Ok(val) => {
                                        res_c.lock().unwrap().insert(tid.clone(), TaskResult {
                                            task_id: tid.clone(), state: TaskState::Success, result: val, error: String::new(),
                                        });
                                        success = true;
                                        break;
                                    }
                                    Err(_) => {
                                        last_err = "Task panicked".into();
                                        if attempt < max_retries {
                                            thread::sleep(Duration::from_millis(100 * (1 << attempt)));
                                        }
                                    }
                                }
                            }
                            if !success {
                                res_c.lock().unwrap().insert(tid.clone(), TaskResult {
                                    task_id: tid, state: TaskState::Failure, result: 0, error: last_err,
                                });
                            }
                        }
                        Err(_) => break,
                    }
                }
            }));
        }

        Self { sender: tx, results, workers, counter: Mutex::new(0) }
    }

    fn submit(&self, name: &str, args: Vec<i64>, max_retries: u32) -> String {
        let mut c = self.counter.lock().unwrap();
        *c += 1;
        let tid = format!("task_{}", *c);
        self.results.lock().unwrap().insert(tid.clone(), TaskResult {
            task_id: tid.clone(), state: TaskState::Pending, result: 0, error: String::new(),
        });
        self.sender.send((tid.clone(), name.into(), args, max_retries)).unwrap();
        tid
    }

    fn get_result(&self, tid: &str, timeout_ms: u64) -> Option<TaskResult> {
        let deadline = Instant::now() + Duration::from_millis(timeout_ms);
        loop {
            {
                let r = self.results.lock().unwrap();
                if let Some(res) = r.get(tid) {
                    if res.state == TaskState::Success || res.state == TaskState::Failure {
                        return Some(res.clone());
                    }
                }
            }
            if Instant::now() >= deadline { return None; }
            thread::sleep(Duration::from_millis(20));
        }
    }

    fn shutdown(self) {
        drop(self.sender);
        for w in self.workers { w.join().unwrap(); }
    }
}

fn main() {
    let mut reg = TaskRegistry::new();
    reg.register("square", |args| args[0] * args[0]);
    reg.register("add", |args| args[0] + args[1]);
    reg.register("slow", |args| { thread::sleep(Duration::from_millis(50)); args[0] * 2 });

    let dw = DistributedWorker::new(4, reg);

    // Basic
    let tid = dw.submit("square", vec![7], 0);
    let r = dw.get_result(&tid, 5000).unwrap();
    assert_eq!(r.state, TaskState::Success);
    assert_eq!(r.result, 49);

    // Multiple
    let tids: Vec<_> = (0..10).map(|i| dw.submit("square", vec![i], 0)).collect();
    for (i, tid) in tids.iter().enumerate() {
        let r = dw.get_result(tid, 5000).unwrap();
        assert_eq!(r.result, (i as i64) * (i as i64));
    }

    // Unknown task
    let tid = dw.submit("nonexistent", vec![], 0);
    let r = dw.get_result(&tid, 5000).unwrap();
    assert_eq!(r.state, TaskState::Failure);

    // Concurrent slow
    let tids: Vec<_> = (0..8).map(|i| dw.submit("slow", vec![i], 0)).collect();
    for (i, tid) in tids.iter().enumerate() {
        let r = dw.get_result(tid, 10000).unwrap();
        assert_eq!(r.result, (i as i64) * 2);
    }

    dw.shutdown();
    println!("Complete Rust Distributed Worker tests passed!");
}
