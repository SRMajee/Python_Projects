# Pub-Sub Message Broker

> **Phase**: [Phase_4: SDE 2 System Simulation](../Readme.md)  
> **Status**: `Not Started`  
> **Target Size**: `200-250 lines`

## Overview
Build an in-memory Kafka clone handling publishing and subscribing events.

## Core Concepts & Patterns
- `Generators, Observer Pattern`

## Key Rules & Constraints
- Simulates partitioned topics and consumer groups

## Structure
- [`broker.py`](./broker.py): Core implementation and class definitions.
- [`test_broker.py`](./test_broker.py): Unit test suite and verification scenarios.

## Running Tests
```bash
python test_broker.py
```
