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

## 📂 Project Structure & Multi-Language Solutions

```text
in_memory_kv_store/
├── README.md
├── python/
│   ├── kv_store.py              # Complete implementation with context managers & typing
│   ├── test_kv_store.py         # Full unit test suite (CRUD, TTL, nested transactions)
│   └── interview_solution.py    # Concise 45-min interview code with scoping & error handling
├── cpp/
│   ├── solution.cpp             # Complete C++17 solution with tests
│   └── interview_solution.cpp   # Concise interview solution with scoping & error handling
└── rust/
    ├── solution.rs              # Complete Rust solution with tests
    └── interview_solution.rs    # Concise interview solution with scoping & error handling
```

---

## 🚀 Running Tests & Verification

### 🐍 Python
```bash
# Run complete test suite
python python/test_kv_store.py

# Run concise interview solution
python python/interview_solution.py
```

### ⚡ C++
```bash
# Run complete C++ solution with tests
g++ -std=c++17 cpp/solution.cpp -o cpp/solution && ./cpp/solution

# Run concise interview C++ solution
g++ -std=c++17 cpp/interview_solution.cpp -o cpp/interview_solution && ./cpp/interview_solution
```

### 🦀 Rust
```bash
# Run complete Rust solution with tests
rustc rust/solution.rs -o rust/solution && ./rust/solution

# Run concise interview Rust solution
rustc rust/interview_solution.rs -o rust/interview_solution && ./rust/interview_solution
```
