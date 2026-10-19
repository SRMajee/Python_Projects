#include<bits/stdc++.h>
using namespace std;

// Simulated async web crawler using threads + queue + mutex
// Real C++ async crawling would use Boost.Asio or libcurl multi

struct CrawlResult {
    string url;
    int status;
    string title;
    vector<string> links;
    string error;
};

// Simulated page database for testing
static unordered_map<string, pair<int, string>> PAGES = {
    {"https://example.com", {200, "<title>Home</title><a href='https://example.com/about'>a</a><a href='https://example.com/blog'>b</a>"}},
    {"https://example.com/about", {200, "<title>About</title><a href='https://example.com'>h</a>"}},
    {"https://example.com/blog", {200, "<title>Blog</title><a href='https://example.com/blog/p1'>p</a>"}},
    {"https://example.com/blog/p1", {200, "<title>Post1</title>"}},
};

class AsyncWebCrawler {
    int max_depth, max_conc;
    mutex mtx;
    condition_variable cv;
    unordered_set<string> visited;
    vector<CrawlResult> results;
    queue<pair<string, int>> work_queue;
    int active_workers = 0;
    bool done = false;

    pair<int, string> fetch(const string& url) {
        // Simulate network delay
        this_thread::sleep_for(chrono::milliseconds(10));
        auto it = PAGES.find(url);
        if (it != PAGES.end()) return it->second;
        return {404, ""};
    }

    string extract_title(const string& html) {
        auto start = html.find("<title>");
        auto end = html.find("</title>");
        if (start != string::npos && end != string::npos)
            return html.substr(start + 7, end - start - 7);
        return "";
    }

    vector<string> extract_links(const string& html) {
        vector<string> links;
        string pattern = "href='";
        size_t pos = 0;
        while ((pos = html.find(pattern, pos)) != string::npos) {
            pos += pattern.size();
            size_t end = html.find("'", pos);
            if (end != string::npos)
                links.push_back(html.substr(pos, end - pos));
            pos = end;
        }
        return links;
    }

    void worker() {
        while (true) {
            string url;
            int depth;
            {
                unique_lock<mutex> lk(mtx);
                cv.wait(lk, [&] { return !work_queue.empty() || done; });
                if (done && work_queue.empty()) return;
                auto [u, d] = work_queue.front();
                work_queue.pop();
                url = u; depth = d;
                active_workers++;
            }

            CrawlResult result;
            result.url = url;
            try {
                auto [status, html] = fetch(url);
                result.status = status;
                result.title = extract_title(html);
                result.links = extract_links(html);
            } catch (exception& e) {
                result.status = 0;
                result.error = e.what();
            }

            {
                lock_guard<mutex> lk(mtx);
                results.push_back(result);
                if (depth < max_depth) {
                    for (auto& link : result.links) {
                        if (visited.find(link) == visited.end()) {
                            visited.insert(link);
                            work_queue.push({link, depth + 1});
                        }
                    }
                }
                active_workers--;
                if (work_queue.empty() && active_workers == 0) done = true;
            }
            cv.notify_all();
        }
    }

public:
    AsyncWebCrawler(int depth, int conc) : max_depth(depth), max_conc(conc) {}

    vector<CrawlResult> crawl(const vector<string>& seeds) {
        {
            lock_guard<mutex> lk(mtx);
            for (auto& u : seeds) {
                if (visited.find(u) == visited.end()) {
                    visited.insert(u);
                    work_queue.push({u, 0});
                }
            }
        }
        vector<thread> threads;
        for (int i = 0; i < max_conc; i++)
            threads.emplace_back(&AsyncWebCrawler::worker, this);
        cv.notify_all();
        for (auto& t : threads) t.join();
        return results;
    }
};

int main() {
    // Test depth=1
    {
        AsyncWebCrawler c(1, 2);
        auto results = c.crawl({"https://example.com"});
        unordered_set<string> urls;
        for (auto& r : results) urls.insert(r.url);
        assert(urls.count("https://example.com"));
        assert(urls.count("https://example.com/about"));
        assert(urls.count("https://example.com/blog"));
        assert(!urls.count("https://example.com/blog/p1"));  // depth > 1
    }
    // Test depth=2
    {
        AsyncWebCrawler c(2, 3);
        auto results = c.crawl({"https://example.com"});
        unordered_set<string> urls;
        for (auto& r : results) urls.insert(r.url);
        assert(urls.count("https://example.com/blog/p1"));
    }
    // Dedup test
    {
        AsyncWebCrawler c(3, 2);
        auto results = c.crawl({"https://example.com"});
        unordered_set<string> urls;
        for (auto& r : results) urls.insert(r.url);
        assert(urls.size() == results.size());
    }
    cout << "Complete C++ Crawler tests passed!" << endl;
}
