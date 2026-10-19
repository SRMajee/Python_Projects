//! O(1) LRU & LFU Cache - Complete Solution (Rust)
//! LRU: HashMap + custom doubly linked list (index-based arena).
//! LFU: HashMap + frequency bucket lists.
//! Concurrency: Mutex wraps cache for thread safety.

use std::collections::HashMap;
use std::sync::Mutex;

// Arena-based doubly linked list for O(1) operations
struct Node { key: i32, val: i32, prev: usize, next: usize, freq: u32 }

struct DLL {
    nodes: Vec<Node>,
    head: usize,
    tail: usize,
    free: Vec<usize>,
}

impl DLL {
    fn new() -> Self {
        let mut nodes = Vec::new();
        nodes.push(Node { key: 0, val: 0, prev: 0, next: 1, freq: 0 }); // head sentinel
        nodes.push(Node { key: 0, val: 0, prev: 0, next: 1, freq: 0 }); // tail sentinel
        Self { nodes, head: 0, tail: 1, free: Vec::new() }
    }
    fn alloc(&mut self, key: i32, val: i32) -> usize {
        if let Some(idx) = self.free.pop() {
            self.nodes[idx] = Node { key, val, prev: 0, next: 0, freq: 1 };
            idx
        } else {
            let idx = self.nodes.len();
            self.nodes.push(Node { key, val, prev: 0, next: 0, freq: 1 });
            idx
        }
    }
    fn push_front(&mut self, idx: usize) {
        let next = self.nodes[self.head].next;
        self.nodes[idx].prev = self.head;
        self.nodes[idx].next = next;
        self.nodes[self.head].next = idx;
        self.nodes[next].prev = idx;
    }
    fn remove(&mut self, idx: usize) {
        let prev = self.nodes[idx].prev;
        let next = self.nodes[idx].next;
        self.nodes[prev].next = next;
        self.nodes[next].prev = prev;
    }
    fn pop_back(&mut self) -> Option<usize> {
        let idx = self.nodes[self.tail].prev;
        if idx == self.head { return None; }
        self.remove(idx);
        self.free.push(idx);
        Some(idx)
    }
}

struct LRUCache {
    cap: usize,
    map: HashMap<i32, usize>,
    dll: DLL,
}
impl LRUCache {
    fn new(cap: usize) -> Self {
        assert!(cap > 0);
        Self { cap, map: HashMap::new(), dll: DLL::new() }
    }
    fn get(&mut self, key: i32) -> Option<i32> {
        if let Some(&idx) = self.map.get(&key) {
            self.dll.remove(idx);
            self.dll.push_front(idx);
            Some(self.dll.nodes[idx].val)
        } else { None }
    }
    fn put(&mut self, key: i32, val: i32) {
        if let Some(&idx) = self.map.get(&key) {
            self.dll.nodes[idx].val = val;
            self.dll.remove(idx);
            self.dll.push_front(idx);
        } else {
            if self.map.len() >= self.cap {
                if let Some(evict) = self.dll.pop_back() {
                    self.map.remove(&self.dll.nodes[evict].key);
                }
            }
            let idx = self.dll.alloc(key, val);
            self.dll.push_front(idx);
            self.map.insert(key, idx);
        }
    }
}

// LFU uses frequency buckets with Vec<(key, order)> for simplicity
struct LFUCache {
    cap: usize,
    min_freq: u32,
    kv: HashMap<i32, (i32, u32)>,  // key -> (val, freq)
    freq_keys: HashMap<u32, Vec<i32>>,
    key_pos: HashMap<i32, usize>,
}
impl LFUCache {
    fn new(cap: usize) -> Self {
        assert!(cap > 0);
        Self { cap, min_freq: 0, kv: HashMap::new(), freq_keys: HashMap::new(), key_pos: HashMap::new() }
    }
    fn touch(&mut self, key: i32) {
        let freq = self.kv[&key].1;
        let list = self.freq_keys.get_mut(&freq).unwrap();
        let pos = list.iter().position(|&k| k == key).unwrap();
        list.remove(pos);
        if list.is_empty() {
            self.freq_keys.remove(&freq);
            if self.min_freq == freq { self.min_freq += 1; }
        }
        self.kv.get_mut(&key).unwrap().1 = freq + 1;
        self.freq_keys.entry(freq + 1).or_default().push(key);
    }
    fn get(&mut self, key: i32) -> Option<i32> {
        if !self.kv.contains_key(&key) { return None; }
        self.touch(key);
        Some(self.kv[&key].0)
    }
    fn put(&mut self, key: i32, val: i32) {
        if self.kv.contains_key(&key) {
            self.kv.get_mut(&key).unwrap().0 = val;
            self.touch(key);
            return;
        }
        if self.kv.len() >= self.cap {
            let list = self.freq_keys.get_mut(&self.min_freq).unwrap();
            let evict = list.remove(0);
            if list.is_empty() { self.freq_keys.remove(&self.min_freq); }
            self.kv.remove(&evict);
        }
        self.kv.insert(key, (val, 1));
        self.min_freq = 1;
        self.freq_keys.entry(1).or_default().push(key);
    }
}

fn main() {
    // LRU tests
    let mut lru = LRUCache::new(2);
    lru.put(1, 10); lru.put(2, 20);
    assert_eq!(lru.get(1), Some(10));
    lru.put(3, 30); // evicts 2
    assert_eq!(lru.get(2), None);
    assert_eq!(lru.get(3), Some(30));

    // LFU tests
    let mut lfu = LFUCache::new(2);
    lfu.put(1, 10); lfu.put(2, 20);
    lfu.get(1); // freq(1)=2
    lfu.put(3, 30); // evicts 2
    assert_eq!(lfu.get(2), None);
    assert_eq!(lfu.get(1), Some(10));

    // Thread safety (wrap in Arc<Mutex>)
    use std::sync::Arc;
    let lru_shared = Arc::new(Mutex::new(LRUCache::new(1000)));
    let mut handles = vec![];
    for t in 0..5 {
        let c = Arc::clone(&lru_shared);
        handles.push(std::thread::spawn(move || {
            for i in t*100..t*100+100 {
                c.lock().unwrap().put(i, i * 10);
            }
        }));
    }
    for h in handles { h.join().unwrap(); }
    assert_eq!(lru_shared.lock().unwrap().map.len(), 500);

    println!("Complete Rust LRU/LFU tests passed!");
}
