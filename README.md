# Python & Multi-Language Systems & Low-Level Design (LLD) Roadmap

A rigorous, hands-on roadmap implementing production-grade systems, concurrency architectures, design patterns, and low-level data structures from scratch in **Python**, **C++**, and **Rust** with zero or minimal dependencies.

## Multi-Language Solution Architecture
Every completed project contains two distinct solution tiers across **Python**, **C++**, and **Rust**:
- **Type A: Complete Solution with Working Tests**: Full production-style architecture with test suites.
- **Type B: Concise Interview Solution**: Live whiteboard / coding interview blueprint structured with:
  1. **Primary Capabilities**
  2. **Error Handling**
  3. **Out Of Scope**

---

## Curriculum Progress & Overview

| Phase | Project Name | Languages | Target Size (LOC) | Status | Project Brief |
| :--- | :--- | :---: | :---: | :---: | :--- |
| [Phase_1](./Phase_1) | [In-Memory Key-Value Store](./Phase_1/in_memory_kv_store) | 🐍 Python, 🔧 C++, 🦀 Rust | 80-120 lines | ✅ Completed | Redis-lite with TTL and transactions |
| [Phase_1](./Phase_1) | [Parking Lot Design](./Phase_1/parking_lot) | 🐍 Python, 🔧 C++, 🦀 Rust | 150-200 lines | ✅ Completed | Multi-level parking lot with dynamic pricing |
| [Phase_2](./Phase_2) | [Task Scheduler](./Phase_2/task_scheduler) | 🐍 Python, 🔧 C++, 🦀 Rust | 150-250 lines | ✅ Completed | DAG topological task runner with Observer |
| [Phase_2](./Phase_2) | [Splitwise Clone](./Phase_2/splitwise_clone) | 🐍 Python, 🔧 C++, 🦀 Rust | 200-300 lines | ✅ Completed | Dynamic expense sharing & debt graphs |
| [Phase_3](./Phase_3) | [Thread-Safe Rate Limiter](./Phase_3/thread_safe_rate_limiter) | 🐍 Python, 🔧 C++, 🦀 Rust | 100-150 lines | ✅ Completed | Token Bucket & Sliding Window limits |
| [Phase_3](./Phase_3) | [Async Web Crawler](./Phase_3/async_web_crawler) | 🐍 Python, 🔧 C++, 🦀 Rust | 100-150 lines | ✅ Completed | Asyncio concurrent crawler with queues |
| [Phase_4](./Phase_4) | [Pub-Sub Message Broker](./Phase_4/pub_sub_broker) | 🐍 Python, 🔧 C++, 🦀 Rust | 200-250 lines | ✅ Completed | In-memory Kafka with partitioned topics |
| [Phase_4](./Phase_4) | [Relational Query Engine](./Phase_4/relational_query_engine) | 🐍 Python, 🔧 C++, 🦀 Rust | 250-300 lines | ✅ Completed | Volcano iterator SQL query engine |
| [Phase_5](./Phase_5) | [O(1) LRU & LFU Cache](./Phase_5/lru_lfu_cache) | 🐍 Python, 🔧 C++, 🦀 Rust | 100-150 lines | ✅ Completed | Strict O(1) doubly linked list caches |
| [Phase_5](./Phase_5) | [Consistent Hashing Ring](./Phase_5/consistent_hashing) | 🐍 Python, 🔧 C++, 🦀 Rust | 100-150 lines | ✅ Completed | Consistent hash ring with virtual nodes |
| [Phase_6](./Phase_6) | [Ride-Sharing Engine](./Phase_6/ride_sharing_engine) | 🐍 Python, 🔧 C++, 🦀 Rust | 250-300 lines | ✅ Completed | Spatial matching Uber-clone state machine |
| [Phase_6](./Phase_6) | [Board Game Engine](./Phase_6/board_game_engine) | 🐍 Python, 🔧 C++, 🦀 Rust | 200-350 lines | ✅ Completed | Command-pattern extensible game engine |
| [Phase_7](./Phase_7) | [Custom Thread Pool](./Phase_7/custom_thread_pool) | 🐍 Python, 🔧 C++, 🦀 Rust | 150-200 lines | ✅ Completed | ThreadPoolExecutor with futures from scratch |
| [Phase_7](./Phase_7) | [Distributed Task Worker](./Phase_7/distributed_task_worker) | 🐍 Python, 🔧 C++, 🦀 Rust | 200-250 lines | ✅ Completed | Multi-process Celery-lite bypassing GIL |

---

## Directory Structure

```text
Python_Projects/
├── Phase_1/                   # Object-Oriented Foundations
│   ├── in_memory_kv_store/    # [Python, C++, Rust] Redis-lite with TTL and transactions
│   └── parking_lot/           # [Python, C++, Rust] Multi-level parking lot with dynamic pricing
├── Phase_2/                   # Design Patterns & Architecture
│   ├── task_scheduler/        # [Python, C++, Rust] DAG topological task runner with Observer
│   └── splitwise_clone/       # [Python, C++, Rust] Dynamic expense sharing & debt graphs
├── Phase_3/                   # Concurrency & Reliability
│   ├── thread_safe_rate_limiter/ # [Python, C++, Rust] Token Bucket & Sliding Window limits
│   └── async_web_crawler/     # [Python, C++, Rust] Asyncio concurrent crawler with queues
├── Phase_4/                   # SDE 2 System Simulation
│   ├── pub_sub_broker/        # [Python, C++, Rust] In-memory Kafka with partitioned topics
│   └── relational_query_engine/ # [Python, C++, Rust] Volcano iterator SQL query engine
├── Phase_5/                   # Advanced Data Structures
│   ├── lru_lfu_cache/         # [Python, C++, Rust] Strict O(1) doubly linked list caches
│   └── consistent_hashing/    # [Python, C++, Rust] Consistent hash ring with virtual nodes
├── Phase_6/                   # Domain-Specific LLD
│   ├── ride_sharing_engine/   # [Python, C++, Rust] Spatial matching Uber-clone state machine
│   └── board_game_engine/     # [Python, C++, Rust] Command-pattern extensible game engine
└── Phase_7/                   # Advanced Concurrency
    ├── custom_thread_pool/    # [Python, C++, Rust] ThreadPoolExecutor with futures from scratch
    └── distributed_task_worker/ # [Python, C++, Rust] Multi-process Celery-lite bypassing GIL
```

## Per-Project Structure

Each project follows this consistent structure:
```text
project_name/
├── README.md                  # Project overview, running instructions
├── python/
│   ├── solution.py (or named module)  # Complete solution with full features
│   ├── test_solution.py               # Comprehensive test suite
│   └── interview_solution.py          # Concise interview blueprint
├── cpp/
│   ├── solution.cpp                   # Complete C++ solution (uses bits/stdc++.h)
│   └── interview_solution.cpp         # Concise interview solution
└── rust/
    ├── solution.rs                    # Complete Rust solution
    └── interview_solution.rs          # Concise interview solution
```

## Concurrency Notes
Every project includes concurrency extensibility:
- **Python**: `threading.Lock` / `asyncio.Semaphore` for thread-safe access
- **C++**: `std::mutex` / `std::condition_variable` for synchronized access
- **Rust**: `Arc<Mutex<>>` / `Condvar` for thread-safe shared state
- **Phase 7** projects are inherently concurrent by design
