# 🗄️ O(1) LRU & LFU Cache

> **Phase**: [Phase_5: Advanced Data Structures](../Readme.md)
> **Status**: `Completed`
> **Target Size**: `100-150 lines`

## 📌 Project Overview
Strict O(1) cache implementations: LRU using HashMap + Doubly Linked List, LFU using HashMap + Frequency bucket DLLs with LRU tie-breaking within same frequency.

## 📂 Structure
```text
lru_lfu_cache/
├── python/
│   ├── cache.py, test_cache.py, interview_solution.py
├── cpp/
│   ├── solution.cpp, interview_solution.cpp
└── rust/
    ├── solution.rs, interview_solution.rs
```

## 🚀 Running
```bash
python python/test_cache.py
g++ -std=c++17 -pthread cpp/solution.cpp -o cpp/solution && ./cpp/solution
rustc rust/solution.rs -o rust/solution && ./rust/solution
```
