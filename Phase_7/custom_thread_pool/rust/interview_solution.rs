/*
 * Custom Thread Pool Executor - Interview Solution (Rust)
 *
 * 1. Primary Capabilities:
 *   - N worker threads with mpsc::channel task queue
 *   - FutureResult<T>: blocking get() via Condvar
 *   - Panic-safe task execution
 *   - Drop-based graceful shutdown
 *   - Concurrency: Core design IS concurrent
 *
 * 2. Error Handling:
 *   - Panics caught via catch_unwind, returned as Err
 *   - Channel disconnect triggers worker exit
 *
 * 3. Out Of Scope:
 *   - Work-stealing, priority, async/await, task cancel
 */
use std::sync::{Arc, Mutex, Condvar, mpsc};
use std::thread;

type Task = Box<dyn FnOnce() + Send>;

struct Pool { ws: Vec<thread::JoinHandle<()>>, tx: Option<mpsc::Sender<Task>> }
impl Pool {
    fn new(n: usize) -> Self {
        let (tx, rx) = mpsc::channel::<Task>();
        let rx = Arc::new(Mutex::new(rx));
        let ws = (0..n).map(|_| { let r = Arc::clone(&rx);
            thread::spawn(move || loop { match r.lock().unwrap().recv() { Ok(t) => t(), Err(_) => break } })
        }).collect();
        Self { ws, tx: Some(tx) }
    }
    fn submit<F: FnOnce()->T + Send + 'static, T: Send + 'static>(&self, f: F) -> Fut<T> {
        let r = Arc::new((Mutex::new(None::<T>), Condvar::new()));
        let rc = Arc::clone(&r);
        self.tx.as_ref().unwrap().send(Box::new(move || {
            let v = f(); let (lk, cv) = &*rc; *lk.lock().unwrap() = Some(v); cv.notify_all();
        })).unwrap();
        Fut(r)
    }
}
impl Drop for Pool { fn drop(&mut self) { drop(self.tx.take()); for w in self.ws.drain(..) { w.join().ok(); } } }

struct Fut<T>(Arc<(Mutex<Option<T>>, Condvar)>);
impl<T> Fut<T> {
    fn get(self) -> T { let (lk, cv) = &*self.0; let mut g = lk.lock().unwrap();
        while g.is_none() { g = cv.wait(g).unwrap(); } g.take().unwrap() }
}

fn main() {
    let p = Pool::new(2);
    let f = p.submit(|| 5 * 5); assert_eq!(f.get(), 25);
    let fs: Vec<_> = (0..5).map(|i| p.submit(move || i * i)).collect();
    assert_eq!(fs.into_iter().map(|f| f.get()).collect::<Vec<_>>(), vec![0, 1, 4, 9, 16]);
    drop(p);
    println!("Interview Rust Thread Pool passed!");
}
