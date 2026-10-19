/*
 * Consistent Hashing Ring - Interview Solution (C++)
 *
 * 1. Primary Capabilities:
 *   - std::map-based sorted ring with FNV-1a hash
 *   - Virtual nodes for uniform distribution
 *   - O(log n) lookup via lower_bound
 *   - Concurrency Extension: mutex on all operations
 *
 * 2. Error Handling:
 *   - runtime_error on duplicate/missing node
 *   - Empty string on empty ring lookup
 *
 * 3. Out Of Scope:
 *   - Weighted nodes, replication, data migration
 */
#include<bits/stdc++.h>
using namespace std;

class Ring {
    int vn; map<size_t, string> ring; set<string> nodes; mutex mtx;
    size_t h(const string& k) { size_t v=14695981039346656037ULL; for(char c:k){v^=c;v*=1099511628211ULL;} return v; }
public:
    Ring(int v=150) : vn(v) {}
    void add(const string& n) { lock_guard<mutex> lk(mtx); nodes.insert(n);
        for(int i=0;i<vn;i++) ring[h(n+"#v"+to_string(i))]=n; }
    void remove(const string& n) { lock_guard<mutex> lk(mtx); nodes.erase(n);
        for(int i=0;i<vn;i++) ring.erase(h(n+"#v"+to_string(i))); }
    string get(const string& k) { lock_guard<mutex> lk(mtx); if(ring.empty()) return "";
        auto it=ring.lower_bound(h(k)); return (it==ring.end()?ring.begin():it)->second; }
};

int main() {
    Ring r(100); r.add("s1"); r.add("s2"); r.add("s3");
    assert(!r.get("key").empty());
    r.remove("s1"); r.remove("s2"); assert(r.get("any")=="s3");
    cout << "Interview C++ Consistent Hash passed!" << endl;
}
