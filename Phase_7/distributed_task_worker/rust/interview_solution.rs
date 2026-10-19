/*
 * Distributed Task Worker - Interview Solution (Rust)
 *
 * 1. Primary Capabilities:
 *   - Worker threads + mpsc channel task dispatch
 *   - Arc<Mutex<HashMap>> result backend with polling get
 *   - Task registry, submit -> task_id
 *   - Panic-safe via catch_unwind
 *   - Concurrency: Core design IS concurrent
 *
 * 2. Error Handling:
 *   - Panics caught as Failure, unknown tasks -> Failure
 *
 * 3. Out Of Scope:
 *   - Real IPC/fork, Redis broker, task chaining, periodic tasks
 */
use std::collections::HashMap;
use std::sync::{Arc, Mutex, mpsc};
use std::thread;
use std::time::{Duration, Instant};

#[derive(Clone, PartialEq, Debug)] enum TS { Pending, Success, Failure }
#[derive(Clone)] struct Res { state: TS, val: i64, err: String }

type TFn = Arc<dyn Fn(Vec<i64>) -> i64 + Send + Sync>;

struct DW {
    tx: mpsc::Sender<(String, String, Vec<i64>)>,
    rs: Arc<Mutex<HashMap<String, Res>>>,
    ws: Vec<thread::JoinHandle<()>>,
    tc: Mutex<u32>,
}
impl DW {
    fn new(n: usize, reg: HashMap<String, TFn>) -> Self {
        let (tx, rx) = mpsc::channel(); let rx = Arc::new(Mutex::new(rx));
        let rs = Arc::new(Mutex::new(HashMap::new())); let reg = Arc::new(reg);
        let ws = (0..n).map(|_| { let r=Arc::clone(&rx); let rs=Arc::clone(&rs); let rg=Arc::clone(&reg);
            thread::spawn(move || loop { match r.lock().unwrap().recv() {
                Ok((tid, name, args)) => { if let Some(f) = rg.get(&name) {
                    match std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| f(args.clone()))) {
                        Ok(v) => { rs.lock().unwrap().insert(tid, Res{state:TS::Success,val:v,err:String::new()}); }
                        Err(_) => { rs.lock().unwrap().insert(tid, Res{state:TS::Failure,val:0,err:"panic".into()}); }
                    }
                } else { rs.lock().unwrap().insert(tid, Res{state:TS::Failure,val:0,err:"unknown".into()}); } }
                Err(_) => break } })
        }).collect();
        Self { tx, rs, ws, tc: Mutex::new(0) }
    }
    fn submit(&self, name: &str, args: Vec<i64>) -> String {
        let mut c = self.tc.lock().unwrap(); *c += 1; let tid = format!("t{}", *c);
        self.rs.lock().unwrap().insert(tid.clone(), Res{state:TS::Pending,val:0,err:String::new()});
        self.tx.send((tid.clone(), name.into(), args)).unwrap(); tid
    }
    fn result(&self, tid: &str, tms: u64) -> Option<Res> {
        let dl = Instant::now() + Duration::from_millis(tms);
        loop { { let r = self.rs.lock().unwrap(); if let Some(res) = r.get(tid) {
            if res.state != TS::Pending { return Some(res.clone()); } } }
            if Instant::now() >= dl { return None; } thread::sleep(Duration::from_millis(20)); }
    }
    fn shutdown(self) { drop(self.tx); for w in self.ws { w.join().unwrap(); } }
}

fn main() {
    let mut reg: HashMap<String, TFn> = HashMap::new();
    reg.insert("sq".into(), Arc::new(|a: Vec<i64>| a[0] * a[0]));
    let dw = DW::new(2, reg);
    let tid = dw.submit("sq", vec![7]);
    let r = dw.result(&tid, 5000).unwrap();
    assert_eq!(r.state, TS::Success); assert_eq!(r.val, 49);
    let tid2 = dw.submit("bad", vec![]);
    let r2 = dw.result(&tid2, 5000).unwrap();
    assert_eq!(r2.state, TS::Failure);
    dw.shutdown();
    println!("Interview Rust Distributed Worker passed!");
}
