/*
 * In-Memory KV Store - Interview Solution (C++)
 *
 * 1. Primary Capabilities:
 *   - Hash-map backed set/get/delete with nested transaction stack
 *   - begin/commit/rollback with diff-frame isolation (tombstone deletes)
 *   - Concurrency Extension: wrap with mutex or shared_mutex for thread-safe access
 *
 * 2. Error Handling:
 *   - commit/rollback on empty stack throws runtime_error
 *   - Tombstoned keys (nullopt) mask parent/base values
 *
 * 3. Out Of Scope:
 *   - TTL expiration, AOF/RDB persistence, RESP protocol, LRU eviction
 */
#include<bits/stdc++.h>
using namespace std;

class KVStore {
    unordered_map<string, string> store;
    vector<unordered_map<string, optional<string>>> tx;
public:
    void set(const string& k, const string& v) {
        if (!tx.empty()) tx.back()[k] = v;
        else store[k] = v;
    }
    optional<string> get(const string& k) {
        for (auto it = tx.rbegin(); it != tx.rend(); ++it) {
            auto f = it->find(k);
            if (f != it->end()) return f->second;
        }
        auto it = store.find(k);
        return it != store.end() ? optional(it->second) : nullopt;
    }
    bool del(const string& k) {
        if (!get(k)) return false;
        if (!tx.empty()) tx.back()[k] = nullopt;
        else store.erase(k);
        return true;
    }
    void begin() { tx.emplace_back(); }
    void commit() {
        if (tx.empty()) throw runtime_error("No transaction");
        auto top = move(tx.back()); tx.pop_back();
        if (!tx.empty()) for (auto& [k,v] : top) tx.back()[k] = move(v);
        else for (auto& [k,v] : top) { if (v) store[k] = *v; else store.erase(k); }
    }
    void rollback() {
        if (tx.empty()) throw runtime_error("No transaction");
        tx.pop_back();
    }
};

int main() {
    KVStore kv;
    kv.set("a","1"); assert(kv.get("a")=="1");
    kv.begin(); kv.set("a","2"); assert(kv.get("a")=="2");
    kv.rollback(); assert(kv.get("a")=="1");
    kv.begin(); kv.set("a","3"); kv.commit(); assert(kv.get("a")=="3");
    kv.begin(); kv.set("b","4"); kv.begin(); kv.del("b"); assert(!kv.get("b"));
    kv.rollback(); assert(kv.get("b")=="4"); kv.commit(); assert(kv.get("b")=="4");
    cout << "Interview C++ KVStore passed!" << endl;
}
