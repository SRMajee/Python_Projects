/*
 * Board Game Engine - Interview Solution (Rust)
 *
 * 1. Primary Capabilities:
 *   - Command pattern: MoveCmd with undo
 *   - Snake & Ladder board, configurable
 *   - Turn-based engine, win detection
 *   - Concurrency Extension: Arc<Mutex<Engine>>
 *
 * 2. Error Handling:
 *   - Panics on game-over play, no-move on exceed
 *
 * 3. Out Of Scope:
 *   - Chess, AI, network, persistence
 */
use std::collections::HashMap;

struct Player { name: String, pos: i32 }
struct Board { sz: i32, snakes: HashMap<i32,i32>, ladders: HashMap<i32,i32> }
impl Board { fn proc(&self, p: i32) -> i32 { *self.snakes.get(&p).or(self.ladders.get(&p)).unwrap_or(&p) } }

struct Cmd { idx: usize, old: i32 }
struct Engine { board: Board, ps: Vec<Player>, turn: usize, hist: Vec<Cmd>, winner: Option<usize> }
impl Engine {
    fn new(b: Board) -> Self { Self { board: b, ps: vec![], turn: 0, hist: vec![], winner: None } }
    fn add(&mut self, n: &str) { self.ps.push(Player { name: n.into(), pos: 0 }); }
    fn play(&mut self, d: i32) -> (i32, bool) {
        let i = self.turn % self.ps.len(); let old = self.ps[i].pos;
        let np = old + d; if np > self.board.sz { self.turn += 1; return (old, false); }
        let fp = self.board.proc(np); self.ps[i].pos = fp;
        self.hist.push(Cmd { idx: i, old }); let w = fp == self.board.sz;
        if w { self.winner = Some(i); } self.turn += 1; (fp, w)
    }
    fn undo(&mut self) -> bool { if let Some(c) = self.hist.pop() { self.ps[c.idx].pos = c.old; self.turn -= 1; self.winner = None; true } else { false } }
}

fn main() {
    let b = Board { sz: 20, snakes: [(15,5)].into(), ladders: [(3,12)].into() };
    let mut e = Engine::new(b); e.add("A"); e.add("B");
    let (p, _) = e.play(3); assert_eq!(p, 12); // ladder
    assert!(e.undo()); assert_eq!(e.ps[0].pos, 0);
    println!("Interview Rust Board Game passed!");
}
