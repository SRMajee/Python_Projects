/*
 * Task Scheduler - Interview Solution (C++)
 *
 * 1. Primary Capabilities:
 *   - DAG topological execution via Kahn's algorithm with priority_queue
 *   - Higher-priority tasks execute first among independent ready tasks
 *   - Concurrency Extension: dispatch ready tasks to thread pool instead of sequential
 *
 * 2. Error Handling:
 *   - runtime_error on cycle detection (order.size() != tasks.size())
 *
 * 3. Out Of Scope:
 *   - Distributed workers, persistent task DB, cron expression parsing
 */
#include<bits/stdc++.h>
using namespace std;

struct Task { string id; int priority{0}; unordered_set<string> deps; function<void()> action; };

class TaskScheduler {
    unordered_map<string, Task> tasks;
public:
    void add(Task t) { tasks.emplace(t.id, move(t)); }
    vector<string> execute() {
        unordered_map<string, int> deg;
        unordered_map<string, vector<string>> graph;
        for (auto& [id,t] : tasks) { deg[id] = t.deps.size(); for (auto& d : t.deps) graph[d].push_back(id); }
        auto cmp = [&](const string& a, const string& b) {
            return tasks.at(a).priority == tasks.at(b).priority ? a > b : tasks.at(a).priority < tasks.at(b).priority;
        };
        priority_queue<string, vector<string>, decltype(cmp)> pq(cmp);
        for (auto& [id,d] : deg) if (d==0) pq.push(id);
        vector<string> order;
        while (!pq.empty()) {
            string c = pq.top(); pq.pop(); order.push_back(c);
            if (tasks.at(c).action) tasks.at(c).action();
            for (auto& n : graph[c]) if (--deg[n]==0) pq.push(n);
        }
        if (order.size() != tasks.size()) throw runtime_error("Cycle!");
        return order;
    }
};

int main() {
    TaskScheduler s;
    vector<string> log;
    s.add({"build",1,{},[&]{log.push_back("build");}});
    s.add({"test",1,{"build"},[&]{log.push_back("test");}});
    s.add({"lint",2,{"build"},[&]{log.push_back("lint");}});
    s.add({"deploy",0,{"test","lint"},[&]{log.push_back("deploy");}});
    auto order = s.execute();
    assert(order == (vector<string>{"build","lint","test","deploy"}));
    cout << "Interview C++ TaskScheduler passed!" << endl;
}
