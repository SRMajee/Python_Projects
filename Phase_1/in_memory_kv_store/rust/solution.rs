/**
 * In-Memory Key-Value Store - Complete Solution with Tests (Rust)
 */

use std::collections::HashMap;
use std::time::{Duration, Instant};

#[derive(Clone, Debug)]
struct Entry {
    value: String,
    expiry: Option<Instant>,
}

impl Entry {
    fn is_expired(&self) -> bool {
        if let Some(exp) = self.expiry { Instant::now() >= exp } else { false }
    }
}

pub struct InMemoryKVStore {
    store: HashMap<String, Entry>,
    tx_stack: Vec<HashMap<String, Option<Entry>>>,
}

impl InMemoryKVStore {
    pub fn new() -> Self {
        Self { store: HashMap::new(), tx_stack: Vec::new() }
    }

    pub fn set(&mut self, key: &str, value: &str, ttl_secs: Option<u64>) {
        let expiry = ttl_secs.map(|s| Instant::now() + Duration::from_secs(s));
        let entry = Entry { value: value.to_string(), expiry };

        if let Some(current_tx) = self.tx_stack.last_mut() {
            current_tx.insert(key.to_string(), Some(entry));
        } else {
            self.store.insert(key.to_string(), entry);
        }
    }

    pub fn get(&mut self, key: &str) -> Option<String> {
        for tx in self.tx_stack.iter().rev() {
            if let Some(opt_entry) = tx.get(key) {
                return match opt_entry {
                    Some(e) if !e.is_expired() => Some(e.value.clone()),
                    _ => None,
                };
            }
        }

        if let Some(entry) = self.store.get(key) {
            if entry.is_expired() {
                self.store.remove(key);
                None
            } else {
                Some(entry.value.clone())
            }
        } else {
            None
        }
    }

    pub fn delete(&mut self, key: &str) -> bool {
        if self.get(key).is_none() { return false; }
        if let Some(current_tx) = self.tx_stack.last_mut() {
            current_tx.insert(key.to_string(), None);
        } else {
            self.store.remove(key);
        }
        true
    }

    pub fn begin(&mut self) { self.tx_stack.push(HashMap::new()); }

    pub fn commit(&mut self) -> Result<(), &'static str> {
        let current_tx = self.tx_stack.pop().ok_or("No active transaction")?;
        if let Some(parent_tx) = self.tx_stack.last_mut() {
            for (k, v) in current_tx { parent_tx.insert(k, v); }
        } else {
            for (k, v) in current_tx {
                match v {
                    Some(entry) => { self.store.insert(k, entry); }
                    None => { self.store.remove(&k); }
                }
            }
        }
        Ok(())
    }

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

    kv.begin();
    kv.set("foo", "inner", None);
    assert_eq!(kv.get("foo").as_deref(), Some("inner"));
    assert!(kv.rollback().is_ok());

    assert_eq!(kv.get("foo").as_deref(), Some("updated"));
    assert!(kv.commit().is_ok());
    assert_eq!(kv.get("foo").as_deref(), Some("updated"));

    println!("Complete Rust InMemoryKVStore tests passed!");
}
