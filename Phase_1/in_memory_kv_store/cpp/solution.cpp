#include<bits/stdc++.h>
using namespace std;

class InMemoryKVStore {
    struct Entry {
        string value;
        optional<chrono::steady_clock::time_point> expiry;
        bool is_expired() const { return expiry && chrono::steady_clock::now() >= *expiry; }
    };
    unordered_map<string, Entry> store;
    vector<unordered_map<string, optional<Entry>>> tx_stack;
    mutable mutex mtx;  // Concurrency: thread-safe wrapper
public:
    void set(const string& key, const string& val, optional<int> ttl_sec = nullopt) {
        lock_guard<mutex> lk(mtx);
        optional<chrono::steady_clock::time_point> exp;
        if (ttl_sec) exp = chrono::steady_clock::now() + chrono::seconds(*ttl_sec);
        Entry entry{val, exp};
        if (!tx_stack.empty()) tx_stack.back()[key] = entry;
        else store[key] = entry;
    }
    optional<string> get(const string& key) {
        lock_guard<mutex> lk(mtx);
        for (auto it = tx_stack.rbegin(); it != tx_stack.rend(); ++it) {
            auto f = it->find(key);
            if (f != it->end()) {
                if (!f->second || f->second->is_expired()) return nullopt;
                return f->second->value;
            }
        }
        auto it = store.find(key);
        if (it == store.end()) return nullopt;
        if (it->second.is_expired()) { store.erase(it); return nullopt; }
        return it->second.value;
    }
    bool del(const string& key) {
        lock_guard<mutex> lk(mtx);
        // inline get check (unlocked version)
        bool exists = false;
        for (auto it = tx_stack.rbegin(); it != tx_stack.rend(); ++it) {
            auto f = it->find(key);
            if (f != it->end()) { exists = f->second.has_value() && !f->second->is_expired(); break; }
        }
        if (!exists) {
            auto it = store.find(key);
            exists = it != store.end() && !it->second.is_expired();
        }
        if (!exists) return false;
        if (!tx_stack.empty()) tx_stack.back()[key] = nullopt;
        else store.erase(key);
        return true;
    }
    void begin() { lock_guard<mutex> lk(mtx); tx_stack.emplace_back(); }
    void commit() {
        lock_guard<mutex> lk(mtx);
        if (tx_stack.empty()) throw runtime_error("No active transaction.");
        auto cur = move(tx_stack.back()); tx_stack.pop_back();
        if (!tx_stack.empty()) { for (auto& [k,v] : cur) tx_stack.back()[k] = move(v); }
        else { for (auto& [k,v] : cur) { if (!v) store.erase(k); else store[k] = move(*v); } }
    }
    void rollback() {
        lock_guard<mutex> lk(mtx);
        if (tx_stack.empty()) throw runtime_error("No active transaction.");
        tx_stack.pop_back();
    }
};

int main() {
    InMemoryKVStore kv;
    kv.set("a","10"); assert(kv.get("a").value()=="10");
    kv.begin(); kv.set("a","20"); kv.set("b","30");
    assert(kv.get("a").value()=="20"); assert(kv.get("b").value()=="30");
    kv.begin(); kv.set("a","99"); assert(kv.get("a").value()=="99");
    kv.rollback(); assert(kv.get("a").value()=="20");
    kv.commit(); assert(kv.get("a").value()=="20"); assert(kv.get("b").value()=="30");
    cout << "Complete C++ KVStore tests passed!" << endl;
}
