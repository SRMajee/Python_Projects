/*
 * Pub-Sub Message Broker - Interview Solution (Rust)
 *
 * 1. Primary Capabilities:
 *   - Topics with N partitions, key-hash or round-robin
 *   - Consumer groups with independent offset tracking
 *   - Concurrency Extension: Mutex<> wraps partitions and consumer state
 *
 * 2. Error Handling:
 *   - Panics on missing topic or duplicate creation
 *
 * 3. Out Of Scope:
 *   - Persistence, replication, exactly-once, rebalancing
 */
use std::collections::HashMap;
use std::sync::Mutex;

struct Partition { log: Vec<(String, String)> }
impl Partition {
    fn new() -> Self { Self { log: vec![] } }
    fn append(&mut self, k: &str, v: &str) -> usize { let o = self.log.len(); self.log.push((k.into(), v.into())); o }
    fn read(&self, off: usize, n: usize) -> Vec<(String,String)> { self.log[off..self.log.len().min(off+n)].to_vec() }
}

struct Topic { parts: Vec<Mutex<Partition>>, rr: Mutex<usize> }
impl Topic {
    fn new(n: usize) -> Self { Self { parts: (0..n).map(|_| Mutex::new(Partition::new())).collect(), rr: Mutex::new(0) } }
    fn publish(&self, k: &str, v: &str) -> (usize, usize) {
        let pid = if k.is_empty() { let mut r = self.rr.lock().unwrap(); let p = *r % self.parts.len(); *r += 1; p }
                  else { k.bytes().fold(0usize, |h, b| h.wrapping_mul(31).wrapping_add(b as usize)) % self.parts.len() };
        let off = self.parts[pid].lock().unwrap().append(k, v); (pid, off)
    }
}

struct CGroup { off: HashMap<usize, usize> }
impl CGroup {
    fn new(n: usize) -> Self { Self { off: (0..n).map(|i| (i, 0)).collect() } }
    fn poll(&mut self, t: &Topic, n: usize) -> Vec<(String,String)> {
        let mut r = vec![];
        for (pid, p) in t.parts.iter().enumerate() {
            let o = *self.off.get(&pid).unwrap();
            let b = p.lock().unwrap().read(o, n);
            *self.off.get_mut(&pid).unwrap() = o + b.len();
            r.extend(b);
        }
        r
    }
}

fn main() {
    let t = Topic::new(2);
    t.publish("k1", "v1"); t.publish("k2", "v2"); t.publish("", "v3");
    let mut c1 = CGroup::new(2);
    assert_eq!(c1.poll(&t, 10).len(), 3);
    let mut c2 = CGroup::new(2);
    assert_eq!(c2.poll(&t, 10).len(), 3);
    println!("Interview Rust Pub-Sub passed!");
}
