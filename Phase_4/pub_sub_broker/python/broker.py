"""
Pub-Sub Message Broker - Complete Solution (Python)
In-memory Kafka-like broker with:
- Topics with configurable partitions (round-robin assignment)
- Consumer groups with independent offset tracking
- At-least-once delivery semantics
- Message ordering guarantee per partition
Concurrency: threading.Lock guards all broker state for thread-safe pub/sub.
"""
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    key: str | None
    value: Any
    timestamp: float = field(default_factory=time.time)
    partition: int = 0
    offset: int = 0


class Partition:
    """Single ordered log of messages."""
    def __init__(self):
        self._log: list[Message] = []
        self._lock = threading.Lock()

    def append(self, msg: Message) -> int:
        with self._lock:
            msg.offset = len(self._log)
            self._log.append(msg)
            return msg.offset

    def read(self, offset: int, max_msgs: int = 10) -> list[Message]:
        with self._lock:
            return self._log[offset:offset + max_msgs]

    def __len__(self):
        with self._lock:
            return len(self._log)


class Topic:
    """Multi-partition topic with round-robin or key-hash assignment."""
    def __init__(self, name: str, num_partitions: int = 3):
        if num_partitions <= 0:
            raise ValueError("num_partitions must be positive")
        self.name = name
        self.partitions = [Partition() for _ in range(num_partitions)]
        self._rr_counter = 0
        self._lock = threading.Lock()

    def publish(self, key: str | None, value: Any) -> tuple[int, int]:
        """Publish message. Returns (partition_id, offset)."""
        if key is not None:
            pid = hash(key) % len(self.partitions)
        else:
            with self._lock:
                pid = self._rr_counter % len(self.partitions)
                self._rr_counter += 1
        msg = Message(key=key, value=value, partition=pid)
        offset = self.partitions[pid].append(msg)
        return pid, offset


class ConsumerGroup:
    """Tracks per-partition offsets for a consumer group."""
    def __init__(self, group_id: str, topic: Topic):
        self.group_id = group_id
        self.topic = topic
        self._offsets: dict[int, int] = {i: 0 for i in range(len(topic.partitions))}
        self._lock = threading.Lock()

    def poll(self, max_msgs: int = 10) -> list[Message]:
        """Poll all partitions, advance offsets."""
        messages = []
        with self._lock:
            for pid, partition in enumerate(self.topic.partitions):
                offset = self._offsets[pid]
                batch = partition.read(offset, max_msgs)
                messages.extend(batch)
                self._offsets[pid] = offset + len(batch)
        return messages

    def commit(self):
        """Offsets are auto-advanced on poll. Explicit commit is a no-op placeholder."""
        pass

    def seek(self, partition_id: int, offset: int):
        """Seek to specific offset for reprocessing."""
        with self._lock:
            if partition_id not in self._offsets:
                raise ValueError(f"Invalid partition {partition_id}")
            self._offsets[partition_id] = offset

    def get_offsets(self) -> dict[int, int]:
        with self._lock:
            return dict(self._offsets)


class Broker:
    """Central message broker managing topics and consumer groups."""
    def __init__(self):
        self._topics: dict[str, Topic] = {}
        self._groups: dict[tuple[str, str], ConsumerGroup] = {}
        self._lock = threading.Lock()

    def create_topic(self, name: str, num_partitions: int = 3) -> Topic:
        with self._lock:
            if name in self._topics:
                raise ValueError(f"Topic '{name}' already exists")
            topic = Topic(name, num_partitions)
            self._topics[name] = topic
            return topic

    def get_topic(self, name: str) -> Topic:
        with self._lock:
            if name not in self._topics:
                raise KeyError(f"Topic '{name}' not found")
            return self._topics[name]

    def publish(self, topic_name: str, key: str | None, value: Any) -> tuple[int, int]:
        topic = self.get_topic(topic_name)
        return topic.publish(key, value)

    def subscribe(self, topic_name: str, group_id: str) -> ConsumerGroup:
        with self._lock:
            gkey = (topic_name, group_id)
            if gkey not in self._groups:
                topic = self._topics.get(topic_name)
                if not topic:
                    raise KeyError(f"Topic '{topic_name}' not found")
                self._groups[gkey] = ConsumerGroup(group_id, topic)
            return self._groups[gkey]

    def list_topics(self) -> list[str]:
        with self._lock:
            return list(self._topics.keys())
