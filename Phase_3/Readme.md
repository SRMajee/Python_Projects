# Phase_3: Concurrency & Reliability

Focuses on multithreading synchronization, locks, condition variables, rate limiting algorithms, and asynchronous networking with asyncio.

## Projects in this Phase

### 1. [Thread-Safe Rate Limiter](./thread_safe_rate_limiter)
- **Core Concepts**: `threading, Locks, Sliding Window`
- **Target Size**: `100-150 lines`
- **Key Rules / Constraints**: Must be thread-safe
- **Status**: `Completed`
- **Project Brief**: Implement Token Bucket and Sliding Window rate limiting algorithms for APIs.

### 2. [Async Web Crawler](./async_web_crawler)
- **Core Concepts**: `asyncio, aiohttp, queues`
- **Target Size**: `100-150 lines`
- **Key Rules / Constraints**: Max concurrent connections enforced
- **Status**: `Completed`
- **Project Brief**: A highly concurrent crawler handling rate limits and robot.txt asynchronously.

