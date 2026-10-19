# 📨 Pub-Sub Message Broker

> **Phase**: [Phase_4: SDE 2 System Simulation](../Readme.md)
> **Status**: `Completed`
> **Target Size**: `200-250 lines`

## 📌 Project Overview
In-memory Kafka-like message broker with partitioned topics, consumer groups with independent offset tracking, key-hash or round-robin partition assignment, and at-least-once delivery semantics.

## 📂 Structure
```text
pub_sub_broker/
├── python/
│   ├── broker.py, test_broker.py, interview_solution.py
├── cpp/
│   ├── solution.cpp, interview_solution.cpp
└── rust/
    ├── solution.rs, interview_solution.rs
```

## 🚀 Running
```bash
python python/test_broker.py
g++ -std=c++17 -pthread cpp/solution.cpp -o cpp/solution && ./cpp/solution
rustc rust/solution.rs -o rust/solution && ./rust/solution
```
