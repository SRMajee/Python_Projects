"""
Board Game Engine - Complete Solution (Python)
Extensible board game framework with:
- Command pattern for moves (undo/redo support)
- Snake & Ladder implementation with configurable board
- Dice rolling, turn management, win detection
- Extensible base classes for custom games
Concurrency: threading.Lock for thread-safe game state access.
"""
import threading
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class Command(ABC):
    """Command pattern base for undoable moves."""
    @abstractmethod
    def execute(self) -> bool:
        ...
    @abstractmethod
    def undo(self):
        ...


@dataclass
class Player:
    id: str
    name: str
    position: int = 0


class Board(ABC):
    """Abstract board base."""
    @abstractmethod
    def size(self) -> int: ...
    @abstractmethod
    def process_position(self, pos: int) -> int: ...


class SnakeLadderBoard(Board):
    """Snake & Ladder board with configurable snakes and ladders."""
    def __init__(self, size: int = 100,
                 snakes: dict[int, int] | None = None,
                 ladders: dict[int, int] | None = None):
        self._size = size
        self.snakes = snakes or {16: 6, 47: 26, 49: 11, 56: 53, 62: 19,
                                  64: 60, 87: 24, 93: 73, 95: 75, 98: 78}
        self.ladders = ladders or {1: 38, 4: 14, 9: 31, 21: 42, 28: 84,
                                    36: 44, 51: 67, 71: 91, 80: 100}
        # Validate: no overlap
        for pos in self.snakes:
            if pos in self.ladders:
                raise ValueError(f"Position {pos} has both snake and ladder")
            if self.snakes[pos] >= pos:
                raise ValueError(f"Snake at {pos} must go down, not to {self.snakes[pos]}")
        for pos in self.ladders:
            if self.ladders[pos] <= pos:
                raise ValueError(f"Ladder at {pos} must go up, not to {self.ladders[pos]}")

    def size(self) -> int:
        return self._size

    def process_position(self, pos: int) -> int:
        if pos in self.snakes:
            return self.snakes[pos]
        if pos in self.ladders:
            return self.ladders[pos]
        return pos


class MoveCommand(Command):
    """A player move on the board."""
    def __init__(self, player: Player, board: Board, dice_val: int):
        self.player = player
        self.board = board
        self.dice_val = dice_val
        self._old_pos = player.position
        self._new_pos = player.position

    def execute(self) -> bool:
        new_pos = self.player.position + self.dice_val
        if new_pos > self.board.size():
            return False  # can't move beyond board
        new_pos = self.board.process_position(new_pos)
        self._new_pos = new_pos
        self.player.position = new_pos
        return True

    def undo(self):
        self.player.position = self._old_pos


class Dice:
    """Configurable dice with N faces."""
    def __init__(self, faces: int = 6, rng: random.Random | None = None):
        self._faces = faces
        self._rng = rng or random.Random()

    def roll(self) -> int:
        return self._rng.randint(1, self._faces)


class GameEngine:
    """Turn-based game engine with command history and undo/redo."""

    def __init__(self, board: Board, dice: Dice | None = None):
        self.board = board
        self.dice = dice or Dice()
        self._players: list[Player] = []
        self._current_turn = 0
        self._history: list[Command] = []
        self._redo_stack: list[Command] = []
        self._winner: Player | None = None
        self._lock = threading.Lock()

    def add_player(self, player_id: str, name: str) -> Player:
        with self._lock:
            if self._winner:
                raise RuntimeError("Game is over")
            p = Player(id=player_id, name=name)
            self._players.append(p)
            return p

    def current_player(self) -> Player:
        with self._lock:
            if not self._players:
                raise RuntimeError("No players")
            return self._players[self._current_turn % len(self._players)]

    def play_turn(self, dice_override: int | None = None) -> dict[str, Any]:
        """Execute one turn. Returns turn result dict."""
        with self._lock:
            if self._winner:
                raise RuntimeError("Game already won")
            if not self._players:
                raise RuntimeError("No players")

            player = self._players[self._current_turn % len(self._players)]
            dice_val = dice_override if dice_override is not None else self.dice.roll()
            old_pos = player.position

            cmd = MoveCommand(player, self.board, dice_val)
            moved = cmd.execute()

            result = {
                "player": player.name,
                "dice": dice_val,
                "from": old_pos,
                "to": player.position,
                "moved": moved,
                "won": False,
            }

            if moved:
                self._history.append(cmd)
                self._redo_stack.clear()
                if player.position == self.board.size():
                    self._winner = player
                    result["won"] = True

            self._current_turn += 1
            return result

    def undo(self) -> bool:
        with self._lock:
            if not self._history:
                return False
            cmd = self._history.pop()
            cmd.undo()
            self._redo_stack.append(cmd)
            self._current_turn -= 1
            if self._winner:
                self._winner = None
            return True

    def redo(self) -> bool:
        with self._lock:
            if not self._redo_stack:
                return False
            cmd = self._redo_stack.pop()
            cmd.execute()
            self._history.append(cmd)
            self._current_turn += 1
            return True

    def get_winner(self) -> Player | None:
        with self._lock:
            return self._winner

    def get_standings(self) -> list[dict]:
        with self._lock:
            return [{"player": p.name, "position": p.position} for p in
                    sorted(self._players, key=lambda p: -p.position)]
