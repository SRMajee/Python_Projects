# 🔗 Consistent Hashing Ring

> **Phase**: [Phase_5: Advanced Data Structures](../Readme.md)
> **Status**: `Completed`
> **Target Size**: `100-150 lines`

## 📌 Project Overview
Consistent hash ring with virtual nodes for uniform key distribution. Supports dynamic node addition/removal with minimal key redistribution. O(log n) lookups via sorted data structures.

## 📂 Structure
```text
consistent_hashing/
├── python/
│   ├── consistent_hash.py, test_consistent_hash.py, interview_solution.py
├── cpp/
│   ├── solution.cpp, interview_solution.cpp
└── rust/
    ├── solution.rs, interview_solution.rs
```

## 🚀 Running
```bash
python python/test_consistent_hash.py
g++ -std=c++17 -pthread cpp/solution.cpp -o cpp/solution && ./cpp/solution
rustc rust/solution.rs -o rust/solution && ./rust/solution
```
