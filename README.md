# Python Systems & Low-Level Design (LLD) Roadmap

A rigorous, hands-on roadmap implementing production-grade systems, concurrency architectures, design patterns, and low-level data structures from scratch in Python with zero or minimal dependencies.

## Curriculum Progress & Overview

| Phase | Project Name | Core Concepts | Target Size (LOC) | Key Rules / Constraints | Status | Project Brief |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| [Phase_1: Object-Oriented Foundations](./Phase_1) | [In-Memory Key-Value Store](./Phase_1/in_memory_kv_store) | `abc, dataclasses, typing` | 80-120 lines | Zero external libs, strict type hints | ⏳ Not Started | Build a Redis-lite with TTL and transactions. |
| [Phase_1: Object-Oriented Foundations](./Phase_1) | [Parking Lot Design](./Phase_1/parking_lot) | `Inheritance, Composition, Factory` | 150-200 lines | Must be easily extensible to new vehicle types | ⏳ Not Started | Design a multi-level parking lot with different spot sizes and dynamic pricing. |
| [Phase_2: Design Patterns & Architecture](./Phase_2) | [Task Scheduler](./Phase_2/task_scheduler) | `Strategy Pattern, DAGs, Observer` | 150-250 lines | Dependencies must execute in Topological order | ⏳ Not Started | Build a cron-like executor that respects task dependencies and priorities. |
| [Phase_2: Design Patterns & Architecture](./Phase_2) | [Splitwise Clone (Expense Sharing)](./Phase_2/splitwise_clone) | `OOP, State Management` | 200-300 lines | Must support EXACT, PERCENT, and EQUAL split types | ⏳ Not Started | Manage balances between users dynamically with simplified debt graphs. |
| [Phase_3: Concurrency & Reliability](./Phase_3) | [Thread-Safe Rate Limiter](./Phase_3/thread_safe_rate_limiter) | `threading, Locks, Sliding Window` | 100-150 lines | Must be thread-safe | ⏳ Not Started | Implement Token Bucket and Sliding Window rate limiting algorithms for APIs. |
| [Phase_3: Concurrency & Reliability](./Phase_3) | [Async Web Crawler](./Phase_3/async_web_crawler) | `asyncio, aiohttp, queues` | 100-150 lines | Max concurrent connections enforced | ⏳ Not Started | A highly concurrent crawler handling rate limits and robot.txt asynchronously. |
| [Phase_4: SDE 2 System Simulation](./Phase_4) | [Pub-Sub Message Broker](./Phase_4/pub_sub_broker) | `Generators, Observer Pattern` | 200-250 lines | Simulates partitioned topics and consumer groups | ⏳ Not Started | Build an in-memory Kafka clone handling publishing and subscribing events. |
| [Phase_4: SDE 2 System Simulation](./Phase_4) | [Relational Query Engine Simulation](./Phase_4/relational_query_engine) | `iterators, B-Tree models` | 250-300 lines | Table scans vs Index scans must be measurable | ⏳ Not Started | Simulate a SQL engine executing WHERE, GROUP BY, and simple JOINS on nested dicts. |
| [Phase_5: Advanced Data Structures](./Phase_5) | [O(1) LRU & LFU Cache](./Phase_5/lru_lfu_cache) | `Doubly Linked Lists, Hash Maps` | 100-150 lines | Strict O(1) time complexity for get and put | ⏳ Not Started | Implement a cache library with multiple eviction strategies. |
| [Phase_5: Advanced Data Structures](./Phase_5) | [Consistent Hashing Ring](./Phase_5/consistent_hashing) | `bisect, hashing` | 100-150 lines | Must handle node addition/removal gracefully | ⏳ Not Started | Simulate a load balancer distributing requests to server nodes. |
| [Phase_6: Domain-Specific LLD](./Phase_6) | [Ride-Sharing Engine (Uber Clone)](./Phase_6/ride_sharing_engine) | `Spatial Grids, State Machines` | 250-300 lines | Must handle concurrent booking requests | ⏳ Not Started | Match riders to nearest drivers using a coordinate grid system. |
| [Phase_6: Domain-Specific LLD](./Phase_6) | [Board Game Engine (Snake & Ladder / Chess)](./Phase_6/board_game_engine) | `2D Arrays, Command Pattern` | 200-350 lines | Must validate all moves strictly | ⏳ Not Started | Build an extensible board game framework. |
| [Phase_7: Advanced Concurrency](./Phase_7) | [Custom Thread Pool Executor](./Phase_7/custom_thread_pool) | `threading, queue, Condition` | 150-200 lines | Must implement task futures and graceful shutdown | ⏳ Not Started | Build a thread pool from scratch mimicking concurrent.futures. |
| [Phase_7: Advanced Concurrency](./Phase_7) | [Distributed Task Worker (Celery Clone)](./Phase_7/distributed_task_worker) | `multiprocessing, IPC, IPC Queues` | 200-250 lines | Must bypass the GIL to execute CPU-bound tasks | ⏳ Not Started | Implement a background daemon that pulls and executes heavy tasks across multiple processes. |

---

## Directory Structure

```text
Python_Projects/
├── Phase_1/                   # Object-Oriented Foundations
│   ├── in_memory_kv_store/    # Redis-lite with TTL and transactions
│   └── parking_lot/           # Multi-level parking lot with dynamic pricing
├── Phase_2/                   # Design Patterns & Architecture
│   ├── task_scheduler/        # DAG topological task runner with Observer
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

## Getting Started

Each project contains its own self-contained module, tests, and documentation.
To test any individual project:

```bash
# Example: Run tests for Phase 1 In-Memory KV Store
cd Phase_1/in_memory_kv_store
python test_kv_store.py
```
