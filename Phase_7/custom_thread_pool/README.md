# Custom Thread Pool Executor

> **Phase**: [Phase_7: Advanced Concurrency](../Readme.md)  
> **Status**: `Not Started`  
> **Target Size**: `150-200 lines`

## Overview
Build a thread pool from scratch mimicking concurrent.futures.

## Core Concepts & Patterns
- `threading, queue, Condition`

## Key Rules & Constraints
- Must implement task futures and graceful shutdown

## Structure
- [`thread_pool.py`](./thread_pool.py): Core implementation and class definitions.
- [`test_thread_pool.py`](./test_thread_pool.py): Unit test suite and verification scenarios.

## Running Tests
```bash
python test_thread_pool.py
```
