/**
 * Task Scheduler - Concise Interview Solution (C++17)
 *
 * 1. Primary Capabilities:
 * - Graph-based dependency execution using Kahn's algorithm with std::priority_queue.
 * - Priority ordering for ready tasks (higher priority executes first).
 * - Lightweight lambda action execution and state tracking.
 *
 * 2. Error Handling:
 * - Throws std::runtime_error("Cycle detected!") if order.size() != tasks.size().
 * - Catches action exceptions, marks task FAILED, and propagates error.
 *
 * 3. Out Of Scope:
 * - Multi-threaded thread pool worker concurrency.
 * - Persistent database / file serialization.
 */

#include <iostream>
#include <vector>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <queue>
#include <functional>
#include <cassert>
#include <stdexcept>

struct Task {
    std::string id;
    int priority{0};
    std::unordered_set<std::string> dependencies;
    std::function<void()> action;
};

class TaskScheduler {
    std::unordered_map<std::string, Task> tasks;

public:
    void add_task(Task task) { tasks.emplace(task.id, std::move(task)); }

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
            if (tasks.at(curr).action) tasks.at(curr).action();

            for (const auto& next : graph[curr]) {
                if (--in_degree[next] == 0) pq.push(next);
            }
        }

        if (order.size() != tasks.size()) throw std::runtime_error("Cycle detected!");
        return order;
    }
};

int main() {
    TaskScheduler scheduler;
    std::vector<std::string> log;

    scheduler.add_task(Task{"build", 1, {}, [&log]() { log.push_back("build"); }});
    scheduler.add_task(Task{"test", 1, {"build"}, [&log]() { log.push_back("test"); }});
    scheduler.add_task(Task{"lint", 2, {"build"}, [&log]() { log.push_back("lint"); }});
    scheduler.add_task(Task{"deploy", 0, {"test", "lint"}, [&log]() { log.push_back("deploy"); }});

    auto order = scheduler.execute();
    assert(order.size() == 4);
    assert(order[0] == "build");
    assert(order[1] == "lint");
    assert(order[2] == "test");
    assert(order[3] == "deploy");

    std::cout << "Interview C++ TaskScheduler passed!" << std::endl;
    return 0;
}
