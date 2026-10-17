# Task Scheduler

> **Phase**: [Phase_2: Design Patterns & Architecture](../Readme.md)  
> **Status**: `Not Started`  
> **Target Size**: `150-250 lines`

## Overview
Build a cron-like executor that respects task dependencies and priorities.

## Core Concepts & Patterns
- `Strategy Pattern, DAGs, Observer`

## Key Rules & Constraints
- Dependencies must execute in Topological order

## Structure
- [`scheduler.py`](./scheduler.py): Core implementation and class definitions.
- [`test_scheduler.py`](./test_scheduler.py): Unit test suite and verification scenarios.

## Running Tests
```bash
python test_scheduler.py
```
