#include<bits/stdc++.h>
using namespace std;

class ConsistentHashRing {
    int num_virtual;
    map<size_t, string> ring;  // sorted by hash
    set<string> nodes;
    mutex mtx;

    size_t hash_fn(const string& key) {
        // Simple FNV-1a hash
        size_t h = 14695981039346656037ULL;
        for (char c : key) { h ^= c; h *= 1099511628211ULL; }
        return h;
    }
public:
    ConsistentHashRing(int vn = 150) : num_virtual(vn) {}

    void add_node(const string& node) {
        lock_guard<mutex> lk(mtx);
        if (nodes.count(node)) throw runtime_error("Node exists");
        nodes.insert(node);
        for (int i = 0; i < num_virtual; i++) {
            size_t h = hash_fn(node + "#v" + to_string(i));
            ring[h] = node;
        }
    }

    void remove_node(const string& node) {
        lock_guard<mutex> lk(mtx);
        if (!nodes.count(node)) throw runtime_error("Node not found");
        nodes.erase(node);
        for (int i = 0; i < num_virtual; i++) {
            size_t h = hash_fn(node + "#v" + to_string(i));
            ring.erase(h);
        }
    }

    string get_node(const string& key) {
        lock_guard<mutex> lk(mtx);
        if (ring.empty()) return "";
        size_t h = hash_fn(key);
        auto it = ring.lower_bound(h);
        if (it == ring.end()) it = ring.begin();
        return it->second;
    }

    set<string> get_nodes() { lock_guard<mutex> lk(mtx); return nodes; }

    map<string, int> get_distribution(const vector<string>& keys) {
        map<string, int> dist;
        for (auto& n : nodes) dist[n] = 0;
        for (auto& k : keys) {
            string n = get_node(k);
            if (!n.empty()) dist[n]++;
        }
        return dist;
    }
};

int main() {
    ConsistentHashRing ring(100);
    ring.add_node("s1"); ring.add_node("s2"); ring.add_node("s3");

    // Basic routing
    string n = ring.get_node("my_key");
    assert(!n.empty());

    // Consistency
    assert(ring.get_node("key_a") == ring.get_node("key_a"));

    // Minimal redistribution
    vector<string> keys;
    for (int i = 0; i < 1000; i++) keys.push_back("key_" + to_string(i));
    map<string, string> before;
    for (auto& k : keys) before[k] = ring.get_node(k);
    ring.add_node("s4");
    int unchanged = 0;
    for (auto& k : keys) if (ring.get_node(k) == before[k]) unchanged++;
    assert(unchanged > 500);

    // Remove node
    ring.remove_node("s1"); ring.remove_node("s2"); ring.remove_node("s3");
    for (int i = 0; i < 100; i++) assert(ring.get_node("k" + to_string(i)) == "s4");

    // Empty ring
    ring.remove_node("s4");
    assert(ring.get_node("anything").empty());

    // Duplicate error
    ring.add_node("x");
    try { ring.add_node("x"); assert(false); } catch (...) {}

    // Thread safety
    {
        ConsistentHashRing r2(50);
        vector<thread> threads;
        for (int g = 0; g < 5; g++) {
            threads.emplace_back([&r2, g] {
                for (int i = g * 10; i < g * 10 + 10; i++)
                    try { r2.add_node("n" + to_string(i)); } catch (...) {}
            });
        }
        for (auto& t : threads) t.join();
        assert(r2.get_nodes().size() == 50);
    }

    cout << "Complete C++ Consistent Hash tests passed!" << endl;
}
