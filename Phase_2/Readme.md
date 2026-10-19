# Phase_2: Design Patterns & Architecture

Explores architectural patterns, Strategy pattern, Directed Acyclic Graph (DAG) task scheduling, Observer notifications, and OOP balance settlement.

## Multi-Language Solutions Standard
All completed projects in this phase include comprehensive solutions in **Python**, **C++17**, and **Rust**:
1. **Concise Interview Solution**: Live-interview ready (~30-60 LOC) organized into:
   - *1. Primary Capabilities*
   - *2. Error Handling*
   - *3. Out Of Scope*
2. **Complete Solution**: Production-grade implementation with self-contained unit assertions and test suites.

## Projects in this Phase

### 1. [Task Scheduler](./task_scheduler)
- **Status**: `Completed` (Available in 🐍 Python, ⚡ C++, 🦀 Rust)
- **Core Concepts**: `Strategy Pattern, DAGs, Observer`
- **Target Size**: `150-250 lines`
- **Key Rules / Constraints**: Dependencies must execute in Topological order
- **Project Brief**: Build a cron-like executor that respects task dependencies and priorities.
- **Solutions**:
  - [Interview Solution (Concise) & Complete Solution in Python, C++, Rust](./task_scheduler/README.md)

### 2. [Splitwise Clone (Expense Sharing)](./splitwise_clone)
- **Status**: `Not Started`
- **Core Concepts**: `OOP, State Management`
- **Target Size**: `200-300 lines`
- **Key Rules / Constraints**: Must support EXACT, PERCENT, and EQUAL split types
- **Project Brief**: Manage balances between users dynamically with simplified debt graphs.
