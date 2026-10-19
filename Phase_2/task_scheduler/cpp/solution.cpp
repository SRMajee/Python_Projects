#include<bits/stdc++.h>
using namespace std;

enum class TaskStatus { PENDING, RUNNING, COMPLETED, FAILED };

struct Task {
    string id; int priority{0}; unordered_set<string> dependencies;
    function<void()> action; TaskStatus status{TaskStatus::PENDING};
    Task(string id_, int p, unordered_set<string> d, function<void()> a)
        : id(move(id_)), priority(p), dependencies(move(d)), action(move(a)) {}
};

class TaskObserver {
public:
    virtual ~TaskObserver() = default;
    virtual void on_status_change(const string& id, TaskStatus old_s, TaskStatus new_s) = 0;
};

class TaskScheduler {
    unordered_map<string, Task> tasks;
    vector<shared_ptr<TaskObserver>> observers;
    void notify(const string& id, TaskStatus o, TaskStatus n) { for (auto& obs : observers) obs->on_status_change(id,o,n); }
public:
    void add_task(Task t) { tasks.emplace(t.id, move(t)); }
    void add_observer(shared_ptr<TaskObserver> o) { observers.push_back(o); }
    vector<string> execute() {
        unordered_map<string, int> deg;
        unordered_map<string, vector<string>> graph;
        for (auto& [id,t] : tasks) { deg[id]=t.dependencies.size(); for (auto& d:t.dependencies) graph[d].push_back(id); }
        auto cmp = [&](const string& a, const string& b) {
            return tasks.at(a).priority==tasks.at(b).priority ? a>b : tasks.at(a).priority<tasks.at(b).priority;
        };
        priority_queue<string, vector<string>, decltype(cmp)> pq(cmp);
        for (auto& [id,d]:deg) if (d==0) pq.push(id);
        vector<string> order;
        while (!pq.empty()) {
            string c = pq.top(); pq.pop(); order.push_back(c);
            auto& task = tasks.at(c);
            notify(c, task.status, TaskStatus::RUNNING); task.status = TaskStatus::RUNNING;
            try {
                if (task.action) task.action();
                notify(c, task.status, TaskStatus::COMPLETED); task.status = TaskStatus::COMPLETED;
            } catch (...) {
                notify(c, task.status, TaskStatus::FAILED); task.status = TaskStatus::FAILED; throw;
            }
            for (auto& n:graph[c]) if (--deg[n]==0) pq.push(n);
        }
        if (order.size()!=tasks.size()) throw runtime_error("Cycle detected!");
        return order;
    }
};

int main() {
    TaskScheduler s;
    vector<string> log;
    s.add_task(Task("build",1,{},[&]{log.push_back("build");}));
    s.add_task(Task("test",1,{"build"},[&]{log.push_back("test");}));
    s.add_task(Task("lint",2,{"build"},[&]{log.push_back("lint");}));
    s.add_task(Task("deploy",0,{"test","lint"},[&]{log.push_back("deploy");}));
    auto order = s.execute();
    assert(order.size()==4); assert(order[0]=="build"); assert(order[1]=="lint");
    assert(order[2]=="test"); assert(order[3]=="deploy");
    cout << "Complete C++ TaskScheduler tests passed!" << endl;
}
