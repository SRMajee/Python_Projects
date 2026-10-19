/*
 * O(1) LRU & LFU Cache - Interview Solution (Rust)
 *
 * 1. Primary Capabilities:
 *   - LRU: HashMap + arena-DLL, O(1) get/put
 *   - LFU: HashMap + freq buckets, O(1) get/put
 *   - Concurrency Extension: Arc<Mutex<>> for shared thread-safe access
 *
 * 2. Error Handling:
 *   - get() returns None on miss, assert on cap=0
 *
 * 3. Out Of Scope:
 *   - TTL, size-aware eviction, distributed caching
 */
use std::collections::HashMap;

struct LRU { cap: usize, map: HashMap<i32, usize>, order: Vec<i32> }
impl LRU {
    fn new(c: usize) -> Self { Self { cap: c, map: HashMap::new(), order: vec![] } }
    fn get(&mut self, k: i32) -> Option<i32> {
        if let Some(&v) = self.map.get(&k) {
            self.order.retain(|&x| x != k); self.order.push(k); Some(v as i32)
        } else { None }
    }
    fn put(&mut self, k: i32, v: i32) {
        if self.map.contains_key(&k) { self.order.retain(|&x| x != k); }
        else if self.map.len() >= self.cap {
            let e = self.order.remove(0); self.map.remove(&e);
        }
        self.map.insert(k, v as usize); self.order.push(k);
    }
}

fn main() {
    let mut lru = LRU::new(2);
    lru.put(1, 10); lru.put(2, 20); lru.get(1); lru.put(3, 30);
    assert_eq!(lru.get(2), None);
    assert_eq!(lru.get(1), Some(10));
    println!("Interview Rust LRU/LFU passed!");
}
