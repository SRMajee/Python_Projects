#include<bits/stdc++.h>
using namespace std;

template<typename T>
class Future {
    T result_;
    exception_ptr exc_;
    bool done_ = false, cancelled_ = false;
    mutex mtx;
    condition_variable cv;
public:
    T get(int timeout_ms = -1) {
        unique_lock<mutex> lk(mtx);
        if (timeout_ms < 0) cv.wait(lk, [&]{ return done_ || cancelled_; });
        else if (!cv.wait_for(lk, chrono::milliseconds(timeout_ms), [&]{ return done_ || cancelled_; }))
            throw runtime_error("Timeout");
        if (cancelled_) throw runtime_error("Cancelled");
        if (exc_) rethrow_exception(exc_);
        return result_;
    }
    bool cancel() { unique_lock<mutex> lk(mtx); if (done_) return false; cancelled_ = true; cv.notify_all(); return true; }
    bool is_done() { unique_lock<mutex> lk(mtx); return done_; }
    void set_result(T val) { unique_lock<mutex> lk(mtx); result_ = move(val); done_ = true; cv.notify_all(); }
    void set_exception(exception_ptr e) { unique_lock<mutex> lk(mtx); exc_ = e; done_ = true; cv.notify_all(); }
    bool is_cancelled() { unique_lock<mutex> lk(mtx); return cancelled_; }
};

class ThreadPool {
    vector<thread> workers;
    queue<function<void()>> tasks;
    mutex mtx;
    condition_variable cv;
    bool shutdown_ = false;
public:
    ThreadPool(int n) {
        if (n <= 0) throw invalid_argument("positive workers required");
        for (int i = 0; i < n; i++) {
            workers.emplace_back([this] {
                while (true) {
                    function<void()> task;
                    {
                        unique_lock<mutex> lk(mtx);
                        cv.wait(lk, [&]{ return shutdown_ || !tasks.empty(); });
                        if (shutdown_ && tasks.empty()) return;
                        task = move(tasks.front());
                        tasks.pop();
                    }
                    task();
                }
            });
        }
    }

    template<typename F, typename... Args>
    shared_ptr<Future<invoke_result_t<F, Args...>>> submit(F&& fn, Args&&... args) {
        using R = invoke_result_t<F, Args...>;
        auto fut = make_shared<Future<R>>();
        auto task_fn = [fut, f = forward<F>(fn), ... a = forward<Args>(args)]() mutable {
            if (fut->is_cancelled()) return;
            try { fut->set_result(f(a...)); }
            catch (...) { fut->set_exception(current_exception()); }
        };
        {
            unique_lock<mutex> lk(mtx);
            if (shutdown_) throw runtime_error("Pool shut down");
            tasks.push(move(task_fn));
        }
        cv.notify_one();
        return fut;
    }

    void shutdown(bool wait = true) {
        {
            unique_lock<mutex> lk(mtx);
            shutdown_ = true;
        }
        cv.notify_all();
        if (wait) for (auto& t : workers) if (t.joinable()) t.join();
    }

    ~ThreadPool() { shutdown(); }
};

int main() {
    // Basic submit
    {
        ThreadPool pool(4);
        auto f = pool.submit([](int x) { return x * x; }, 7);
        assert(f->get() == 49);
        pool.shutdown();
    }

    // Multiple tasks
    {
        ThreadPool pool(4);
        vector<shared_ptr<Future<int>>> futures;
        for (int i = 0; i < 10; i++)
            futures.push_back(pool.submit([](int x) { return x * x; }, i));
        for (int i = 0; i < 10; i++)
            assert(futures[i]->get() == i * i);
        pool.shutdown();
    }

    // Exception propagation
    {
        ThreadPool pool(2);
        auto f = pool.submit([]() -> int { throw runtime_error("boom"); });
        try { f->get(); assert(false); } catch (runtime_error& e) { assert(string(e.what()) == "boom"); }
        pool.shutdown();
    }

    // Cancel
    {
        ThreadPool pool(1);
        auto blocker = pool.submit([] { this_thread::sleep_for(chrono::milliseconds(500)); return 0; });
        auto f = pool.submit([] { return 42; });
        f->cancel(); // may or may not succeed
        pool.shutdown();
    }

    // Concurrent stress test
    {
        ThreadPool pool(8);
        atomic<int> sum{0};
        vector<shared_ptr<Future<int>>> futures;
        for (int i = 0; i < 100; i++) {
            futures.push_back(pool.submit([&sum, i] { sum += i; return i; }));
        }
        for (auto& f : futures) f->get();
        assert(sum == 4950);
        pool.shutdown();
    }

    cout << "Complete C++ Thread Pool tests passed!" << endl;
}
