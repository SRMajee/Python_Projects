#include<bits/stdc++.h>
using namespace std;

// ── LRU Cache ──
class LRUCache {
    int cap;
    list<pair<int,int>> dll; // (key, val)
    unordered_map<int, list<pair<int,int>>::iterator> mp;
    mutex mtx;
public:
    LRUCache(int c) : cap(c) { if (c <= 0) throw invalid_argument("positive capacity required"); }

    int get(int key) {
        lock_guard<mutex> lk(mtx);
        auto it = mp.find(key);
        if (it == mp.end()) return -1;
        dll.splice(dll.begin(), dll, it->second);
        return it->second->second;
    }

    void put(int key, int val) {
        lock_guard<mutex> lk(mtx);
        auto it = mp.find(key);
        if (it != mp.end()) {
            it->second->second = val;
            dll.splice(dll.begin(), dll, it->second);
        } else {
            if ((int)mp.size() >= cap) {
                auto& back = dll.back();
                mp.erase(back.first);
                dll.pop_back();
            }
            dll.push_front({key, val});
            mp[key] = dll.begin();
        }
    }

    int size() { lock_guard<mutex> lk(mtx); return mp.size(); }
};

// ── LFU Cache ──
class LFUCache {
    int cap, min_freq;
    unordered_map<int, pair<int,int>> kv_freq; // key -> (val, freq)
    unordered_map<int, list<int>> freq_list;   // freq -> list of keys (back=LRU)
    unordered_map<int, list<int>::iterator> key_iter; // key -> iterator in freq_list
    mutex mtx;

    void touch(int key) {
        int freq = kv_freq[key].second;
        freq_list[freq].erase(key_iter[key]);
        if (freq_list[freq].empty()) {
            freq_list.erase(freq);
            if (min_freq == freq) min_freq++;
        }
        kv_freq[key].second = freq + 1;
        freq_list[freq + 1].push_front(key);
        key_iter[key] = freq_list[freq + 1].begin();
    }
public:
    LFUCache(int c) : cap(c), min_freq(0) { if (c <= 0) throw invalid_argument("positive capacity required"); }

    int get(int key) {
        lock_guard<mutex> lk(mtx);
        auto it = kv_freq.find(key);
        if (it == kv_freq.end()) return -1;
        touch(key);
        return it->second.first;
    }

    void put(int key, int val) {
        lock_guard<mutex> lk(mtx);
        if (kv_freq.count(key)) {
            kv_freq[key].first = val;
            touch(key);
            return;
        }
        if ((int)kv_freq.size() >= cap) {
            int evict = freq_list[min_freq].back();
            freq_list[min_freq].pop_back();
            if (freq_list[min_freq].empty()) freq_list.erase(min_freq);
            key_iter.erase(evict);
            kv_freq.erase(evict);
        }
        kv_freq[key] = {val, 1};
        min_freq = 1;
        freq_list[1].push_front(key);
        key_iter[key] = freq_list[1].begin();
    }
};

int main() {
    // LRU tests
    {
        LRUCache lru(2);
        lru.put(1, 10); lru.put(2, 20);
        assert(lru.get(1) == 10);
        lru.put(3, 30); // evicts 2
        assert(lru.get(2) == -1);
        assert(lru.get(3) == 30);

        // Update
        lru.put(1, 99);
        assert(lru.get(1) == 99);

        // Access refreshes
        LRUCache lru2(2);
        lru2.put(1, 10); lru2.put(2, 20);
        lru2.get(1); // refresh 1
        lru2.put(3, 30); // evicts 2
        assert(lru2.get(2) == -1);
        assert(lru2.get(1) == 10);
    }

    // LFU tests
    {
        LFUCache lfu(2);
        lfu.put(1, 10); lfu.put(2, 20);
        lfu.get(1); // freq(1)=2
        lfu.put(3, 30); // evicts 2 (freq=1)
        assert(lfu.get(2) == -1);
        assert(lfu.get(1) == 10);
        assert(lfu.get(3) == 30);

        // Tie-breaking: LRU within same freq
        LFUCache lfu2(2);
        lfu2.put(1, 10); // freq=1
        lfu2.put(2, 20); // freq=1
        lfu2.put(3, 30); // evicts 1 (LRU among freq=1)
        assert(lfu2.get(1) == -1);
    }

    // Thread safety
    {
        LRUCache lru(1000);
        vector<thread> threads;
        for (int t = 0; t < 5; t++) {
            threads.emplace_back([&lru, t] {
                for (int i = t * 100; i < t * 100 + 100; i++)
                    lru.put(i, i * 10);
            });
        }
        for (auto& t : threads) t.join();
        assert(lru.size() == 500);
    }

    cout << "Complete C++ LRU/LFU tests passed!" << endl;
}
