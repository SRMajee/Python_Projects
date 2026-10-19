/*
 * Async Web Crawler - Interview Solution (Rust)
 *
 * 1. Primary Capabilities:
 *   - BFS with depth limit, URL dedup via HashSet
 *   - Thread pool with Arc<Mutex<State>> + Condvar
 *   - Concurrency Extension: Condvar-based worker coordination
 *
 * 2. Error Handling:
 *   - Missing pages return 404 result, workers never panic
 *
 * 3. Out Of Scope:
 *   - Real HTTP (reqwest), robots.txt, JS rendering, polite delay
 */
use std::collections::{HashMap, HashSet, VecDeque};
use std::sync::{Arc, Mutex, Condvar};

#[derive(Debug)]
struct Result { url: String, status: u16, title: String, links: Vec<String> }

fn crawl(seeds: Vec<String>, max_d: u32, n: usize) -> Vec<Result> {
    let db: HashMap<String, (u16, String)> = [
        ("https://a.com".into(), (200u16, "<title>A</title><a href='https://a.com/b'>b</a>".into())),
        ("https://a.com/b".into(), (200u16, "<title>B</title>".into())),
    ].into();

    struct S { q: VecDeque<(String,u32)>, vis: HashSet<String>, res: Vec<Result>, act: u32, done: bool }
    let st = Arc::new((Mutex::new(S {
        q: seeds.iter().map(|u| (u.clone(), 0)).collect(),
        vis: seeds.into_iter().collect(), res: vec![], act: 0, done: false,
    }), Condvar::new()));

    let mut hs = vec![];
    for _ in 0..n {
        let s = Arc::clone(&st); let pg = db.clone();
        hs.push(std::thread::spawn(move || loop {
            let (url, d) = { let (lk, cv) = &*s; let mut g = lk.lock().unwrap();
                loop { if let Some(i) = g.q.pop_front() { g.act += 1; break i; }
                       if g.done { return; } g = cv.wait(g).unwrap(); if g.done && g.q.is_empty() { return; } } };
            let r = if let Some((st, h)) = pg.get(&url) {
                let t = h.find("<title>").and_then(|s| h.find("</title>").map(|e| h[s+7..e].to_string())).unwrap_or_default();
                let mut lks = vec![]; let p = "href='"; let mut pos = 0;
                while let Some(i) = h[pos..].find(p) { let a = pos+i+p.len();
                    if let Some(e) = h[a..].find('\'') { lks.push(h[a..a+e].into()); pos = a+e; } else { break; } }
                Result { url: url.clone(), status: *st, title: t, links: lks }
            } else { Result { url: url.clone(), status: 404, title: String::new(), links: vec![] } };
            { let (lk, cv) = &*s; let mut g = lk.lock().unwrap();
              if d < max_d { for l in &r.links { if !g.vis.contains(l) { g.vis.insert(l.clone()); g.q.push_back((l.clone(), d+1)); } } }
              g.res.push(r); g.act -= 1; if g.q.is_empty() && g.act == 0 { g.done = true; } cv.notify_all(); }
        }));
    }
    st.1.notify_all();
    for h in hs { h.join().unwrap(); }
    let g = st.0.lock().unwrap(); std::mem::drop(g);
    Arc::try_unwrap(st).ok().unwrap().0.into_inner().unwrap().res
}

fn main() {
    let r = crawl(vec!["https://a.com".into()], 1, 2);
    assert_eq!(r.len(), 2);
    println!("Interview Rust Crawler passed!");
}
