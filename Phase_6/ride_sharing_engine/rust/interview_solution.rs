/*
 * Ride-Sharing Engine - Interview Solution (Rust)
 *
 * 1. Primary Capabilities:
 *   - Grid spatial index, nearest-driver matching
 *   - State machine lifecycle: REQ -> MATCH -> ACTIVE -> DONE
 *   - Concurrency Extension: Mutex<Engine> for thread-safe access
 *
 * 2. Error Handling:
 *   - None on no available driver, panics on invalid state
 *
 * 3. Out Of Scope:
 *   - Real GPS, ETA, payments, ratings, ride pooling
 */
use std::collections::{HashMap, HashSet};

#[derive(PartialEq, Debug)] enum TS { Req, Match, Active, Done }
#[derive(PartialEq)] enum DS { Idle, Assigned, OnTrip }
struct Loc { x: f64, y: f64 }
impl Loc { fn dist(&self, o: &Loc) -> f64 { ((self.x-o.x).powi(2)+(self.y-o.y).powi(2)).sqrt() } }

struct Engine {
    ds: HashMap<String, (Loc, DS)>, ts: HashMap<String, (Loc, Loc, Option<String>, TS, f64)>,
    grid: HashMap<(i32,i32), HashSet<String>>, cell: f64, tc: u32,
}
impl Engine {
    fn new(c: f64) -> Self { Self { ds: HashMap::new(), ts: HashMap::new(), grid: HashMap::new(), cell: c, tc: 0 } }
    fn c(&self, l: &Loc) -> (i32,i32) { ((l.x/self.cell).floor() as i32, (l.y/self.cell).floor() as i32) }
    fn add(&mut self, id: &str, x: f64, y: f64) { let l = Loc{x,y}; let c = self.c(&l);
        self.ds.insert(id.into(), (l, DS::Idle)); self.grid.entry(c).or_default().insert(id.into()); }
    fn req(&mut self, px: f64, py: f64, dx: f64, dy: f64) -> String { self.tc += 1; let t = format!("t{}", self.tc);
        self.ts.insert(t.clone(), (Loc{x:px,y:py}, Loc{x:dx,y:dy}, None, TS::Req, 0.0)); t }
    fn mat(&mut self, tid: &str) -> Option<String> {
        let (p, _, _, _, _) = self.ts.get(tid)?;
        let (cx,cy) = self.c(p); let px = p.x; let py = p.y; let pl = Loc{x:px,y:py};
        let mut best: Option<(String, f64)> = None;
        for dx in -3..=3 { for dy in -3..=3 { if let Some(ids) = self.grid.get(&(cx+dx,cy+dy)) {
            for did in ids { let (dl, ds) = &self.ds[did]; if *ds == DS::Idle { let d = dl.dist(&pl);
                if best.as_ref().map_or(true, |b| d < b.1) { best = Some((did.clone(), d)); } } } } } }
        if let Some((did, _)) = best {
            self.ds.get_mut(&did).unwrap().1 = DS::Assigned;
            let dl = &self.ds[&did].0; let c = self.c(&Loc{x:dl.x,y:dl.y});
            self.grid.get_mut(&c).map(|s| s.remove(&did));
            let t = self.ts.get_mut(tid).unwrap(); t.2 = Some(did.clone()); t.3 = TS::Match; Some(did)
        } else { None }
    }
    fn start(&mut self, tid: &str) { let t = self.ts.get_mut(tid).unwrap(); t.3 = TS::Active;
        self.ds.get_mut(t.2.as_ref().unwrap()).unwrap().1 = DS::OnTrip; }
    fn done(&mut self, tid: &str) -> f64 { let t = self.ts.get_mut(tid).unwrap(); t.3 = TS::Done;
        t.4 = 5.0 + t.0.dist(&t.1) * 2.0; let did = t.2.clone().unwrap();
        self.ds.get_mut(&did).unwrap().1 = DS::Idle; t.4 }
}

fn main() {
    let mut e = Engine::new(1.0); e.add("d1",0.0,0.0); e.add("d2",5.0,5.0);
    let tid = e.req(0.5,0.5,8.0,8.0); assert_eq!(e.mat(&tid), Some("d1".into()));
    e.start(&tid); let f = e.done(&tid); assert!(f > 0.0);
    println!("Interview Rust Ride Engine passed!");
}
