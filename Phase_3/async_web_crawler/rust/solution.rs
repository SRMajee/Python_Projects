//! Async Web Crawler - Complete Solution (Rust)
//! Thread-pool BFS crawler with depth limiting and deduplication.
//! Concurrency: Arc<Mutex<>> shared state with crossbeam-style worker threads.

use std::collections::{HashMap, HashSet, VecDeque};
use std::sync::{Arc, Mutex, Condvar};

#[derive(Debug, Clone)]
struct CrawlResult {
    url: String,
    status: u16,
    title: String,
    links: Vec<String>,
    error: String,
}

// Simulated page DB for testing
fn mock_pages() -> HashMap<String, (u16, String)> {
    let mut m = HashMap::new();
    m.insert("https://ex.com".into(), (200, "<title>Home</title><a href='https://ex.com/a'>a</a><a href='https://ex.com/b'>b</a>".into()));
    m.insert("https://ex.com/a".into(), (200, "<title>A</title><a href='https://ex.com'>h</a>".into()));
    m.insert("https://ex.com/b".into(), (200, "<title>B</title><a href='https://ex.com/b/c'>c</a>".into()));
    m.insert("https://ex.com/b/c".into(), (200, "<title>C</title>".into()));
    m
}

fn extract_title(html: &str) -> String {
    if let Some(s) = html.find("<title>") {
        if let Some(e) = html.find("</title>") {
            return html[s + 7..e].to_string();
        }
    }
    String::new()
}

fn extract_links(html: &str) -> Vec<String> {
    let mut links = Vec::new();
    let pat = "href='";
    let mut pos = 0;
    while let Some(s) = html[pos..].find(pat) {
        let start = pos + s + pat.len();
        if let Some(e) = html[start..].find('\'') {
            links.push(html[start..start + e].to_string());
            pos = start + e;
        } else { break; }
    }
    links
}

struct SharedState {
    queue: VecDeque<(String, u32)>,
    visited: HashSet<String>,
    results: Vec<CrawlResult>,
    active: u32,
    done: bool,
}

fn crawl(seeds: Vec<String>, max_depth: u32, max_conc: usize) -> Vec<CrawlResult> {
    let pages = mock_pages();
    let state = Arc::new((Mutex::new(SharedState {
        queue: seeds.iter().cloned().map(|u| (u.clone(), 0)).collect(),
        visited: seeds.into_iter().collect(),
        results: Vec::new(),
        active: 0,
        done: false,
    }), Condvar::new()));

    let mut handles = Vec::new();
    for _ in 0..max_conc {
        let st = Arc::clone(&state);
        let pg = pages.clone();
        handles.push(std::thread::spawn(move || {
            loop {
                let (url, depth) = {
                    let (lock, cvar) = &*st;
                    let mut s = lock.lock().unwrap();
                    loop {
                        if let Some(item) = s.queue.pop_front() {
                            s.active += 1;
                            break item;
                        }
                        if s.done { return; }
                        s = cvar.wait(s).unwrap();
                        if s.done && s.queue.is_empty() { return; }
                    }
                };

                let result = if let Some((status, html)) = pg.get(&url) {
                    CrawlResult {
                        url: url.clone(), status: *status,
                        title: extract_title(html),
                        links: extract_links(html),
                        error: String::new(),
                    }
                } else {
                    CrawlResult { url: url.clone(), status: 404, title: String::new(), links: Vec::new(), error: "not found".into() }
                };

                {
                    let (lock, cvar) = &*st;
                    let mut s = lock.lock().unwrap();
                    if depth < max_depth {
                        for link in &result.links {
                            if !s.visited.contains(link) {
                                s.visited.insert(link.clone());
                                s.queue.push_back((link.clone(), depth + 1));
                            }
                        }
                    }
                    s.results.push(result);
                    s.active -= 1;
                    if s.queue.is_empty() && s.active == 0 {
                        s.done = true;
                    }
                    cvar.notify_all();
                }
            }
        }));
    }
    // Wake workers
    state.1.notify_all();
    for h in handles { h.join().unwrap(); }
    let s = state.0.lock().unwrap();
    s.results.clone()
}

fn main() {
    // Depth 1
    let r1 = crawl(vec!["https://ex.com".into()], 1, 2);
    let urls1: HashSet<_> = r1.iter().map(|r| r.url.as_str()).collect();
    assert!(urls1.contains("https://ex.com"));
    assert!(urls1.contains("https://ex.com/a"));
    assert!(urls1.contains("https://ex.com/b"));
    assert!(!urls1.contains("https://ex.com/b/c"));

    // Depth 2
    let r2 = crawl(vec!["https://ex.com".into()], 2, 3);
    let urls2: HashSet<_> = r2.iter().map(|r| r.url.as_str()).collect();
    assert!(urls2.contains("https://ex.com/b/c"));

    // Dedup
    let r3 = crawl(vec!["https://ex.com".into()], 3, 2);
    let url_set: HashSet<_> = r3.iter().map(|r| r.url.as_str()).collect();
    assert_eq!(url_set.len(), r3.len());

    println!("Complete Rust Crawler tests passed!");
}
