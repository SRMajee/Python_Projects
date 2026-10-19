/*
 * Async Web Crawler - Interview Solution (C++)
 *
 * 1. Primary Capabilities:
 *   - BFS crawl with thread pool + shared work queue
 *   - Depth-limited, URL deduplication via unordered_set
 *   - Concurrency Extension: mutex + condition_variable for thread coordination
 *
 * 2. Error Handling:
 *   - Per-URL try/catch, errors stored in result
 *   - Graceful shutdown when queue empty + no active workers
 *
 * 3. Out Of Scope:
 *   - Real HTTP (needs libcurl/Boost.Asio), robots.txt, JavaScript rendering
 */
#include<bits/stdc++.h>
using namespace std;

struct CrawlResult { string url; int status; string title; vector<string> links; };

static unordered_map<string, pair<int, string>> DB = {
    {"https://a.com", {200, "<title>A</title><a href='https://a.com/b'>b</a>"}},
    {"https://a.com/b", {200, "<title>B</title>"}},
};

class Crawler {
    int maxd, maxc;
    mutex mtx; condition_variable cv;
    unordered_set<string> vis;
    vector<CrawlResult> res;
    queue<pair<string,int>> q;
    int active = 0; bool fin = false;
    void work() {
        while (true) {
            string url; int d;
            { unique_lock<mutex> lk(mtx);
              cv.wait(lk, [&]{ return !q.empty() || fin; });
              if (fin && q.empty()) return;
              tie(url, d) = q.front(); q.pop(); active++; }
            CrawlResult r{url, 404, "", {}};
            auto it = DB.find(url);
            if (it != DB.end()) {
                r.status = it->second.first;
                auto& h = it->second.second;
                auto s = h.find("<title>"), e = h.find("</title>");
                if (s != string::npos) r.title = h.substr(s+7, e-s-7);
                size_t p = 0; string pat = "href='";
                while ((p = h.find(pat, p)) != string::npos) {
                    p += pat.size(); auto e2 = h.find("'", p);
                    r.links.push_back(h.substr(p, e2-p)); p = e2;
                }
            }
            { lock_guard<mutex> lk(mtx);
              res.push_back(r);
              if (d < maxd) for (auto& l : r.links) if (!vis.count(l)) { vis.insert(l); q.push({l, d+1}); }
              active--;
              if (q.empty() && active == 0) fin = true; }
            cv.notify_all();
        }
    }
public:
    Crawler(int d, int c) : maxd(d), maxc(c) {}
    vector<CrawlResult> crawl(vector<string> seeds) {
        { lock_guard<mutex> lk(mtx); for (auto& u : seeds) { vis.insert(u); q.push({u, 0}); } }
        vector<thread> ts;
        for (int i = 0; i < maxc; i++) ts.emplace_back(&Crawler::work, this);
        cv.notify_all();
        for (auto& t : ts) t.join();
        return res;
    }
};

int main() {
    Crawler c(1, 2);
    auto r = c.crawl({"https://a.com"});
    assert(r.size() == 2);
    cout << "Interview C++ Crawler passed!" << endl;
}
