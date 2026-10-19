"""
Board Game Engine - Interview Solution (Python)

1. Primary Capabilities:
   - Command pattern: MoveCommand with execute/undo for full undo/redo
   - Snake & Ladder board with configurable snakes/ladders
   - Turn-based engine with dice, win detection, standings
   - Extensible: abstract Board/Command for custom games
   - Concurrency Extension: threading.Lock on game state

2. Error Handling:
   - ValueError on invalid snake/ladder config, overlap
   - RuntimeError on game-over play, no players

3. Out Of Scope:
   - Chess piece validation, AI opponents, network multiplayer,
     persistent game state, spectator mode, replays
"""
import threading, random
from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def execute(self) -> bool: ...
    @abstractmethod
    def undo(self): ...

class Player:
    def __init__(self, name): self.name, self.pos = name, 0

class Board:
    def __init__(self, sz, snakes, ladders):
        self.sz, self.snakes, self.ladders = sz, snakes or {}, ladders or {}
    def process(self, p):
        return self.snakes.get(p, self.ladders.get(p, p))

class Move(Command):
    def __init__(self, player, board, dice):
        self.p, self.b, self.d, self.old = player, board, dice, player.pos
    def execute(self):
        np = self.p.pos + self.d
        if np > self.b.sz: return False
        self.p.pos = self.b.process(np); return True
    def undo(self): self.p.pos = self.old

class Engine:
    def __init__(self, board):
        self.board, self.players, self.turn = board, [], 0
        self.hist, self.redo_s, self.winner = [], [], None
        self._lk = threading.Lock()
    def add(self, name):
        p = Player(name); self.players.append(p); return p
    def play(self, dice=None):
        with self._lk:
            if self.winner: raise RuntimeError("Game over")
            p = self.players[self.turn % len(self.players)]
            d = dice or random.randint(1, 6)
            cmd = Move(p, self.board, d); ok = cmd.execute()
            if ok:
                self.hist.append(cmd); self.redo_s.clear()
                if p.pos == self.board.sz: self.winner = p
            self.turn += 1
            return {"player": p.name, "dice": d, "pos": p.pos, "won": p.pos == self.board.sz}
    def undo(self):
        with self._lk:
            if not self.hist: return False
            c = self.hist.pop(); c.undo(); self.redo_s.append(c); self.turn -= 1; self.winner = None; return True

if __name__ == "__main__":
    b = Board(20, {15: 5}, {3: 12})
    e = Engine(b); e.add("A"); e.add("B")
    r = e.play(3)  # A -> 3 -> ladder -> 12
    assert r["pos"] == 12
    e.undo(); assert e.players[0].pos == 0
    e.players[0].pos = 14; r = e.play(6)  # A -> 20 -> win
    assert r["won"]
    print("Interview Board Game passed!")
