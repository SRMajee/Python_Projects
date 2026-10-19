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
| [Phase_1](./Phase_1) | [In-Memory Key-Value Store](./Phase_1/in_memory_kv_store) | 🐍 Python, ⚡ C++, 🦀 Rust | 80-120 lines | ✅ Completed | Redis-lite with TTL and transactions |
| [Phase_1](./Phase_1) | [Parking Lot Design](./Phase_1/parking_lot) | 🐍 Python, ⚡ C++, 🦀 Rust | 150-200 lines | ✅ Completed | Multi-level parking lot with dynamic pricing |
| [Phase_2](./Phase_2) | [Task Scheduler](./Phase_2/task_scheduler) | 🐍 Python, ⚡ C++, 🦀 Rust | 150-250 lines | ✅ Completed | DAG topological task runner with Observer |
| [Phase_2](./Phase_2) | [Splitwise Clone](./Phase_2/splitwise_clone) | ⏳ Planned | 200-300 lines | ⏳ Not Started | Dynamic expense sharing & debt graphs |
| [Phase_3](./Phase_3) | [Thread-Safe Rate Limiter](./Phase_3/thread_safe_rate_limiter) | ⏳ Planned | 100-150 lines | ⏳ Not Started | Token Bucket & Sliding Window limits |
| [Phase_3](./Phase_3) | [Async Web Crawler](./Phase_3/async_web_crawler) | ⏳ Planned | 100-150 lines | ⏳ Not Started | Asyncio concurrent crawler with queues |
| [Phase_4](./Phase_4) | [Pub-Sub Message Broker](./Phase_4/pub_sub_broker) | ⏳ Planned | 200-250 lines | ⏳ Not Started | In-memory Kafka with partitioned topics |
| [Phase_4](./Phase_4) | [Relational Query Engine](./Phase_4/relational_query_engine) | ⏳ Planned | 250-300 lines | ⏳ Not Started | Volcano iterator SQL query engine |
| [Phase_5](./Phase_5) | [O(1) LRU & LFU Cache](./Phase_5/lru_lfu_cache) | ⏳ Planned | 100-150 lines | ⏳ Not Started | Strict O(1) doubly linked list caches |
| [Phase_5](./Phase_5) | [Consistent Hashing Ring](./Phase_5/consistent_hashing) | ⏳ Planned | 100-150 lines | ⏳ Not Started | Consistent hash ring with virtual nodes |
| [Phase_6](./Phase_6) | [Ride-Sharing Engine](./Phase_6/ride_sharing_engine) | ⏳ Planned | 250-300 lines | ⏳ Not Started | Spatial matching Uber-clone state machine |
| [Phase_6](./Phase_6) | [Board Game Engine](./Phase_6/board_game_engine) | ⏳ Planned | 200-350 lines | ⏳ Not Started | Command-pattern extensible game engine |
| [Phase_7](./Phase_7) | [Custom Thread Pool](./Phase_7/custom_thread_pool) | ⏳ Planned | 150-200 lines | ⏳ Not Started | ThreadPoolExecutor with futures from scratch |
| [Phase_7](./Phase_7) | [Distributed Task Worker](./Phase_7/distributed_task_worker) | ⏳ Planned | 200-250 lines | ⏳ Not Started | Multi-process Celery-lite bypassing GIL |

---

## Directory Structure

```text
Python_Projects/
├── Phase_1/                   # Object-Oriented Foundations
│   ├── in_memory_kv_store/    # [Python, C++, Rust] Redis-lite with TTL and transactions
│   └── parking_lot/           # [Python, C++, Rust] Multi-level parking lot with dynamic pricing
├── Phase_2/                   # Design Patterns & Architecture
│   ├── task_scheduler/        # [Python, C++, Rust] DAG topological task runner with Observer
│   └── splitwise_clone/       # Dynamic expense sharing & debt graphs
├── Phase_3/                   # Concurrency & Reliability
│   ├── thread_safe_rate_limiter/ # Token Bucket & Sliding Window limits
│   └── async_web_crawler/     # Asyncio concurrent crawler with queues
├── Phase_4/                   # SDE 2 System Simulation
│   ├── pub_sub_broker/        # In-memory Kafka with partitioned topics
│   └── relational_query_engine/ # Volcano iterator SQL query engine
├── Phase_5/                   # Advanced Data Structures
│   ├── lru_lfu_cache/         # Strict O(1) doubly linked list caches
│   └── consistent_hashing/    # Consistent hash ring with virtual nodes
├── Phase_6/                   # Domain-Specific LLD
│   ├── ride_sharing_engine/   # Spatial matching Uber-clone state machine
│   └── board_game_engine/     # Command-pattern extensible game engine
└── Phase_7/                   # Advanced Concurrency
    ├── custom_thread_pool/    # ThreadPoolExecutor with futures from scratch
    └── distributed_task_worker/ # Multi-process Celery-lite bypassing GIL
```
