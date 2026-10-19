# 🧵 Custom Thread Pool Executor

> **Phase**: [Phase_7: Advanced Concurrency](../Readme.md)
> **Status**: `Completed`
> **Target Size**: `150-200 lines`

## 📌 Project Overview
ThreadPoolExecutor built from scratch with worker threads, shared task queue, Future objects (blocking get, timeout, cancel, callbacks), graceful shutdown, and exception propagation.

## 📂 Structure
```text
custom_thread_pool/
├── python/
│   ├── thread_pool.py, test_thread_pool.py, interview_solution.py
├── cpp/
│   ├── solution.cpp, interview_solution.cpp
└── rust/
    ├── solution.rs, interview_solution.rs
```

## 🚀 Running
```bash
python python/test_thread_pool.py
g++ -std=c++17 -pthread cpp/solution.cpp -o cpp/solution && ./cpp/solution
rustc rust/solution.rs -o rust/solution && ./rust/solution
```
