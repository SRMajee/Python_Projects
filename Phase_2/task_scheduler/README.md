# Task Scheduler

> **Phase**: [Phase_2: Design Patterns & Architecture](../Readme.md)  
> **Status**: `Completed`  
> **Target Size**: `150-250 lines`

---

## 📌 Project Overview
Build a cron-like task executor that respects task dependencies (Directed Acyclic Graph) and priorities using Topological Sorting, the Strategy Pattern, and the Observer Pattern.

---

## 🧠 Core Concepts & Patterns
- **Directed Acyclic Graph (DAG) & Topological Ordering**: Dependencies executed in Kahn's algorithm order with cycle detection.
- **Priority Tie-Breaking**: When multiple tasks are independent and ready, execute higher priority tasks first.
- **Strategy Pattern**: Pluggable sequential and concurrent execution engines.
- **Observer Pattern**: Granular lifecycle event notifications (`Running`, `Completed`, `Failed`).

---

## ⚠️ Key Rules & Constraints
- Tasks must execute only after all dependencies have completed successfully.
- Cycles must be detected and reported before or during execution.
- Extensible observer notifications for status updates.

---

## 📂 Project Structure & Multi-Language Solutions

```text
task_scheduler/
├── README.md
├── python/
│   ├── scheduler.py             # Complete production-style implementation
│   ├── test_scheduler.py        # Comprehensive unit test suite (17 tests)
│   ├── interview_solution.py    # Concise 45-min interview code with requirements & error handling
│   └── INTERVIEW_GUIDE.md       # Interview strategy & live coding Q&A
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
# Run comprehensive test suite
python python/test_scheduler.py

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
