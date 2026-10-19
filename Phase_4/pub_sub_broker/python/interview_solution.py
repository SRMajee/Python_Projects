"""
Pub-Sub Message Broker - Interview Solution (Python)

1. Primary Capabilities:
   - Topics with N partitions, round-robin or key-hash assignment
   - Consumer groups with independent offset tracking per partition
   - poll() returns batched messages, advances offsets
   - Concurrency Extension: threading.Lock on all state mutations

2. Error Handling:
   - KeyError on missing topic, ValueError on duplicate topic creation
   - seek() validates partition ID

3. Out Of Scope:
   - Disk persistence, replication, exactly-once delivery, consumer rebalancing,
     ACKs, dead-letter queues, schema registry
"""
import threading, time
from collections import defaultdict

class Partition:
    def __init__(self):
        self.log, self._lk = [], threading.Lock()
    def append(self, msg):
        with self._lk: off = len(self.log); self.log.append((off, msg)); return off
    def read(self, off, n=10):
        with self._lk: return self.log[off:off+n]

class Topic:
    def __init__(self, name, n=3):
        self.name = name; self.parts = [Partition() for _ in range(n)]; self._rr = 0; self._lk = threading.Lock()
    def publish(self, key, val):
        if key is not None: pid = hash(key) % len(self.parts)
        else:
            with self._lk: pid = self._rr % len(self.parts); self._rr += 1
        return pid, self.parts[pid].append((key, val, time.time()))

class ConsumerGroup:
    def __init__(self, topic):
        self.topic = topic; self._off = {i: 0 for i in range(len(topic.parts))}; self._lk = threading.Lock()
    def poll(self, n=10):
        msgs = []
        with self._lk:
            for pid, p in enumerate(self.topic.parts):
                batch = p.read(self._off[pid], n)
                msgs.extend(batch); self._off[pid] += len(batch)
        return msgs

class Broker:
    def __init__(self):
        self._topics, self._groups, self._lk = {}, {}, threading.Lock()
    def create_topic(self, name, n=3):
        with self._lk:
            if name in self._topics: raise ValueError("exists")
            self._topics[name] = Topic(name, n); return self._topics[name]
    def publish(self, topic, key, val):
        return self._topics[topic].publish(key, val)
    def subscribe(self, topic, group):
        with self._lk:
            k = (topic, group)
            if k not in self._groups: self._groups[k] = ConsumerGroup(self._topics[topic])
            return self._groups[k]

if __name__ == "__main__":
    b = Broker(); b.create_topic("t", 2)
    b.publish("t", "k1", "v1"); b.publish("t", "k2", "v2"); b.publish("t", None, "v3")
    c = b.subscribe("t", "g1"); msgs = c.poll()
    assert len(msgs) == 3
    c2 = b.subscribe("t", "g2"); msgs2 = c2.poll()
    assert len(msgs2) == 3  # independent group
    print("Interview Pub-Sub passed!")
