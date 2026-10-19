#include<bits/stdc++.h>
using namespace std;

// Simulates multi-process with threads (C++ has no direct multiprocessing module)
// In production, use fork() or separate executables.

enum class TaskState { PENDING, RUNNING, SUCCESS, FAILURE };

struct TaskResult {
    string task_id;
    TaskState state;
    int result;
    string error;
    int retries;
};

class ResultBackend {
    unordered_map<string, TaskResult> store;
    mutex mtx;
public:
    void put(const string& id, TaskResult r) { lock_guard<mutex> lk(mtx); store[id] = move(r); }
    TaskResult get(const string& id) { lock_guard<mutex> lk(mtx); return store[id]; }
    bool wait_for(const string& id, TaskResult& out, int timeout_ms = 10000) {
        auto deadline = chrono::steady_clock::now() + chrono::milliseconds(timeout_ms);
        while (chrono::steady_clock::now() < deadline) {
            { lock_guard<mutex> lk(mtx);
              auto it = store.find(id);
              if (it != store.end() && (it->second.state == TaskState::SUCCESS || it->second.state == TaskState::FAILURE)) {
                  out = it->second; return true; } }
            this_thread::sleep_for(chrono::milliseconds(20));
        }
        return false;
    }
};

using TaskFn = function<int(vector<int>)>;

class DistributedWorker {
    int num_workers;
    queue<tuple<string, string, vector<int>, int>> task_queue;
    mutex queue_mtx;
    condition_variable queue_cv;
    ResultBackend backend;
    unordered_map<string, TaskFn> registry;
    vector<thread> workers;
    bool shutdown_ = false;
    int task_counter = 0;
    mutex counter_mtx;

    void worker_loop() {
        while (true) {
            tuple<string, string, vector<int>, int> item;
            {
                unique_lock<mutex> lk(queue_mtx);
                queue_cv.wait(lk, [&]{ return shutdown_ || !task_queue.empty(); });
                if (shutdown_ && task_queue.empty()) return;
                item = move(task_queue.front());
                task_queue.pop();
            }
            auto& [tid, name, args, max_retries] = item;
            auto it = registry.find(name);
            if (it == registry.end()) {
                backend.put(tid, {tid, TaskState::FAILURE, 0, "Unknown task: " + name, 0});
                continue;
            }
            for (int attempt = 0; attempt <= max_retries; attempt++) {
                try {
                    backend.put(tid, {tid, TaskState::RUNNING, 0, "", attempt});
                    int result = it->second(args);
                    backend.put(tid, {tid, TaskState::SUCCESS, result, "", attempt});
                    break;
                } catch (exception& e) {
                    if (attempt == max_retries) {
                        backend.put(tid, {tid, TaskState::FAILURE, 0, e.what(), attempt});
                    } else {
                        this_thread::sleep_for(chrono::milliseconds(100 * (1 << attempt)));
                    }
                }
            }
        }
    }
public:
    DistributedWorker(int n) : num_workers(n) {}

    void register_task(const string& name, TaskFn fn) { registry[name] = move(fn); }

    void start() {
        for (int i = 0; i < num_workers; i++)
            workers.emplace_back(&DistributedWorker::worker_loop, this);
    }

    string submit(const string& name, vector<int> args = {}, int max_retries = 0) {
        string tid;
        { lock_guard<mutex> lk(counter_mtx); tid = "task_" + to_string(++task_counter); }
        backend.put(tid, {tid, TaskState::PENDING, 0, "", 0});
        { lock_guard<mutex> lk(queue_mtx); task_queue.push({tid, name, move(args), max_retries}); }
        queue_cv.notify_one();
        return tid;
    }

    bool get_result(const string& tid, TaskResult& out, int timeout_ms = 10000) {
        return backend.wait_for(tid, out, timeout_ms);
    }

    void shutdown() {
        { lock_guard<mutex> lk(queue_mtx); shutdown_ = true; }
        queue_cv.notify_all();
        for (auto& t : workers) if (t.joinable()) t.join();
    }

    ~DistributedWorker() { if (!shutdown_) shutdown(); }
};

int main() {
    DistributedWorker dw(4);
    dw.register_task("square", [](vector<int> args) { return args[0] * args[0]; });
    dw.register_task("add", [](vector<int> args) { return args[0] + args[1]; });
    dw.register_task("fail", [](vector<int>) -> int { throw runtime_error("boom"); });
    dw.register_task("slow", [](vector<int> args) {
        this_thread::sleep_for(chrono::milliseconds(50));
        return args[0] * 2;
    });
    dw.start();

    // Basic
    {
        auto tid = dw.submit("square", {7});
        TaskResult r; assert(dw.get_result(tid, r));
        assert(r.state == TaskState::SUCCESS && r.result == 49);
    }

    // Multiple
    {
        vector<string> tids;
        for (int i = 0; i < 10; i++) tids.push_back(dw.submit("square", {i}));
        for (int i = 0; i < 10; i++) {
            TaskResult r; assert(dw.get_result(tids[i], r));
            assert(r.result == i * i);
        }
    }

    // Failure
    {
        auto tid = dw.submit("fail");
        TaskResult r; assert(dw.get_result(tid, r));
        assert(r.state == TaskState::FAILURE);
    }

    // Unknown task
    {
        auto tid = dw.submit("nonexistent");
        TaskResult r; assert(dw.get_result(tid, r));
        assert(r.state == TaskState::FAILURE);
    }

    // Concurrent slow tasks
    {
        vector<string> tids;
        for (int i = 0; i < 8; i++) tids.push_back(dw.submit("slow", {i}));
        for (int i = 0; i < 8; i++) {
            TaskResult r; assert(dw.get_result(tids[i], r));
            assert(r.result == i * 2);
        }
    }

    dw.shutdown();
    cout << "Complete C++ Distributed Worker tests passed!" << endl;
}
