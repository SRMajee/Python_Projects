# 🕷️ Async Web Crawler

> **Phase**: [Phase_3: Concurrency & Reliability](../Readme.md)
> **Status**: `Completed`
> **Target Size**: `100-150 lines`

## 📌 Project Overview
BFS-based concurrent web crawler with depth limiting, URL deduplication, and configurable concurrency. Python uses asyncio + semaphore, C++ and Rust use thread pools with condition variables.

## 📂 Structure
```text
async_web_crawler/
├── python/
│   ├── crawler.py, test_crawler.py, interview_solution.py
├── cpp/
│   ├── solution.cpp, interview_solution.cpp
└── rust/
    ├── solution.rs, interview_solution.rs
```

## 🚀 Running
```bash
python python/test_crawler.py
g++ -std=c++17 -pthread cpp/solution.cpp -o cpp/solution && ./cpp/solution
rustc rust/solution.rs -o rust/solution && ./rust/solution
```
