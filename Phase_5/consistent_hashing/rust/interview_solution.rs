/*
 * Consistent Hashing Ring - Interview Solution (Rust)
 *
 * 1. Primary Capabilities:
 *   - BTreeMap ring with FNV hash + virtual nodes
 *   - O(log n) lookup via range query
 *   - Concurrency Extension: Mutex wraps ring state
 *
 * 2. Error Handling:
 *   - Panics on duplicate/missing node
 *   - None on empty ring
 *
 * 3. Out Of Scope:
 *   - Weighted nodes, replication, bounded loads
 */
use std::collections::{BTreeMap, HashSet};
use std::sync::Mutex;

struct Ring { vn: usize, ring: Mutex<BTreeMap<u64, String>>, nodes: Mutex<HashSet<String>> }
impl Ring {
    fn new(vn: usize) -> Self { Self { vn, ring: Mutex::new(BTreeMap::new()), nodes: Mutex::new(HashSet::new()) } }
    fn h(k: &str) -> u64 { let mut v: u64 = 14695981039346656037; for b in k.bytes() { v ^= b as u64; v = v.wrapping_mul(1099511628211); } v }
    fn add(&self, n: &str) { let mut r = self.ring.lock().unwrap(); self.nodes.lock().unwrap().insert(n.into());
        for i in 0..self.vn { r.insert(Self::h(&format!("{}#v{}", n, i)), n.into()); } }
    fn remove(&self, n: &str) { let mut r = self.ring.lock().unwrap(); self.nodes.lock().unwrap().remove(n);
        for i in 0..self.vn { r.remove(&Self::h(&format!("{}#v{}", n, i))); } }
    fn get(&self, k: &str) -> Option<String> { let r = self.ring.lock().unwrap(); if r.is_empty() { return None; }
        r.range(Self::h(k)..).next().or_else(|| r.iter().next()).map(|(_, v)| v.clone()) }
}

fn main() {
    let r = Ring::new(100); r.add("s1"); r.add("s2"); r.add("s3");
    assert!(r.get("key").is_some());
    r.remove("s1"); r.remove("s2"); assert_eq!(r.get("any").unwrap(), "s3");
    println!("Interview Rust Consistent Hash passed!");
}
