# ⚙️ Distributed Task Worker (Celery Clone)

> **Phase**: [Phase_7: Advanced Concurrency](../Readme.md)
> **Status**: `Completed`
> **Target Size**: `200-250 lines`

## 📌 Project Overview
Multi-process (Python) / multi-threaded (C++/Rust) Celery-like task execution system with in-memory broker, result backend, task registry, retry with exponential backoff, and process-safe result collection.

## 📂 Structure
```text
distributed_task_worker/
├── python/
│   ├── task_worker.py, test_task_worker.py, interview_solution.py
├── cpp/
│   ├── solution.cpp, interview_solution.cpp
└── rust/
    ├── solution.rs, interview_solution.rs
```

## 🚀 Running
```bash
python python/test_task_worker.py
g++ -std=c++17 -pthread cpp/solution.cpp -o cpp/solution && ./cpp/solution
rustc rust/solution.rs -o rust/solution && ./rust/solution
```
