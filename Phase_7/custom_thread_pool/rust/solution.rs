//! Custom Thread Pool Executor - Complete Solution (Rust)
//! Worker threads + shared task queue with Mutex + Condvar.
//! Future-like result retrieval via Arc<Mutex<Option<Result>>>.

use std::sync::{Arc, Mutex, Condvar, mpsc};
use std::thread;

type Task = Box<dyn FnOnce() + Send + 'static>;

struct ThreadPool {
    workers: Vec<thread::JoinHandle<()>>,
    sender: Option<mpsc::Sender<Task>>,
}

impl ThreadPool {
    fn new(size: usize) -> Self {
        assert!(size > 0);
        let (sender, receiver) = mpsc::channel::<Task>();
        let receiver = Arc::new(Mutex::new(receiver));
        let mut workers = Vec::with_capacity(size);

        for _ in 0..size {
            let rx = Arc::clone(&receiver);
            workers.push(thread::spawn(move || loop {
                let task = {
                    let rx = rx.lock().unwrap();
                    rx.recv()
                };
                match task {
                    Ok(task) => task(),
                    Err(_) => break,
                }
            }));
        }

        Self { workers, sender: Some(sender) }
    }

    fn submit<F, T>(&self, f: F) -> FutureResult<T>
    where
        F: FnOnce() -> T + Send + 'static,
        T: Send + 'static,
    {
        let result = Arc::new((Mutex::new(None::<Result<T, String>>), Condvar::new()));
        let result_clone = Arc::clone(&result);

        let task = Box::new(move || {
            let val = std::panic::catch_unwind(std::panic::AssertUnwindSafe(f));
            let (lock, cvar) = &*result_clone;
            let mut guard = lock.lock().unwrap();
            *guard = Some(match val {
                Ok(v) => Ok(v),
                Err(_) => Err("Task panicked".to_string()),
            });
            cvar.notify_all();
        });

        self.sender.as_ref().unwrap().send(task).unwrap();
        FutureResult { inner: result }
    }

    fn shutdown(mut self) {
        drop(self.sender.take());
        for w in self.workers.drain(..) {
            w.join().unwrap();
        }
    }
}

impl Drop for ThreadPool {
    fn drop(&mut self) {
        drop(self.sender.take());
        for w in self.workers.drain(..) {
            let _ = w.join();
        }
    }
}

struct FutureResult<T> {
    inner: Arc<(Mutex<Option<Result<T, String>>>, Condvar)>,
}

impl<T> FutureResult<T> {
    fn get(self) -> Result<T, String> {
        let (lock, cvar) = &*self.inner;
        let mut guard = lock.lock().unwrap();
        while guard.is_none() {
            guard = cvar.wait(guard).unwrap();
        }
        guard.take().unwrap()
    }
}

fn main() {
    // Basic submit
    {
        let pool = ThreadPool::new(4);
        let f = pool.submit(|| 7 * 7);
        assert_eq!(f.get().unwrap(), 49);
        pool.shutdown();
    }

    // Multiple tasks
    {
        let pool = ThreadPool::new(4);
        let futures: Vec<_> = (0..10).map(|i| pool.submit(move || i * i)).collect();
        let results: Vec<_> = futures.into_iter().map(|f| f.get().unwrap()).collect();
        assert_eq!(results, (0..10).map(|i| i * i).collect::<Vec<_>>());
        pool.shutdown();
    }

    // Panic handling
    {
        let pool = ThreadPool::new(2);
        let f = pool.submit(|| -> i32 { panic!("boom"); });
        assert!(f.get().is_err());
        pool.shutdown();
    }

    // Stress test
    {
        let pool = ThreadPool::new(8);
        let sum = Arc::new(Mutex::new(0i64));
        let futures: Vec<_> = (0..100).map(|i| {
            let s = Arc::clone(&sum);
            pool.submit(move || { *s.lock().unwrap() += i; i })
        }).collect();
        for f in futures { f.get().unwrap(); }
        assert_eq!(*sum.lock().unwrap(), 4950);
        pool.shutdown();
    }

    println!("Complete Rust Thread Pool tests passed!");
}
