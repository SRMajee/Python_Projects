/**
 * Task Scheduler - Complete Solution with Tests (C++17)
 * Features Strategy pattern, Observer notifications, and unit test suite.
 */

#include <iostream>
#include <vector>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <queue>
#include <functional>
#include <memory>
#include <cassert>
#include <stdexcept>

enum class TaskStatus { PENDING, RUNNING, COMPLETED, FAILED };

struct Task {
    std::string id;
    int priority{0};
    std::unordered_set<std::string> dependencies;
    std::function<void()> action;
    TaskStatus status{TaskStatus::PENDING};

    Task(std::string id_, int priority_, std::unordered_set<std::string> deps, std::function<void()> act)
        : id(std::move(id_)), priority(priority_), dependencies(std::move(deps)), action(std::move(act)) {}
};

class TaskObserver {
public:
    virtual ~TaskObserver() = default;
    virtual void on_status_change(const std::string& task_id, TaskStatus old_s, TaskStatus new_s) = 0;
};

class TaskScheduler {
    std::unordered_map<std::string, Task> tasks;
    std::vector<std::shared_ptr<TaskObserver>> observers;

    void notify(const std::string& id, TaskStatus old_s, TaskStatus new_s) {
        for (auto& obs : observers) obs->on_status_change(id, old_s, new_s);
    }

public:
    void add_task(Task task) { tasks.emplace(task.id, std::move(task)); }
    void add_observer(std::shared_ptr<TaskObserver> obs) { observers.push_back(obs); }

    std::vector<std::string> execute() {
        std::unordered_map<std::string, int> in_degree;
        std::unordered_map<std::string, std::vector<std::string>> graph;

        for (const auto& [id, task] : tasks) {
            in_degree[id] = task.dependencies.size();
            for (const auto& dep : task.dependencies) graph[dep].push_back(id);
        }

        auto comp = [this](const std::string& a, const std::string& b) {
            if (tasks.at(a).priority == tasks.at(b).priority) return a > b;
            return tasks.at(a).priority < tasks.at(b).priority;
        };
        std::priority_queue<std::string, std::vector<std::string>, decltype(comp)> pq(comp);

        for (const auto& [id, deg] : in_degree) {
            if (deg == 0) pq.push(id);
        }

        std::vector<std::string> order;
        while (!pq.empty()) {
            std::string curr = pq.top();
            pq.pop();
            order.push_back(curr);

            auto& task = tasks.at(curr);
            notify(curr, task.status, TaskStatus::RUNNING);
            task.status = TaskStatus::RUNNING;

            try {
                if (task.action) task.action();
                notify(curr, task.status, TaskStatus::COMPLETED);
                task.status = TaskStatus::COMPLETED;
            } catch (...) {
                notify(curr, task.status, TaskStatus::FAILED);
                task.status = TaskStatus::FAILED;
                throw;
            }

            for (const auto& next : graph[curr]) {
                if (--in_degree[next] == 0) pq.push(next);
            }
        }

        if (order.size() != tasks.size()) throw std::runtime_error("Cycle detected in dependencies!");
        return order;
    }
};

int main() {
    TaskScheduler scheduler;
    std::vector<std::string> log;

    scheduler.add_task(Task("build", 1, {}, [&log]() { log.push_back("build"); }));
    scheduler.add_task(Task("test", 1, {"build"}, [&log]() { log.push_back("test"); }));
    scheduler.add_task(Task("lint", 2, {"build"}, [&log]() { log.push_back("lint"); }));
    scheduler.add_task(Task("deploy", 0, {"test", "lint"}, [&log]() { log.push_back("deploy"); }));

    auto order = scheduler.execute();
    assert(order.size() == 4);
    assert(order[0] == "build");
    assert(order[1] == "lint");
    assert(order[2] == "test");
    assert(order[3] == "deploy");

    std::cout << "Complete C++ TaskScheduler tests passed!" << std::endl;
    return 0;
}
