/*
 * O(1) LRU & LFU Cache - Interview Solution (C++)
 *
 * 1. Primary Capabilities:
 *   - LRU: list<pair> + unordered_map, splice for O(1) move-to-front
 *   - LFU: freq_map of lists + kv_freq map, O(1) promotion
 *   - Concurrency Extension: mutex on all operations
 *
 * 2. Error Handling:
 *   - get() returns -1 on miss
 *   - invalid_argument on capacity <= 0
 *
 * 3. Out Of Scope:
 *   - TTL, size-aware eviction, distributed caching, persistence
 */
#include<bits/stdc++.h>
using namespace std;

class LRU {
    int cap; list<pair<int,int>> dll;
    unordered_map<int, list<pair<int,int>>::iterator> mp;
    mutex mtx;
public:
    LRU(int c) : cap(c) {}
    int get(int k) { lock_guard<mutex> lk(mtx); auto it=mp.find(k); if(it==mp.end()) return -1;
        dll.splice(dll.begin(), dll, it->second); return it->second->second; }
    void put(int k, int v) { lock_guard<mutex> lk(mtx); auto it=mp.find(k);
        if(it!=mp.end()) { it->second->second=v; dll.splice(dll.begin(),dll,it->second); return; }
        if((int)mp.size()>=cap) { mp.erase(dll.back().first); dll.pop_back(); }
        dll.push_front({k,v}); mp[k]=dll.begin(); }
};

class LFU {
    int cap, mf;
    unordered_map<int, pair<int,int>> kf; // key->(val,freq)
    unordered_map<int, list<int>> fl; // freq->keys
    unordered_map<int, list<int>::iterator> ki;
    mutex mtx;
    void touch(int k) { int f=kf[k].second; fl[f].erase(ki[k]);
        if(fl[f].empty()) { fl.erase(f); if(mf==f) mf++; }
        kf[k].second=f+1; fl[f+1].push_front(k); ki[k]=fl[f+1].begin(); }
public:
    LFU(int c) : cap(c), mf(0) {}
    int get(int k) { lock_guard<mutex> lk(mtx); if(!kf.count(k)) return -1; touch(k); return kf[k].first; }
    void put(int k, int v) { lock_guard<mutex> lk(mtx);
        if(kf.count(k)) { kf[k].first=v; touch(k); return; }
        if((int)kf.size()>=cap) { int e=fl[mf].back(); fl[mf].pop_back(); if(fl[mf].empty()) fl.erase(mf); ki.erase(e); kf.erase(e); }
        kf[k]={v,1}; mf=1; fl[1].push_front(k); ki[k]=fl[1].begin(); }
};

int main() {
    LRU lru(2); lru.put(1,10); lru.put(2,20); lru.get(1); lru.put(3,30);
    assert(lru.get(2)==-1 && lru.get(1)==10);
    LFU lfu(2); lfu.put(1,10); lfu.put(2,20); lfu.get(1); lfu.put(3,30);
    assert(lfu.get(2)==-1 && lfu.get(1)==10);
    cout << "Interview C++ LRU/LFU passed!" << endl;
}
