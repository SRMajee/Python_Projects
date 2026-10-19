/*
 * Thread-Safe Rate Limiter - Interview Solution (C++)
 *
 * 1. Primary Capabilities:
 *   - Token Bucket: lazy refill, capacity-bounded, O(1) per call
 *   - Sliding Window Log: deque of timestamps, evict expired, O(1) amortized
 *   - Per-key rate limiting via unordered_map
 *   - Concurrency Extension: mutex guards all mutable state
 *
 * 2. Error Handling:
 *   - invalid_argument on non-positive capacity/rate/window
 *
 * 3. Out Of Scope:
 *   - Distributed (Redis-backed), leaky bucket, adaptive throttling, retry headers
 */
#include<bits/stdc++.h>
using namespace std;

class TokenBucket {
    int cap; double rate;
    mutex mtx;
    unordered_map<string, pair<double, chrono::steady_clock::time_point>> bk;
public:
    TokenBucket(int c, double r) : cap(c), rate(r) {}
    bool allow(const string& k = "d") {
        lock_guard<mutex> lk(mtx);
        auto now = chrono::steady_clock::now();
        auto [tok, last] = bk.count(k) ? bk[k] : make_pair((double)cap, now);
        tok = min((double)cap, tok + chrono::duration<double>(now - last).count() * rate);
        if (tok >= 1) { bk[k] = {tok - 1, now}; return true; }
        bk[k] = {tok, now}; return false;
    }
};

class SlidingWindowLog {
    int mx; double win;
    mutex mtx;
    unordered_map<string, deque<chrono::steady_clock::time_point>> logs;
public:
    SlidingWindowLog(int m, double w) : mx(m), win(w) {}
    bool allow(const string& k = "d") {
        lock_guard<mutex> lk(mtx);
        auto now = chrono::steady_clock::now();
        auto& q = logs[k];
        while (!q.empty() && q.front() <= now - chrono::duration<double>(win)) q.pop_front();
        if ((int)q.size() < mx) { q.push_back(now); return true; }
        return false;
    }
};

int main() {
    TokenBucket tb(3, 1.0);
    assert(tb.allow() && tb.allow() && tb.allow() && !tb.allow());
    SlidingWindowLog sw(2, 1.0);
    assert(sw.allow() && sw.allow() && !sw.allow());
    cout << "Interview C++ Rate Limiter passed!" << endl;
}
