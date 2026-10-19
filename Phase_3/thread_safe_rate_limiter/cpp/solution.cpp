#include<bits/stdc++.h>
using namespace std;

// ── Token Bucket ──
class TokenBucket {
    int capacity;
    double refill_rate;
    mutex mtx;
    unordered_map<string, pair<double, chrono::steady_clock::time_point>> buckets;
public:
    TokenBucket(int cap, double rate) : capacity(cap), refill_rate(rate) {
        if (cap <= 0 || rate <= 0) throw invalid_argument("positive values required");
    }
    bool allow(const string& key = "default") {
        lock_guard<mutex> lk(mtx);
        auto now = chrono::steady_clock::now();
        auto it = buckets.find(key);
        double tokens;
        chrono::steady_clock::time_point last;
        if (it == buckets.end()) {
            tokens = capacity; last = now;
        } else {
            tokens = it->second.first; last = it->second.second;
        }
        double elapsed = chrono::duration<double>(now - last).count();
        tokens = min((double)capacity, tokens + elapsed * refill_rate);
        if (tokens >= 1.0) {
            buckets[key] = {tokens - 1.0, now};
            return true;
        }
        buckets[key] = {tokens, now};
        return false;
    }
};

// ── Sliding Window Log ──
class SlidingWindowLog {
    int max_req;
    double window_sec;
    mutex mtx;
    unordered_map<string, deque<chrono::steady_clock::time_point>> logs;
public:
    SlidingWindowLog(int mx, double win) : max_req(mx), window_sec(win) {
        if (mx <= 0 || win <= 0) throw invalid_argument("positive values required");
    }
    bool allow(const string& key = "default") {
        lock_guard<mutex> lk(mtx);
        auto now = chrono::steady_clock::now();
        auto& q = logs[key];
        auto cutoff = now - chrono::duration<double>(window_sec);
        while (!q.empty() && q.front() <= cutoff) q.pop_front();
        if ((int)q.size() < max_req) {
            q.push_back(now);
            return true;
        }
        return false;
    }
};

// ── Sliding Window Counter ──
class SlidingWindowCounter {
    int max_req;
    double window_sec;
    mutex mtx;
    struct State { int prev_c=0, curr_c=0; chrono::steady_clock::time_point win_start; };
    unordered_map<string, State> states;
public:
    SlidingWindowCounter(int mx, double win) : max_req(mx), window_sec(win) {}
    bool allow(const string& key = "default") {
        lock_guard<mutex> lk(mtx);
        auto now = chrono::steady_clock::now();
        auto it = states.find(key);
        if (it == states.end()) {
            states[key] = {0, 1, now};
            return true;
        }
        auto& s = it->second;
        double elapsed = chrono::duration<double>(now - s.win_start).count();
        int windows = (int)(elapsed / window_sec);
        if (windows >= 2) { s.prev_c = 0; s.curr_c = 0; s.win_start = now; }
        else if (windows == 1) { s.prev_c = s.curr_c; s.curr_c = 0; s.win_start += chrono::duration<double>(window_sec); }
        double pos = chrono::duration<double>(now - s.win_start).count() / window_sec;
        double weight = max(0.0, 1.0 - pos);
        double est = s.prev_c * weight + s.curr_c;
        if (est < max_req) { s.curr_c++; return true; }
        return false;
    }
};

int main() {
    // Token Bucket tests
    {
        TokenBucket tb(3, 1.0);
        assert(tb.allow()); assert(tb.allow()); assert(tb.allow());
        assert(!tb.allow());
    }
    // Per-key isolation
    {
        TokenBucket tb(1, 0.1);
        assert(tb.allow("a"));
        assert(!tb.allow("a"));
        assert(tb.allow("b"));
    }
    // Sliding Window Log tests
    {
        SlidingWindowLog sw(2, 1.0);
        assert(sw.allow()); assert(sw.allow()); assert(!sw.allow());
    }
    // Sliding Window Counter tests
    {
        SlidingWindowCounter sc(3, 1.0);
        assert(sc.allow()); assert(sc.allow()); assert(sc.allow());
        assert(!sc.allow());
    }
    // Thread safety stress test
    {
        TokenBucket tb(100, 0.0);
        atomic<int> allowed{0};
        vector<thread> threads;
        for (int t = 0; t < 10; t++) {
            threads.emplace_back([&] {
                for (int i = 0; i < 20; i++) if (tb.allow()) allowed++;
            });
        }
        for (auto& t : threads) t.join();
        assert(allowed == 100);
    }
    cout << "Complete C++ Rate Limiter tests passed!" << endl;
}
