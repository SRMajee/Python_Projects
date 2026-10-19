# 🚦 Thread-Safe Rate Limiter

> **Phase**: [Phase_3: Concurrency & Reliability](../Readme.md)
> **Status**: `Completed`
> **Target Size**: `100-150 lines`

## 📌 Project Overview
Implements Token Bucket and Sliding Window (Log + Counter) rate limiting algorithms with per-key isolation. All algorithms are thread-safe via mutex/lock protection.

## 📂 Structure
```text
thread_safe_rate_limiter/
├── python/
│   ├── rate_limiter.py, test_rate_limiter.py, interview_solution.py
├── cpp/
│   ├── solution.cpp, interview_solution.cpp
└── rust/
    ├── solution.rs, interview_solution.rs
```

## 🚀 Running
```bash
python python/test_rate_limiter.py
g++ -std=c++17 -pthread cpp/solution.cpp -o cpp/solution && ./cpp/solution
rustc rust/solution.rs -o rust/solution && ./rust/solution
```
