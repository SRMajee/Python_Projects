//! Consistent Hashing Ring - Complete Solution (Rust)
//! BTreeMap-based ring with virtual nodes and FNV-like hashing.
//! Concurrency: Mutex wraps the ring for thread-safe operations.

use std::collections::{BTreeMap, HashSet};
use std::sync::Mutex;

struct ConsistentHashRing {
    num_virtual: usize,
    ring: Mutex<BTreeMap<u64, String>>,
    nodes: Mutex<HashSet<String>>,
}

impl ConsistentHashRing {
    fn new(vn: usize) -> Self {
        Self { num_virtual: vn, ring: Mutex::new(BTreeMap::new()), nodes: Mutex::new(HashSet::new()) }
    }

    fn hash_fn(key: &str) -> u64 {
        let mut h: u64 = 14695981039346656037;
        for b in key.bytes() { h ^= b as u64; h = h.wrapping_mul(1099511628211); }
        h
    }

    fn add_node(&self, node: &str) {
        let mut ring = self.ring.lock().unwrap();
        let mut nodes = self.nodes.lock().unwrap();
        assert!(!nodes.contains(node), "Node already exists");
        nodes.insert(node.to_string());
        for i in 0..self.num_virtual {
            let vkey = format!("{}#v{}", node, i);
            ring.insert(Self::hash_fn(&vkey), node.to_string());
        }
    }

    fn remove_node(&self, node: &str) {
        let mut ring = self.ring.lock().unwrap();
        let mut nodes = self.nodes.lock().unwrap();
        assert!(nodes.remove(node), "Node not found");
        for i in 0..self.num_virtual {
            let vkey = format!("{}#v{}", node, i);
            ring.remove(&Self::hash_fn(&vkey));
        }
    }

    fn get_node(&self, key: &str) -> Option<String> {
        let ring = self.ring.lock().unwrap();
        if ring.is_empty() { return None; }
        let h = Self::hash_fn(key);
        let node = ring.range(h..).next().or_else(|| ring.iter().next());
        node.map(|(_, v)| v.clone())
    }

    fn get_nodes(&self) -> HashSet<String> { self.nodes.lock().unwrap().clone() }
}

fn main() {
    let ring = ConsistentHashRing::new(100);
    ring.add_node("s1"); ring.add_node("s2"); ring.add_node("s3");

    // Basic
    let n = ring.get_node("my_key");
    assert!(n.is_some());

    // Consistency
    assert_eq!(ring.get_node("key_a"), ring.get_node("key_a"));

    // Minimal redistribution
    let keys: Vec<String> = (0..1000).map(|i| format!("key_{}", i)).collect();
    let before: Vec<_> = keys.iter().map(|k| ring.get_node(k).unwrap()).collect();
    ring.add_node("s4");
    let unchanged = keys.iter().zip(before.iter())
        .filter(|(k, b)| ring.get_node(k).as_ref() == Some(b)).count();
    assert!(unchanged > 500);

    // Remove
    ring.remove_node("s1"); ring.remove_node("s2"); ring.remove_node("s3");
    for i in 0..100 { assert_eq!(ring.get_node(&format!("k{}", i)).unwrap(), "s4"); }

    // Empty
    ring.remove_node("s4");
    assert!(ring.get_node("anything").is_none());

    // Thread safety
    use std::sync::Arc;
    let r2 = Arc::new(ConsistentHashRing::new(50));
    let mut handles = vec![];
    for g in 0..5 {
        let rc = Arc::clone(&r2);
        handles.push(std::thread::spawn(move || {
            for i in g*10..g*10+10 { rc.add_node(&format!("n{}", i)); }
        }));
    }
    for h in handles { h.join().unwrap(); }
    assert_eq!(r2.get_nodes().len(), 50);

    println!("Complete Rust Consistent Hash tests passed!");
}
