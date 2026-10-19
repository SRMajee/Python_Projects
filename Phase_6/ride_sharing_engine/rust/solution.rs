//! Ride-Sharing Engine - Complete Solution (Rust)
//! Grid-based spatial matching with state machine trip lifecycle.
//! Concurrency: Mutex wraps engine state for thread-safe operations.

use std::collections::{HashMap, HashSet};
use std::sync::Mutex;

#[derive(Debug, Clone, Copy, PartialEq)]
enum TripState { Requested, Matched, InProgress, Completed, Cancelled }
#[derive(Debug, Clone, Copy, PartialEq)]
enum DriverState { Idle, Assigned, OnTrip }

#[derive(Debug, Clone, Copy)]
struct Loc { x: f64, y: f64 }
impl Loc { fn dist(&self, o: &Loc) -> f64 { ((self.x-o.x).powi(2) + (self.y-o.y).powi(2)).sqrt() } }

#[derive(Debug, Clone)]
struct Driver { id: String, loc: Loc, state: DriverState }
#[derive(Debug, Clone)]
struct Trip { id: String, pickup: Loc, dropoff: Loc, driver_id: Option<String>, state: TripState, fare: f64 }

struct Engine {
    drivers: HashMap<String, Driver>,
    trips: HashMap<String, Trip>,
    grid: HashMap<(i32,i32), HashSet<String>>,
    cell: f64,
    tc: u32,
}

impl Engine {
    fn new(cell: f64) -> Mutex<Self> {
        Mutex::new(Self { drivers: HashMap::new(), trips: HashMap::new(), grid: HashMap::new(), cell, tc: 0 })
    }
    fn cell_of(&self, l: &Loc) -> (i32,i32) { ((l.x/self.cell).floor() as i32, (l.y/self.cell).floor() as i32) }

    fn add_driver(&mut self, id: &str, x: f64, y: f64) {
        let loc = Loc{x,y}; let c = self.cell_of(&loc);
        self.drivers.insert(id.into(), Driver{id:id.into(), loc, state: DriverState::Idle});
        self.grid.entry(c).or_default().insert(id.into());
    }
    fn request(&mut self, px: f64, py: f64, dx: f64, dy: f64) -> String {
        self.tc += 1; let tid = format!("t{}", self.tc);
        self.trips.insert(tid.clone(), Trip{id:tid.clone(), pickup:Loc{x:px,y:py}, dropoff:Loc{x:dx,y:dy}, driver_id:None, state:TripState::Requested, fare:0.0});
        tid
    }
    fn match_driver(&mut self, tid: &str, max_dist: f64) -> Option<String> {
        let trip = self.trips.get(tid)?;
        let (cx, cy) = self.cell_of(&trip.pickup);
        let pickup = trip.pickup;
        let mut best: Option<(String, f64)> = None;
        for dx in -3..=3 { for dy in -3..=3 {
            if let Some(ids) = self.grid.get(&(cx+dx, cy+dy)) {
                for did in ids {
                    let d = &self.drivers[did];
                    if d.state == DriverState::Idle {
                        let dist = d.loc.dist(&pickup);
                        if dist <= max_dist && best.as_ref().map_or(true, |b| dist < b.1) {
                            best = Some((did.clone(), dist));
                        }
                    }
                }
            }
        }}
        if let Some((did, _)) = best {
            self.drivers.get_mut(&did).unwrap().state = DriverState::Assigned;
            let dloc = self.drivers[&did].loc;
            let c = self.cell_of(&dloc);
            self.grid.get_mut(&c).map(|s| s.remove(&did));
            let trip = self.trips.get_mut(tid).unwrap();
            trip.driver_id = Some(did.clone()); trip.state = TripState::Matched;
            Some(did)
        } else { None }
    }
    fn start(&mut self, tid: &str) {
        let t = self.trips.get_mut(tid).unwrap(); t.state = TripState::InProgress;
        self.drivers.get_mut(t.driver_id.as_ref().unwrap()).unwrap().state = DriverState::OnTrip;
    }
    fn complete(&mut self, tid: &str) -> f64 {
        let t = self.trips.get_mut(tid).unwrap(); t.state = TripState::Completed;
        let dist = t.pickup.dist(&t.dropoff); t.fare = 5.0 + dist * 2.0;
        let did = t.driver_id.clone().unwrap(); let dropoff = t.dropoff;
        let d = self.drivers.get_mut(&did).unwrap();
        d.state = DriverState::Idle; d.loc = dropoff;
        let c = ((dropoff.x / self.cell).floor() as i32, (dropoff.y / self.cell).floor() as i32);
        self.grid.entry(c).or_default().insert(did);
        t.fare
    }
}

fn main() {
    let eng = Engine::new(1.0);
    let mut e = eng.lock().unwrap();
    e.add_driver("d1", 0.0, 0.0); e.add_driver("d2", 5.0, 5.0);
    let tid = e.request(0.5, 0.5, 8.0, 8.0);
    let d = e.match_driver(&tid, 10.0); assert_eq!(d, Some("d1".into()));
    e.start(&tid);
    let fare = e.complete(&tid); assert!(fare > 0.0);
    assert_eq!(e.trips[&tid].state, TripState::Completed);

    // No match
    let tid2 = e.request(100.0, 100.0, 200.0, 200.0);
    assert!(e.match_driver(&tid2, 5.0).is_none());

    drop(e);

    // Thread safety
    use std::sync::Arc;
    let eng2 = Arc::new(Engine::new(1.0));
    { let mut e = eng2.lock().unwrap(); for i in 0..20 { e.add_driver(&format!("td{}", i), i as f64, i as f64); } }
    let mut handles = vec![];
    let matched = Arc::new(std::sync::atomic::AtomicU32::new(0));
    for i in 0..10 {
        let ec = Arc::clone(&eng2); let mc = Arc::clone(&matched);
        handles.push(std::thread::spawn(move || {
            let mut e = ec.lock().unwrap();
            let tid = e.request(i as f64, i as f64, (i+5) as f64, (i+5) as f64);
            if e.match_driver(&tid, 5.0).is_some() { mc.fetch_add(1, std::sync::atomic::Ordering::Relaxed); }
        }));
    }
    for h in handles { h.join().unwrap(); }
    assert!(matched.load(std::sync::atomic::Ordering::Relaxed) > 0);
    println!("Complete Rust Ride Engine tests passed!");
}
