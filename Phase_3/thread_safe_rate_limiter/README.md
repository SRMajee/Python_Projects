# Thread-Safe Rate Limiter

> **Phase**: [Phase_3: Concurrency & Reliability](../Readme.md)  
> **Status**: `Not Started`  
> **Target Size**: `100-150 lines`

## Overview
Implement Token Bucket and Sliding Window rate limiting algorithms for APIs.

## Core Concepts & Patterns
- `threading, Locks, Sliding Window`

## Key Rules & Constraints
- Must be thread-safe

## Structure
- [`rate_limiter.py`](./rate_limiter.py): Core implementation and class definitions.
- [`test_rate_limiter.py`](./test_rate_limiter.py): Unit test suite and verification scenarios.

## Running Tests
```bash
python test_rate_limiter.py
```
