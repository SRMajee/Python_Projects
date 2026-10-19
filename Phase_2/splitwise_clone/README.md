# Splitwise Clone (Expense Sharing)

> **Phase**: [Phase_2: Design Patterns & Architecture](../Readme.md)
> **Status**: `Completed`
> **Target Size**: `200-300 lines`

## 📌 Project Overview
Multi-user expense manager with EQUAL, EXACT, and PERCENT split strategies. Tracks pairwise balances and supports min-cash-flow debt simplification.

## 📂 Structure
```text
splitwise_clone/
├── python/
│   ├── splitwise.py, test_splitwise.py, interview_solution.py
├── cpp/
│   ├── solution.cpp, interview_solution.cpp
└── rust/
    ├── solution.rs, interview_solution.rs
```

## 🚀 Running
```bash
python python/test_splitwise.py
g++ -std=c++17 cpp/solution.cpp -o cpp/solution && ./cpp/solution
rustc rust/solution.rs -o rust/solution && ./rust/solution
```
