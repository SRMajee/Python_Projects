/*
 * Distributed Task Worker - Interview Solution (C++)
 *
 * 1. Primary Capabilities:
 *   - Worker threads + shared task queue (simulates multi-process)
 *   - Task registry, submit -> task_id, get_result(task_id)
 *   - Result backend with wait_for polling
 *   - Retry with exponential backoff
 *   - Concurrency: mutex + condition_variable coordination
 *
 * 2. Error Handling:
 *   - Exception captured, stored as FAILURE in backend
 *   - Unknown task -> FAILURE
 *
 * 3. Out Of Scope:
 *   - Real IPC (fork), Redis broker, task chaining, periodic tasks
 */
#include<bits/stdc++.h>
using namespace std;

enum class TS { PENDING, SUCCESS, FAILURE };
struct Res { TS state; int val; string err; };

using TFn = function<int(vector<int>)>;

class DW {
    unordered_map<string, TFn> reg;
    queue<tuple<string,string,vector<int>,int>> q;
    unordered_map<string, Res> rs;
    mutex qm, rm; condition_variable cv;
    vector<thread> ws; bool shut=false; int tc=0;
    void work() { while(true) {
        tuple<string,string,vector<int>,int> item;
        { unique_lock<mutex> lk(qm); cv.wait(lk,[&]{return shut||!q.empty();}); if(shut&&q.empty()) return;
          item=move(q.front()); q.pop(); }
        auto& [tid,name,args,retry] = item;
        auto it=reg.find(name);
        if(it==reg.end()) { lock_guard<mutex> lk(rm); rs[tid]={TS::FAILURE,0,"Unknown: "+name}; continue; }
        for(int a=0;a<=retry;a++) {
            try { int r=it->second(args); { lock_guard<mutex> lk(rm); rs[tid]={TS::SUCCESS,r,""}; } break; }
            catch(exception& e) { if(a==retry) { lock_guard<mutex> lk(rm); rs[tid]={TS::FAILURE,0,e.what()}; }
                else this_thread::sleep_for(chrono::milliseconds(100*(1<<a))); }
        }
    }}
public:
    DW(int n) { for(int i=0;i<n;i++) ws.emplace_back(&DW::work, this); }
    void reg_task(const string& n, TFn f) { reg[n]=move(f); }
    string submit(const string& n, vector<int> a={}, int retry=0) {
        string tid="t"+to_string(++tc);
        { lock_guard<mutex> lk(rm); rs[tid]={TS::PENDING,0,""}; }
        { lock_guard<mutex> lk(qm); q.push({tid,n,move(a),retry}); } cv.notify_one(); return tid; }
    Res result(const string& tid, int tms=10000) {
        auto dl=chrono::steady_clock::now()+chrono::milliseconds(tms);
        while(chrono::steady_clock::now()<dl) { { lock_guard<mutex> lk(rm); auto it=rs.find(tid);
            if(it!=rs.end()&&it->second.state!=TS::PENDING) return it->second; }
            this_thread::sleep_for(chrono::milliseconds(20)); }
        return {TS::FAILURE,0,"timeout"}; }
    void shutdown() { {lock_guard<mutex> lk(qm); shut=true;} cv.notify_all(); for(auto&t:ws) if(t.joinable()) t.join(); }
    ~DW() { if(!shut) shutdown(); }
};

int main() {
    DW dw(2); dw.reg_task("sq", [](vector<int> a){return a[0]*a[0];});
    auto tid = dw.submit("sq", {7}); auto r = dw.result(tid);
    assert(r.state==TS::SUCCESS && r.val==49);
    auto tid2 = dw.submit("bad"); auto r2 = dw.result(tid2);
    assert(r2.state==TS::FAILURE);
    dw.shutdown();
    cout << "Interview C++ Distributed Worker passed!" << endl;
}
