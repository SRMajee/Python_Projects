# Async Web Crawler

> **Phase**: [Phase_3: Concurrency & Reliability](../Readme.md)  
> **Status**: `Not Started`  
> **Target Size**: `100-150 lines`

## Overview
A highly concurrent crawler handling rate limits and robot.txt asynchronously.

## Core Concepts & Patterns
- `asyncio, aiohttp, queues`

## Key Rules & Constraints
- Max concurrent connections enforced

## Structure
- [`crawler.py`](./crawler.py): Core implementation and class definitions.
- [`test_crawler.py`](./test_crawler.py): Unit test suite and verification scenarios.

## Running Tests
```bash
python test_crawler.py
```
