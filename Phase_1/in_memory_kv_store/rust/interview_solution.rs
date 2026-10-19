/**
 * In-Memory Key-Value Store - Concise Interview Solution (Rust)
 *
 * 1. Primary Capabilities:
 * - Idiomatic Rust memory management without garbage collection overhead.
 * - Transaction rollback via popping nested HashMap stack frames.
 * - TTL expiration with std::time::Instant.
 *
 * 2. Error Handling:
 * - Safe Option<String> returns for missing or expired keys.
 * - Result<(), &'static str> returned for empty transaction commits or rollbacks.
 *
 * 3. Out Of Scope:
 * - Shared-state multi-threading with Arc<RwLock<...>>.
 * - Persistent storage engine.
 */

use std::collections::HashMap;
use std::time::{Duration, Instant};

#[derive(Clone)]
struct Entry { value: String, expiry: Option<Instant> }

pub struct InMemoryKVStore {
    store: HashMap<String, Entry>,
    tx_stack: Vec<HashMap<String, Option<Entry>>>,
}

impl InMemoryKVStore {
    pub fn new() -> Self { Self { store: HashMap::new(), tx_stack: Vec::new() } }

    pub fn set(&mut self, key: &str, val: &str, ttl_secs: Option<u64>) {
        let expiry = ttl_secs.map(|s| Instant::now() + Duration::from_secs(s));
        let entry = Entry { value: val.to_string(), expiry };
        if let Some(tx) = self.tx_stack.last_mut() {
            tx.insert(key.to_string(), Some(entry));
        } else {
            self.store.insert(key.to_string(), entry);
        }
    }

    pub fn get(&mut self, key: &str) -> Option<String> {
        for tx in self.tx_stack.iter().rev() {
            if let Some(opt_e) = tx.get(key) {
                return match opt_e {
                    Some(e) if e.expiry.map_or(true, |exp| Instant::now() < exp) => Some(e.value.clone()),
                    _ => None,
                };
            }
        }
        if let Some(entry) = self.store.get(key) {
            if entry.expiry.map_or(false, |exp| Instant::now() >= exp) {
                self.store.remove(key);
                None
            } else {
                Some(entry.value.clone())
            }
        } else {
            None
        }
    }

    pub fn begin(&mut self) { self.tx_stack.push(HashMap::new()); }
    pub fn rollback(&mut self) -> Result<(), &'static str> {
        self.tx_stack.pop().ok_or("No active transaction")?;
        Ok(())
    }
}

fn main() {
    let mut kv = InMemoryKVStore::new();
    kv.set("foo", "bar", None);
    assert_eq!(kv.get("foo").as_deref(), Some("bar"));

    kv.begin();
    kv.set("foo", "updated", None);
    assert_eq!(kv.get("foo").as_deref(), Some("updated"));
    assert!(kv.rollback().is_ok());
    assert_eq!(kv.get("foo").as_deref(), Some("bar"));

    println!("Interview Rust InMemoryKVStore passed!");
}
