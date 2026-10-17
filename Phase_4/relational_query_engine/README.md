# Relational Query Engine Simulation

> **Phase**: [Phase_4: SDE 2 System Simulation](../Readme.md)  
> **Status**: `Not Started`  
> **Target Size**: `250-300 lines`

## Overview
Simulate a SQL engine executing WHERE, GROUP BY, and simple JOINS on nested dicts.

## Core Concepts & Patterns
- `iterators, B-Tree models`

## Key Rules & Constraints
- Table scans vs Index scans must be measurable

## Structure
- [`query_engine.py`](./query_engine.py): Core implementation and class definitions.
- [`test_query_engine.py`](./test_query_engine.py): Unit test suite and verification scenarios.

## Running Tests
```bash
python test_query_engine.py
```
