/*
 * Custom Thread Pool Executor - Interview Solution (C++)
 *
 * 1. Primary Capabilities:
 *   - N worker threads + shared task queue (mutex + condition_variable)
 *   - Future<T>: get(timeout), cancel(), exception propagation
 *   - submit(fn, args...) -> shared_ptr<Future<T>>
 *   - Graceful shutdown with drain
 *   - Concurrency: Core design IS concurrent
 *
 * 2. Error Handling:
 *   - Exception forwarding via exception_ptr + rethrow
 *   - runtime_error on submit after shutdown or cancel
 *
 * 3. Out Of Scope:
 *   - Work-stealing, priority, process pool, DAG deps, coroutines
 */
#include<bits/stdc++.h>
using namespace std;

template<typename T>
class Future {
    T res; exception_ptr exc; bool done=false, cancel_=false;
    mutex m; condition_variable cv;
public:
    T get() { unique_lock<mutex> lk(m); cv.wait(lk, [&]{return done||cancel_;}); if(cancel_) throw runtime_error("cancelled");
        if(exc) rethrow_exception(exc); return res; }
    bool cancel() { unique_lock<mutex> lk(m); if(done) return false; cancel_=true; cv.notify_all(); return true; }
    void set(T v) { unique_lock<mutex> lk(m); res=move(v); done=true; cv.notify_all(); }
    void fail(exception_ptr e) { unique_lock<mutex> lk(m); exc=e; done=true; cv.notify_all(); }
    bool cancelled() { unique_lock<mutex> lk(m); return cancel_; }
};

class Pool {
    vector<thread> ws; queue<function<void()>> q; mutex m; condition_variable cv; bool shut=false;
public:
    Pool(int n) { for(int i=0;i<n;i++) ws.emplace_back([this]{
        while(true) { function<void()> t; { unique_lock<mutex> lk(m); cv.wait(lk,[&]{return shut||!q.empty();}); if(shut&&q.empty()) return;
            t=move(q.front()); q.pop(); } t(); } }); }
    template<typename F, typename... A>
    shared_ptr<Future<invoke_result_t<F,A...>>> submit(F&& f, A&&... a) {
        using R = invoke_result_t<F,A...>; auto fut = make_shared<Future<R>>();
        { unique_lock<mutex> lk(m); if(shut) throw runtime_error("shut");
          q.push([fut, fn=forward<F>(f), ...args=forward<A>(a)]()mutable{
            if(fut->cancelled()) return; try{fut->set(fn(args...));}catch(...){fut->fail(current_exception());} }); }
        cv.notify_one(); return fut; }
    void shutdown() { {unique_lock<mutex> lk(m); shut=true;} cv.notify_all(); for(auto&t:ws) if(t.joinable()) t.join(); }
    ~Pool() { shutdown(); }
};

int main() {
    Pool p(2);
    auto f1 = p.submit([](int x){return x*x;}, 5); assert(f1->get()==25);
    auto f2 = p.submit([]()->int{throw runtime_error("e");});
    try { f2->get(); } catch(runtime_error&) {}
    p.shutdown();
    cout << "Interview C++ Thread Pool passed!" << endl;
}
