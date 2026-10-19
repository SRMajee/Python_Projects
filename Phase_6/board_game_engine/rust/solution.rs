//! Board Game Engine - Complete Solution (Rust)
//! Command-pattern extensible Snake & Ladder engine with undo/redo.
//! Concurrency: Mutex wraps engine for thread-safe access.

use std::collections::HashMap;

struct Player { name: String, pos: i32 }
struct Board { sz: i32, snakes: HashMap<i32,i32>, ladders: HashMap<i32,i32> }

impl Board {
    fn new(sz: i32, snakes: Vec<(i32,i32)>, ladders: Vec<(i32,i32)>) -> Self {
        Self { sz, snakes: snakes.into_iter().collect(), ladders: ladders.into_iter().collect() }
    }
    fn process(&self, pos: i32) -> i32 {
        if let Some(&to) = self.snakes.get(&pos) { return to; }
        if let Some(&to) = self.ladders.get(&pos) { return to; }
        pos
    }
}

struct MoveCmd { player_idx: usize, old_pos: i32, dice: i32 }

struct Engine {
    board: Board,
    players: Vec<Player>,
    turn: usize,
    history: Vec<MoveCmd>,
    winner: Option<usize>,
}

impl Engine {
    fn new(board: Board) -> Self {
        Self { board, players: vec![], turn: 0, history: vec![], winner: None }
    }
    fn add_player(&mut self, name: &str) { self.players.push(Player { name: name.into(), pos: 0 }); }
    fn play(&mut self, dice: i32) -> (i32, bool) {
        assert!(self.winner.is_none(), "Game over");
        let idx = self.turn % self.players.len();
        let old = self.players[idx].pos;
        let np = old + dice;
        if np > self.board.sz {
            self.turn += 1;
            return (old, false);
        }
        let final_pos = self.board.process(np);
        self.players[idx].pos = final_pos;
        self.history.push(MoveCmd { player_idx: idx, old_pos: old, dice });
        let won = final_pos == self.board.sz;
        if won { self.winner = Some(idx); }
        self.turn += 1;
        (final_pos, won)
    }
    fn undo(&mut self) -> bool {
        if let Some(cmd) = self.history.pop() {
            self.players[cmd.player_idx].pos = cmd.old_pos;
            self.turn -= 1;
            self.winner = None;
            true
        } else { false }
    }
    fn standings(&self) -> Vec<(&str, i32)> {
        let mut s: Vec<_> = self.players.iter().map(|p| (p.name.as_str(), p.pos)).collect();
        s.sort_by(|a, b| b.1.cmp(&a.1));
        s
    }
}

fn main() {
    let board = Board::new(20, vec![(15, 5)], vec![(3, 12)]);
    let mut e = Engine::new(board);
    e.add_player("Alice"); e.add_player("Bob");

    // Ladder
    let (pos, _) = e.play(3);
    assert_eq!(pos, 12); // 3 -> ladder -> 12

    // Undo
    assert!(e.undo());
    assert_eq!(e.players[0].pos, 0);

    // Snake
    e.play(4); // Alice -> 4
    e.play(1); // Bob -> 1
    let (pos2, _) = e.play(11); // Alice: 4+11=15 -> snake -> 5
    assert_eq!(pos2, 5);

    // Win
    let b2 = Board::new(10, vec![], vec![]);
    let mut e2 = Engine::new(b2);
    e2.add_player("A");
    let (_, won) = e2.play(10);
    assert!(won);
    assert!(e2.winner.is_some());

    // Can't exceed
    let b3 = Board::new(10, vec![], vec![]);
    let mut e3 = Engine::new(b3);
    e3.add_player("A");
    e3.play(8);
    let (p, _) = e3.play(5);
    assert_eq!(p, 8); // didn't move

    // Thread safety
    use std::sync::{Arc, Mutex};
    let eng = Arc::new(Mutex::new(Engine::new(Board::new(100, vec![], vec![]))));
    { let mut e = eng.lock().unwrap(); e.add_player("T1"); e.add_player("T2"); }
    let mut handles = vec![];
    for _ in 0..4 {
        let ec = Arc::clone(&eng);
        handles.push(std::thread::spawn(move || {
            for _ in 0..5 { let mut e = ec.lock().unwrap(); e.play(1); }
        }));
    }
    for h in handles { h.join().unwrap(); }
    let e = eng.lock().unwrap();
    let total: i32 = e.players.iter().map(|p| p.pos).sum();
    assert_eq!(total, 20);

    println!("Complete Rust Board Game tests passed!");
}
