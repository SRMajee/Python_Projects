# Distributed Task Worker (Celery Clone)

> **Phase**: [Phase_7: Advanced Concurrency](../Readme.md)  
> **Status**: `Not Started`  
> **Target Size**: `200-250 lines`

## Overview
Implement a background daemon that pulls and executes heavy tasks across multiple processes.

## Core Concepts & Patterns
- `multiprocessing, IPC, IPC Queues`

## Key Rules & Constraints
- Must bypass the GIL to execute CPU-bound tasks

## Structure
- [`worker.py`](./worker.py): Core implementation and class definitions.
- [`test_worker.py`](./test_worker.py): Unit test suite and verification scenarios.

## Running Tests
```bash
python test_worker.py
```
