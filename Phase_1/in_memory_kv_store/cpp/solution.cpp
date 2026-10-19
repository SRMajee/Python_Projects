/**
 * In-Memory Key-Value Store - Complete Solution with Tests (C++17)
 */

#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>
#include <optional>
#include <chrono>
#include <cassert>
#include <stdexcept>

class InMemoryKVStore {
    struct Entry {
        std::string value;
        std::optional<std::chrono::steady_clock::time_point> expiry;

        bool is_expired() const {
            if (!expiry.has_value()) return false;
            return std::chrono::steady_clock::now() >= expiry.value();
        }
    };

    std::unordered_map<std::string, Entry> store;
    std::vector<std::unordered_map<std::string, std::optional<Entry>>> tx_stack;

public:
    void set(const std::string& key, const std::string& val, std::optional<int> ttl_sec = std::nullopt) {
        std::optional<std::chrono::steady_clock::time_point> exp;
        if (ttl_sec.has_value()) {
            exp = std::chrono::steady_clock::now() + std::chrono::seconds(ttl_sec.value());
        }
        Entry entry{val, exp};

        if (!tx_stack.empty()) {
            tx_stack.back()[key] = entry;
        } else {
            store[key] = entry;
        }
    }

    std::optional<std::string> get(const std::string& key) {
        for (auto it = tx_stack.rbegin(); it != tx_stack.rend(); ++it) {
            auto found = it->find(key);
            if (found != it->end()) {
                if (!found->second.has_value() || found->second->is_expired()) {
                    return std::nullopt;
                }
                return found->second->value;
            }
        }
        auto it = store.find(key);
        if (it == store.end()) return std::nullopt;
        if (it->second.is_expired()) {
            store.erase(it);
            return std::nullopt;
        }
        return it->second.value;
    }

    bool del(const std::string& key) {
        if (!get(key).has_value()) return false;
        if (!tx_stack.empty()) {
            tx_stack.back()[key] = std::nullopt;
        } else {
            store.erase(key);
        }
        return true;
    }

    void begin() {
        tx_stack.emplace_back();
    }

    void commit() {
        if (tx_stack.empty()) throw std::runtime_error("No active transaction.");
        auto current_tx = std::move(tx_stack.back());
        tx_stack.pop_back();

        if (!tx_stack.empty()) {
            for (auto& [k, v] : current_tx) {
                tx_stack.back()[k] = std::move(v);
            }
        } else {
            for (auto& [k, v] : current_tx) {
                if (!v.has_value()) store.erase(k);
                else store[k] = std::move(*v);
            }
        }
    }

    void rollback() {
        if (tx_stack.empty()) throw std::runtime_error("No active transaction.");
        tx_stack.pop_back();
    }
};

int main() {
    InMemoryKVStore kv;
    kv.set("a", "10");
    assert(kv.get("a").value() == "10");

    kv.begin();
    kv.set("a", "20");
    kv.set("b", "30");
    assert(kv.get("a").value() == "20");
    assert(kv.get("b").value() == "30");

    kv.begin();
    kv.set("a", "99");
    assert(kv.get("a").value() == "99");
    kv.rollback();

    assert(kv.get("a").value() == "20");
    kv.commit();
    assert(kv.get("a").value() == "20");
    assert(kv.get("b").value() == "30");

    std::cout << "Complete C++ InMemoryKVStore tests passed!" << std::endl;
    return 0;
}
