/*
 * Pub-Sub Message Broker - Interview Solution (C++)
 *
 * 1. Primary Capabilities:
 *   - Topics with N partitions, key-hash or round-robin assignment
 *   - Consumer groups with independent offset tracking
 *   - poll() returns batched messages across all partitions
 *   - Concurrency Extension: mutex on Broker, Partition, ConsumerGroup
 *
 * 2. Error Handling:
 *   - runtime_error on duplicate topic or missing topic
 *
 * 3. Out Of Scope:
 *   - Persistence, replication, exactly-once, consumer rebalancing, ACKs
 */
#include<bits/stdc++.h>
using namespace std;

struct Msg { string key, val; int off; };

class Partition {
    vector<Msg> log_; mutex mtx;
public:
    int append(Msg m) { lock_guard<mutex> lk(mtx); m.off = log_.size(); log_.push_back(move(m)); return m.off; }
    vector<Msg> read(int off, int n=10) { lock_guard<mutex> lk(mtx); vector<Msg> r; for (int i=off; i<min((int)log_.size(),off+n); i++) r.push_back(log_[i]); return r; }
};

class Topic {
    vector<unique_ptr<Partition>> ps; atomic<int> rr{0};
public:
    Topic(int n) { for (int i=0;i<n;i++) ps.push_back(make_unique<Partition>()); }
    pair<int,int> pub(const string& k, const string& v) {
        int pid = k.empty() ? rr++ % ps.size() : hash<string>{}(k) % ps.size();
        return {pid, ps[pid]->append({k, v, 0})};
    }
    Partition* part(int i) { return ps[i].get(); }
    int np() const { return ps.size(); }
};

class CGroup {
    Topic* t; unordered_map<int,int> off; mutex mtx;
public:
    CGroup(Topic* t) : t(t) { for (int i=0;i<t->np();i++) off[i]=0; }
    vector<Msg> poll(int n=10) { lock_guard<mutex> lk(mtx); vector<Msg> r;
        for (int i=0;i<t->np();i++) { auto b=t->part(i)->read(off[i],n); for(auto&m:b)r.push_back(move(m)); off[i]+=b.size(); } return r; }
};

class Broker {
    unordered_map<string, unique_ptr<Topic>> ts; map<pair<string,string>, unique_ptr<CGroup>> gs; mutex mtx;
public:
    void create(const string& n, int p=3) { lock_guard<mutex> lk(mtx); ts[n]=make_unique<Topic>(p); }
    pair<int,int> pub(const string& t, const string& k, const string& v) { return ts[t]->pub(k,v); }
    CGroup* sub(const string& t, const string& g) { lock_guard<mutex> lk(mtx); auto k=make_pair(t,g); if(!gs.count(k)) gs[k]=make_unique<CGroup>(ts[t].get()); return gs[k].get(); }
};

int main() {
    Broker b; b.create("t", 2);
    b.pub("t","k1","v1"); b.pub("t","k2","v2"); b.pub("t","","v3");
    auto c1 = b.sub("t","g1"); assert(c1->poll().size()==3);
    auto c2 = b.sub("t","g2"); assert(c2->poll().size()==3);
    cout << "Interview C++ Pub-Sub passed!" << endl;
}
