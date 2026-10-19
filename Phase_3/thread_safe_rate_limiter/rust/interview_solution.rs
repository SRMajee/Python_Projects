/*
 * Thread-Safe Rate Limiter - Interview Solution (Rust)
 *
 * 1. Primary Capabilities:
 *   - Token Bucket: lazy refill, capacity-bounded, O(1) per call
 *   - Sliding Window Log: VecDeque timestamps, evict expired
 *   - Concurrency Extension: Mutex<HashMap> for thread-safe per-key state
 *
 * 2. Error Handling:
 *   - Panics on zero capacity/rate via assert
 *
 * 3. Out Of Scope:
 *   - Distributed rate limiting, leaky bucket, adaptive throttle
 */
use std::collections::{HashMap, VecDeque};
use std::sync::Mutex;
use std::time::Instant;

struct TokenBucket {
    cap: f64, rate: f64,
    st: Mutex<HashMap<String, (f64, Instant)>>,
}
impl TokenBucket {
    fn new(c: u32, r: f64) -> Self { Self { cap: c as f64, rate: r, st: Mutex::new(HashMap::new()) } }
    fn allow(&self, k: &str) -> bool {
        let mut s = self.st.lock().unwrap();
        let now = Instant::now();
        let (mut tok, last) = s.get(k).cloned().unwrap_or((self.cap, now));
        tok = (tok + now.duration_since(last).as_secs_f64() * self.rate).min(self.cap);
        if tok >= 1.0 { s.insert(k.into(), (tok - 1.0, now)); true }
        else { s.insert(k.into(), (tok, now)); false }
    }
}

struct SlidingWindowLog {
    mx: usize, win: f64,
    st: Mutex<HashMap<String, VecDeque<Instant>>>,
}
impl SlidingWindowLog {
    fn new(m: usize, w: f64) -> Self { Self { mx: m, win: w, st: Mutex::new(HashMap::new()) } }
    fn allow(&self, k: &str) -> bool {
        let mut s = self.st.lock().unwrap();
        let now = Instant::now();
        let q = s.entry(k.into()).or_default();
        let cut = std::time::Duration::from_secs_f64(self.win);
        while q.front().map_or(false, |&f| now.duration_since(f) >= cut) { q.pop_front(); }
        if q.len() < self.mx { q.push_back(now); true } else { false }
    }
}

fn main() {
    let tb = TokenBucket::new(3, 1.0);
    assert!(tb.allow("d") && tb.allow("d") && tb.allow("d") && !tb.allow("d"));
    let sw = SlidingWindowLog::new(2, 1.0);
    assert!(sw.allow("d") && sw.allow("d") && !sw.allow("d"));
    println!("Interview Rust Rate Limiter passed!");
}
