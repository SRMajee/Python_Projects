# 🚗 Ride-Sharing Engine

> **Phase**: [Phase_6: Domain-Specific LLD](../Readme.md)
> **Status**: `Completed`
> **Target Size**: `250-300 lines`

## 📌 Project Overview
Uber-like ride matching engine with grid-based spatial indexing for nearest-driver lookup, state machine trip lifecycle (REQUESTED → MATCHED → IN_PROGRESS → COMPLETED/CANCELLED), and surge pricing.

## 📂 Structure
```text
ride_sharing_engine/
├── python/
│   ├── ride_engine.py, test_ride_engine.py, interview_solution.py
├── cpp/
│   ├── solution.cpp, interview_solution.cpp
└── rust/
    ├── solution.rs, interview_solution.rs
```

## 🚀 Running
```bash
python python/test_ride_engine.py
g++ -std=c++17 -pthread cpp/solution.cpp -o cpp/solution && ./cpp/solution
rustc rust/solution.rs -o rust/solution && ./rust/solution
```
