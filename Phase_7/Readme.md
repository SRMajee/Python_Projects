# Phase_7: Advanced Concurrency

Tackles production-grade concurrency & IPC: building a custom ThreadPoolExecutor with futures/conditions and a multi-process distributed task worker bypassing the GIL.

## Projects in this Phase

### 1. [Custom Thread Pool Executor](./custom_thread_pool)
- **Core Concepts**: `threading, queue, Condition`
- **Target Size**: `150-200 lines`
- **Key Rules / Constraints**: Must implement task futures and graceful shutdown
- **Status**: `Completed`
- **Project Brief**: Build a thread pool from scratch mimicking concurrent.futures.

### 2. [Distributed Task Worker (Celery Clone)](./distributed_task_worker)
- **Core Concepts**: `multiprocessing, IPC, IPC Queues`
- **Target Size**: `200-250 lines`
- **Key Rules / Constraints**: Must bypass the GIL to execute CPU-bound tasks
- **Status**: `Completed`
- **Project Brief**: Implement a background daemon that pulls and executes heavy tasks across multiple processes.

