# In-Memory Key-Value Store

> **Phase**: [Phase_1: Object-Oriented Foundations](../Readme.md)  
> **Status**: `Completed`  
> **Target Size**: `80-120 lines`

---

## 📌 Project Overview
Build a high-performance in-memory key-value store (Redis-lite) with TTL (Time-To-Live) expiration and nested ACID-style transactions (`BEGIN`, `COMMIT`, `ROLLBACK`).

---

## 🧠 Core Concepts & Patterns
- **Abstract Base Class / Interfaces**: Formal contract defining CRUD operations and transactional boundaries.
- **Data Encapsulation**: Entry metadata with TTL timestamps and expiration checks.
- **Nested Transaction Stack**: Stack of diff frames enabling isolated staging and rollbacks.

---

## ⚠️ Key Rules & Constraints
- Zero external dependencies; use only language standard libraries.
- Strict type safety and clear error reporting.
- Nested transaction frames must isolate uncommitted mutations from the base store.

---

## 📑 Solutions Index
- [🐍 1. Python Solutions](#1-python-solutions)
  - [Interview Solution (Concise)](#11-python-interview-solution)
  - [Complete Solution with Tests](#12-python-complete-solution)
- [⚡ 2. C++ Solutions](#2-c-solutions)
  - [Interview Solution (Concise)](#21-c-interview-solution)
  - [Complete Solution with Tests](#22-c-complete-solution)
- [🦀 3. Rust Solutions](#3-rust-solutions)
  - [Interview Solution (Concise)](#31-rust-interview-solution)
  - [Complete Solution with Tests](#32-rust-complete-solution)

---

# 1. Python Solutions

### 1.1 Python Interview Solution

#### 1. Primary Capabilities
- `set(key, val, ttl=None)`: Insert or update key with optional expiration.
- `get(key)`: Retrieve value; inspects active transaction frames top-down, then base store.
- `delete(key)`: Tombstone key in current transaction or purge from base store.
- `begin()`, `commit()`, `rollback()`: Multi-level transaction stack.

#### 2. Error Handling
- Calling `commit()` or `rollback()` without active transactions raises `RuntimeError`.
- Accessing expired keys triggers lazy eviction and returns `None`.

#### 3. Out Of Scope
- AOF / RDB disk persistence.
- Redis Serialization Protocol (RESP) networking socket server.
- LRU/LFU memory eviction when memory capacity is reached.

```python
import time
from typing import Any, Dict, List, Optional

class InMemoryKVStore:
    def __init__(self):
        self.store: Dict[str, tuple] = {}  # key -> (value, expiry_timestamp)
        self.tx_stack: List[Dict[str, Optional[tuple]]] = []

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        expiry = time.time() + ttl if ttl else None
        entry = (value, expiry)
        if self.tx_stack:
            self.tx_stack[-1][key] = entry
        else:
            self.store[key] = entry

    def get(self, key: str) -> Optional[Any]:
        # Check active transactions top-down
        for tx in reversed(self.tx_stack):
            if key in tx:
                entry = tx[key]
                if entry is None or (entry[1] and time.time() >= entry[1]):
                    return None
                return entry[0]
        # Check base store
        if key in self.store:
            val, exp = self.store[key]
            if exp and time.time() >= exp:
                del self.store[key]
                return None
            return val
        return None

    def delete(self, key: str) -> bool:
        if self.get(key) is None:
            return False
        if self.tx_stack:
            self.tx_stack[-1][key] = None  # Tombstone
        else:
            del self.store[key]
        return True

    def begin(self) -> None:
        self.tx_stack.append({})

    def commit(self) -> None:
        if not self.tx_stack:
            raise RuntimeError("No active transaction")
        current_tx = self.tx_stack.pop()
        if self.tx_stack:
            self.tx_stack[-1].update(current_tx)
        else:
            for k, entry in current_tx.items():
                if entry is None: self.store.pop(k, None)
                else: self.store[k] = entry

    def rollback(self) -> None:
        if not self.tx_stack:
            raise RuntimeError("No active transaction")
        self.tx_stack.pop()
```

---

### 1.2 Python Complete Solution

Full production-style implementation with Abstract Base Class, dataclass `Entry`, context managers, and assertions.

```python
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
import time
from typing import Any, Dict, Iterator, List, Optional

@dataclass
class Entry:
    value: Any
    expiry: Optional[float] = None

    def is_expired(self) -> bool:
        return self.expiry is not None and time.time() >= self.expiry

class BaseKVStore(ABC):
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None: ...
    @abstractmethod
    def get(self, key: str) -> Optional[Any]: ...
    @abstractmethod
    def delete(self, key: str) -> bool: ...
    @abstractmethod
    def begin(self) -> None: ...
    @abstractmethod
    def commit(self) -> None: ...
    @abstractmethod
    def rollback(self) -> None: ...

class InMemoryKVStore(BaseKVStore):
    def __init__(self) -> None:
        self._store: Dict[str, Entry] = {}
        self._tx_stack: List[Dict[str, Optional[Entry]]] = []

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        expiry = time.time() + ttl if ttl is not None else None
        entry = Entry(value=value, expiry=expiry)
        if self._tx_stack:
            self._tx_stack[-1][key] = entry
        else:
            self._store[key] = entry

    def get(self, key: str) -> Optional[Any]:
        for tx in reversed(self._tx_stack):
            if key in tx:
                entry = tx[key]
                return None if (entry is None or entry.is_expired()) else entry.value
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.is_expired():
            del self._store[key]
            return None
        return entry.value

    def delete(self, key: str) -> bool:
        if self.get(key) is None:
            return False
        if self._tx_stack:
            self._tx_stack[-1][key] = None
        else:
            self._store.pop(key, None)
        return True

    def begin(self) -> None:
        self._tx_stack.append({})

    def commit(self) -> None:
        if not self._tx_stack:
            raise RuntimeError("No active transaction.")
        current_tx = self._tx_stack.pop()
        if self._tx_stack:
            self._tx_stack[-1].update(current_tx)
        else:
            for k, entry in current_tx.items():
                if entry is None: self._store.pop(k, None)
                else: self._store[k] = entry

    def rollback(self) -> None:
        if not self._tx_stack:
            raise RuntimeError("No active transaction.")
        self._tx_stack.pop()

    @contextmanager
    def transaction(self) -> Iterator["InMemoryKVStore"]:
        self.begin()
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise

# Verification Tests
if __name__ == "__main__":
    kv = InMemoryKVStore()
    kv.set("user", "alice")
    assert kv.get("user") == "alice"
    
    with kv.transaction():
        kv.set("user", "bob")
        assert kv.get("user") == "bob"
    
    assert kv.get("user") == "bob"
    
    # Rollback verification
    kv.begin()
    kv.set("user", "charlie")
    assert kv.get("user") == "charlie"
    kv.rollback()
    assert kv.get("user") == "bob"
    print("Python KV Store tests passed successfully!")
```

---

# 2. C++ Solutions

### 2.1 C++ Interview Solution

#### 1. Primary Capabilities
- Fast hash-table key-value storage using `std::unordered_map`.
- TTL support via `std::chrono::steady_clock`.
- Multi-level nested transactions using a stack of hash maps (`std::optional<Entry>`).

#### 2. Error Handling
- Rollback or commit with no active transaction throws `std::runtime_error`.
- Tombstoned keys (`std::nullopt`) properly mask existing parent/base keys.

#### 3. Out Of Scope
- Multi-threaded read-write locks (`std::shared_mutex`).
- Disk persistence engine.

```cpp
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>
#include <optional>
#include <chrono>
#include <stdexcept>

class InMemoryKVStore {
    struct Entry {
        std::string value;
        std::optional<std::chrono::steady_clock::time_point> expiry;
        bool is_expired() const {
            return expiry.has_value() && std::chrono::steady_clock::now() >= *expiry;
        }
    };

    std::unordered_map<std::string, Entry> store;
    std::vector<std::unordered_map<std::string, std::optional<Entry>>> tx_stack;

public:
    void set(const std::string& key, const std::string& val, std::optional<int> ttl_sec = std::nullopt) {
        std::optional<std::chrono::steady_clock::time_point> exp;
        if (ttl_sec) exp = std::chrono::steady_clock::now() + std::chrono::seconds(*ttl_sec);
        Entry entry{val, exp};

        if (!tx_stack.empty()) tx_stack.back()[key] = entry;
        else store[key] = entry;
    }

    std::optional<std::string> get(const std::string& key) {
        for (auto it = tx_stack.rbegin(); it != tx_stack.rend(); ++it) {
            auto found = it->find(key);
            if (found != it->end()) {
                if (!found->second || found->second->is_expired()) return std::nullopt;
                return found->second->value;
            }
        }
        auto it = store.find(key);
        if (it == store.end()) return std::nullopt;
        if (it->second.is_expired()) { store.erase(it); return std::nullopt; }
        return it->second.value;
    }

    bool del(const std::string& key) {
        if (!get(key).has_value()) return false;
        if (!tx_stack.empty()) tx_stack.back()[key] = std::nullopt;
        else store.erase(key);
        return true;
    }

    void begin() { tx_stack.emplace_back(); }
    void commit() {
        if (tx_stack.empty()) throw std::runtime_error("No active transaction.");
        auto current_tx = std::move(tx_stack.back());
        tx_stack.pop_back();

        if (!tx_stack.empty()) {
            for (auto& [k, v] : current_tx) tx_stack.back()[k] = std::move(v);
        } else {
            for (auto& [k, v] : current_tx) {
                if (!v) store.erase(k);
                else store[k] = std::move(*v);
            }
        }
    }
    void rollback() {
        if (tx_stack.empty()) throw std::runtime_error("No active transaction.");
        tx_stack.pop_back();
    }
};
```

---

### 2.2 C++ Complete Solution

Complete C++17 implementation with unit tests and assertions.

```cpp
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>
#include <optional>
#include <chrono>
#include <cassert>
#include <stdexcept>

class InMemoryKVStore {
    struct Entry {
        std::string value;
        std::optional<std::chrono::steady_clock::time_point> expiry;

        bool is_expired() const {
            if (!expiry.has_value()) return false;
            return std::chrono::steady_clock::now() >= expiry.value();
        }
    };

    std::unordered_map<std::string, Entry> store;
    std::vector<std::unordered_map<std::string, std::optional<Entry>>> tx_stack;

public:
    void set(const std::string& key, const std::string& val, std::optional<int> ttl_sec = std::nullopt) {
        std::optional<std::chrono::steady_clock::time_point> exp;
        if (ttl_sec.has_value()) {
            exp = std::chrono::steady_clock::now() + std::chrono::seconds(ttl_sec.value());
        }
        Entry entry{val, exp};

        if (!tx_stack.empty()) {
            tx_stack.back()[key] = entry;
        } else {
            store[key] = entry;
        }
    }

    std::optional<std::string> get(const std::string& key) {
        for (auto it = tx_stack.rbegin(); it != tx_stack.rend(); ++it) {
            auto found = it->find(key);
            if (found != it->end()) {
                if (!found->second.has_value() || found->second->is_expired()) {
                    return std::nullopt;
                }
                return found->second->value;
            }
        }
        auto it = store.find(key);
        if (it == store.end()) return std::nullopt;
        if (it->second.is_expired()) {
            store.erase(it);
            return std::nullopt;
        }
        return it->second.value;
    }

    bool del(const std::string& key) {
        if (!get(key).has_value()) return false;
        if (!tx_stack.empty()) {
            tx_stack.back()[key] = std::nullopt;
        } else {
            store.erase(key);
        }
        return true;
    }

    void begin() {
        tx_stack.emplace_back();
    }

    void commit() {
        if (tx_stack.empty()) throw std::runtime_error("No active transaction.");
        auto current_tx = std::move(tx_stack.back());
        tx_stack.pop_back();

        if (!tx_stack.empty()) {
            for (auto& [k, v] : current_tx) {
                tx_stack.back()[k] = std::move(v);
            }
        } else {
            for (auto& [k, v] : current_tx) {
                if (!v.has_value()) store.erase(k);
                else store[k] = std::move(*v);
            }
        }
    }

    void rollback() {
        if (tx_stack.empty()) throw std::runtime_error("No active transaction.");
        tx_stack.pop_back();
    }
};

int main() {
    InMemoryKVStore kv;
    kv.set("a", "10");
    assert(kv.get("a").value() == "10");

    kv.begin();
    kv.set("a", "20");
    kv.set("b", "30");
    assert(kv.get("a").value() == "20");
    assert(kv.get("b").value() == "30");

    kv.begin();
    kv.set("a", "99");
    assert(kv.get("a").value() == "99");
    kv.rollback();

    assert(kv.get("a").value() == "20");
    kv.commit();
    assert(kv.get("a").value() == "20");
    assert(kv.get("b").value() == "30");

    std::cout << "C++ InMemoryKVStore tests passed successfully!" << std::endl;
    return 0;
}
```

---

# 3. Rust Solutions

### 3.1 Rust Interview Solution

#### 1. Primary Capabilities
- Idiomatic Rust memory management without garbage collection overhead.
- Transaction rollback via popping nested `HashMap` stack frames.
- TTL expiration with `std::time::Instant`.

#### 2. Error Handling
- Safe `Option<String>` returns for missing or expired keys.
- `Result<(), &'static str>` returned for empty transaction commits or rollbacks.

#### 3. Out Of Scope
- Shared-state multi-threading with `Arc<RwLock<...>>`.
- Persistent storage engine.

```rust
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
```

---

### 3.2 Rust Complete Solution

Includes full nested commit merging, deletion tombstones, and unit verification tests.

```rust
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

    println!("Rust InMemoryKVStore tests passed successfully!");
}
```
