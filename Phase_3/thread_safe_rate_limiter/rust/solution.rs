//! Thread-Safe Rate Limiter - Complete Solution (Rust)
//! Token Bucket + Sliding Window Log with per-key isolation.
//! Concurrency: Arc<Mutex<>> for thread-safe shared state.

use std::collections::{HashMap, VecDeque};
use std::sync::{Arc, Mutex};
use std::time::Instant;

trait RateLimiter {
    fn allow(&self, key: &str) -> bool;
}

struct TokenBucket {
    capacity: f64,
    refill_rate: f64,
    state: Mutex<HashMap<String, (f64, Instant)>>,
}

impl TokenBucket {
    fn new(capacity: u32, refill_rate: f64) -> Self {
        assert!(capacity > 0 && refill_rate > 0.0);
        Self { capacity: capacity as f64, refill_rate, state: Mutex::new(HashMap::new()) }
    }
}

impl RateLimiter for TokenBucket {
    fn allow(&self, key: &str) -> bool {
        let mut state = self.state.lock().unwrap();
        let now = Instant::now();
        let (mut tokens, last) = state
            .get(key)
            .cloned()
            .unwrap_or((self.capacity, now));
        let elapsed = now.duration_since(last).as_secs_f64();
        tokens = (tokens + elapsed * self.refill_rate).min(self.capacity);
        if tokens >= 1.0 {
            state.insert(key.to_string(), (tokens - 1.0, now));
            true
        } else {
            state.insert(key.to_string(), (tokens, now));
            false
        }
    }
}

struct SlidingWindowLog {
    max_requests: usize,
    window_secs: f64,
    state: Mutex<HashMap<String, VecDeque<Instant>>>,
}

impl SlidingWindowLog {
    fn new(max_requests: usize, window_secs: f64) -> Self {
        assert!(max_requests > 0 && window_secs > 0.0);
        Self { max_requests, window_secs, state: Mutex::new(HashMap::new()) }
    }
}

impl RateLimiter for SlidingWindowLog {
    fn allow(&self, key: &str) -> bool {
        let mut state = self.state.lock().unwrap();
        let now = Instant::now();
        let log = state.entry(key.to_string()).or_insert_with(VecDeque::new);
        let cutoff = std::time::Duration::from_secs_f64(self.window_secs);
        while let Some(&front) = log.front() {
            if now.duration_since(front) >= cutoff { log.pop_front(); } else { break; }
        }
        if log.len() < self.max_requests {
            log.push_back(now);
            true
        } else {
            false
        }
    }
}

fn main() {
    // Token Bucket tests
    let tb = TokenBucket::new(3, 1.0);
    assert!(tb.allow("d")); assert!(tb.allow("d")); assert!(tb.allow("d"));
    assert!(!tb.allow("d"));

    // Per-key isolation
    let tb2 = TokenBucket::new(1, 0.1);
    assert!(tb2.allow("a"));
    assert!(!tb2.allow("a"));
    assert!(tb2.allow("b"));

    // Sliding Window Log tests
    let sw = SlidingWindowLog::new(2, 1.0);
    assert!(sw.allow("d")); assert!(sw.allow("d")); assert!(!sw.allow("d"));

    // Thread safety
    let tb_arc = Arc::new(TokenBucket::new(100, 0.0));
    let allowed = Arc::new(Mutex::new(0u32));
    let mut handles = vec![];
    for _ in 0..10 {
        let tb_c = Arc::clone(&tb_arc);
        let cnt = Arc::clone(&allowed);
        handles.push(std::thread::spawn(move || {
            for _ in 0..20 {
                if tb_c.allow("d") {
                    *cnt.lock().unwrap() += 1;
                }
            }
        }));
    }
    for h in handles { h.join().unwrap(); }
    assert_eq!(*allowed.lock().unwrap(), 100);

    println!("Complete Rust Rate Limiter tests passed!");
}
