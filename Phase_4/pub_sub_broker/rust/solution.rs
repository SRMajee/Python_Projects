//! Pub-Sub Message Broker - Complete Solution (Rust)
//! In-memory Kafka-like broker with topics, partitions, consumer groups.
//! Concurrency: Mutex<> guards all shared state.

use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone)]
struct Message {
    key: Option<String>,
    value: String,
    partition: usize,
    offset: usize,
    timestamp: f64,
}

struct Partition {
    log: Vec<Message>,
}
impl Partition {
    fn new() -> Self { Self { log: Vec::new() } }
    fn append(&mut self, mut msg: Message) -> usize {
        msg.offset = self.log.len();
        let off = msg.offset;
        self.log.push(msg);
        off
    }
    fn read(&self, offset: usize, max_n: usize) -> Vec<Message> {
        self.log[offset..self.log.len().min(offset + max_n)].to_vec()
    }
}

struct Topic {
    name: String,
    partitions: Vec<Mutex<Partition>>,
    rr: Mutex<usize>,
}
impl Topic {
    fn new(name: &str, n: usize) -> Self {
        let parts = (0..n).map(|_| Mutex::new(Partition::new())).collect();
        Self { name: name.into(), partitions: parts, rr: Mutex::new(0) }
    }
    fn publish(&self, key: Option<&str>, value: &str) -> (usize, usize) {
        let pid = if let Some(k) = key {
            let mut h: usize = 0;
            for b in k.bytes() { h = h.wrapping_mul(31).wrapping_add(b as usize); }
            h % self.partitions.len()
        } else {
            let mut rr = self.rr.lock().unwrap();
            let p = *rr % self.partitions.len();
            *rr += 1;
            p
        };
        let ts = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs_f64();
        let msg = Message { key: key.map(|s| s.into()), value: value.into(), partition: pid, offset: 0, timestamp: ts };
        let off = self.partitions[pid].lock().unwrap().append(msg);
        (pid, off)
    }
}

struct ConsumerGroup {
    offsets: HashMap<usize, usize>,
}
impl ConsumerGroup {
    fn new(n: usize) -> Self {
        Self { offsets: (0..n).map(|i| (i, 0)).collect() }
    }
    fn poll(&mut self, topic: &Topic, max_n: usize) -> Vec<Message> {
        let mut msgs = Vec::new();
        for (pid, part) in topic.partitions.iter().enumerate() {
            let off = *self.offsets.get(&pid).unwrap();
            let batch = part.lock().unwrap().read(off, max_n);
            let count = batch.len();
            msgs.extend(batch);
            *self.offsets.get_mut(&pid).unwrap() = off + count;
        }
        msgs
    }
}

struct Broker {
    topics: HashMap<String, Arc<Topic>>,
    groups: HashMap<(String, String), Mutex<ConsumerGroup>>,
}
impl Broker {
    fn new() -> Self { Self { topics: HashMap::new(), groups: HashMap::new() } }
    fn create_topic(&mut self, name: &str, n: usize) {
        if self.topics.contains_key(name) { panic!("Topic exists"); }
        self.topics.insert(name.into(), Arc::new(Topic::new(name, n)));
    }
    fn publish(&self, topic: &str, key: Option<&str>, val: &str) -> (usize, usize) {
        self.topics.get(topic).expect("Topic not found").publish(key, val)
    }
    fn subscribe(&mut self, topic: &str, group: &str) -> &Mutex<ConsumerGroup> {
        let np = self.topics.get(topic).expect("Topic not found").partitions.len();
        let key = (topic.into(), group.into());
        self.groups.entry(key.clone()).or_insert_with(|| Mutex::new(ConsumerGroup::new(np)));
        self.groups.get(&key).unwrap()
    }
}

fn main() {
    let mut b = Broker::new();
    b.create_topic("orders", 3);
    b.publish("orders", Some("u1"), "laptop");
    b.publish("orders", Some("u2"), "phone");
    b.publish("orders", None, "misc");

    let topic = Arc::clone(b.topics.get("orders").unwrap());

    // Consumer group 1
    let cg1 = b.subscribe("orders", "analytics");
    let msgs1 = cg1.lock().unwrap().poll(&topic, 10);
    assert_eq!(msgs1.len(), 3);

    // Independent consumer group 2
    let cg2 = b.subscribe("orders", "billing");
    let msgs2 = cg2.lock().unwrap().poll(&topic, 10);
    assert_eq!(msgs2.len(), 3);

    // Key consistency
    let (p1, _) = b.publish("orders", Some("same"), "a");
    let (p2, _) = b.publish("orders", Some("same"), "b");
    assert_eq!(p1, p2);

    println!("Complete Rust Pub-Sub tests passed!");
}
