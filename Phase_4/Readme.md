# Phase_4: SDE 2 System Simulation

Simulates production-scale distributed components: in-memory Kafka partitioned brokers with consumer groups and an iterator-based relational query engine.

## Projects in this Phase

### 1. [Pub-Sub Message Broker](./pub_sub_broker)
- **Core Concepts**: `Generators, Observer Pattern`
- **Target Size**: `200-250 lines`
- **Key Rules / Constraints**: Simulates partitioned topics and consumer groups
- **Status**: `Completed`
- **Project Brief**: Build an in-memory Kafka clone handling publishing and subscribing events.

### 2. [Relational Query Engine Simulation](./relational_query_engine)
- **Core Concepts**: `iterators, B-Tree models`
- **Target Size**: `250-300 lines`
- **Key Rules / Constraints**: Table scans vs Index scans must be measurable
- **Status**: `Completed`
- **Project Brief**: Simulate a SQL engine executing WHERE, GROUP BY, and simple JOINS on nested dicts.

