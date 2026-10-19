#include<bits/stdc++.h>
using namespace std;

struct Message {
    string key;
    string value;
    double timestamp;
    int partition;
    int offset;
};

class Partition {
    vector<Message> log_;
    mutex mtx;
public:
    int append(Message msg) {
        lock_guard<mutex> lk(mtx);
        msg.offset = log_.size();
        log_.push_back(move(msg));
        return msg.offset;
    }
    vector<Message> read(int offset, int max_n = 10) {
        lock_guard<mutex> lk(mtx);
        vector<Message> result;
        for (int i = offset; i < min((int)log_.size(), offset + max_n); i++)
            result.push_back(log_[i]);
        return result;
    }
    int size() { lock_guard<mutex> lk(mtx); return log_.size(); }
};

class Topic {
    string name_;
    vector<unique_ptr<Partition>> parts_;
    atomic<int> rr_{0};
public:
    Topic(const string& name, int n) : name_(name) {
        for (int i = 0; i < n; i++) parts_.push_back(make_unique<Partition>());
    }
    pair<int, int> publish(const string& key, const string& val) {
        int pid;
        if (!key.empty()) pid = hash<string>{}(key) % parts_.size();
        else pid = rr_++ % parts_.size();
        Message msg{key, val, (double)chrono::system_clock::now().time_since_epoch().count(), pid, 0};
        int off = parts_[pid]->append(move(msg));
        return {pid, off};
    }
    Partition* partition(int i) { return parts_[i].get(); }
    int num_partitions() const { return parts_.size(); }
    const string& name() const { return name_; }
};

class ConsumerGroup {
    Topic* topic_;
    unordered_map<int, int> offsets_;
    mutex mtx;
public:
    ConsumerGroup(Topic* t) : topic_(t) {
        for (int i = 0; i < t->num_partitions(); i++) offsets_[i] = 0;
    }
    vector<Message> poll(int max_n = 10) {
        lock_guard<mutex> lk(mtx);
        vector<Message> result;
        for (int pid = 0; pid < topic_->num_partitions(); pid++) {
            auto batch = topic_->partition(pid)->read(offsets_[pid], max_n);
            for (auto& m : batch) result.push_back(move(m));
            offsets_[pid] += batch.size();
        }
        return result;
    }
    void seek(int pid, int off) {
        lock_guard<mutex> lk(mtx);
        offsets_[pid] = off;
    }
};

class Broker {
    unordered_map<string, unique_ptr<Topic>> topics_;
    map<pair<string,string>, unique_ptr<ConsumerGroup>> groups_;
    mutex mtx;
public:
    Topic* create_topic(const string& name, int n = 3) {
        lock_guard<mutex> lk(mtx);
        if (topics_.count(name)) throw runtime_error("Topic exists");
        topics_[name] = make_unique<Topic>(name, n);
        return topics_[name].get();
    }
    pair<int,int> publish(const string& topic, const string& key, const string& val) {
        lock_guard<mutex> lk(mtx);
        auto it = topics_.find(topic);
        if (it == topics_.end()) throw runtime_error("Topic not found");
        return it->second->publish(key, val);
    }
    ConsumerGroup* subscribe(const string& topic, const string& group) {
        lock_guard<mutex> lk(mtx);
        auto gk = make_pair(topic, group);
        if (!groups_.count(gk)) {
            auto it = topics_.find(topic);
            if (it == topics_.end()) throw runtime_error("Topic not found");
            groups_[gk] = make_unique<ConsumerGroup>(it->second.get());
        }
        return groups_[gk].get();
    }
};

int main() {
    Broker b;
    b.create_topic("orders", 3);
    b.publish("orders", "u1", "laptop");
    b.publish("orders", "u2", "phone");
    b.publish("orders", "", "misc");

    auto cg1 = b.subscribe("orders", "analytics");
    auto msgs1 = cg1->poll();
    assert(msgs1.size() == 3);

    // Independent consumer group
    auto cg2 = b.subscribe("orders", "billing");
    auto msgs2 = cg2->poll();
    assert(msgs2.size() == 3);

    // Offset tracking
    b.publish("orders", "k", "v1");
    b.publish("orders", "k", "v2");
    auto cg3 = b.subscribe("orders", "tracker");
    auto batch1 = cg3->poll(2);
    auto batch2 = cg3->poll(10);
    assert(batch1.size() + batch2.size() == 5);

    // Key partitioning consistency
    auto [p1, _1] = b.publish("orders", "same", "a");
    auto [p2, _2] = b.publish("orders", "same", "b");
    assert(p1 == p2);

    // Duplicate topic error
    try { b.create_topic("orders"); assert(false); } catch (runtime_error&) {}

    // Thread safety
    {
        atomic<int> total{0};
        vector<thread> threads;
        for (int t = 0; t < 4; t++) {
            threads.emplace_back([&b, t] {
                for (int i = 0; i < 50; i++)
                    b.publish("orders", "", "p" + to_string(t) + "_" + to_string(i));
            });
        }
        for (auto& t : threads) t.join();
    }

    cout << "Complete C++ Pub-Sub tests passed!" << endl;
}
