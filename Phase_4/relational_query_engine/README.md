# 🔍 Relational Query Engine

> **Phase**: [Phase_4: SDE 2 System Simulation](../Readme.md)
> **Status**: `Completed`
> **Target Size**: `250-300 lines`

## 📌 Project Overview
Volcano-model iterator-based SQL query engine supporting Table Scan, Index Scan, WHERE filter, GROUP BY (COUNT/SUM/AVG/MIN/MAX), ORDER BY, LIMIT, and nested-loop INNER JOIN.

## 📂 Structure
```text
relational_query_engine/
├── python/
│   ├── query_engine.py, test_query_engine.py, interview_solution.py
├── cpp/
│   ├── solution.cpp, interview_solution.cpp
└── rust/
    ├── solution.rs, interview_solution.rs
```

## 🚀 Running
```bash
python python/test_query_engine.py
g++ -std=c++17 -pthread cpp/solution.cpp -o cpp/solution && ./cpp/solution
rustc rust/solution.rs -o rust/solution && ./rust/solution
```
