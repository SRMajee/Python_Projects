"""Tests for Board Game Engine."""
import random
import unittest
from game_engine import (GameEngine, SnakeLadderBoard, Dice, Player,
                         MoveCommand)


class TestSnakeLadderBoard(unittest.TestCase):
    def test_snake(self):
        board = SnakeLadderBoard(100, snakes={50: 10}, ladders={})
        self.assertEqual(board.process_position(50), 10)

    def test_ladder(self):
        board = SnakeLadderBoard(100, snakes={}, ladders={5: 50})
        self.assertEqual(board.process_position(5), 50)

    def test_normal_position(self):
        board = SnakeLadderBoard(100, snakes={50: 10}, ladders={5: 50})
        self.assertEqual(board.process_position(30), 30)

    def test_invalid_snake(self):
        with self.assertRaises(ValueError):
            SnakeLadderBoard(100, snakes={10: 50}, ladders={})  # goes up

    def test_invalid_ladder(self):
        with self.assertRaises(ValueError):
            SnakeLadderBoard(100, snakes={}, ladders={50: 10})  # goes down

    def test_overlap(self):
        with self.assertRaises(ValueError):
            SnakeLadderBoard(100, snakes={20: 5}, ladders={20: 50})


class TestGameEngine(unittest.TestCase):
    def setUp(self):
        self.board = SnakeLadderBoard(20, snakes={15: 5}, ladders={3: 12})
        self.dice = Dice(6, rng=random.Random(42))
        self.engine = GameEngine(self.board, self.dice)
        self.engine.add_player("p1", "Alice")
        self.engine.add_player("p2", "Bob")

    def test_turn_order(self):
        self.assertEqual(self.engine.current_player().name, "Alice")
        self.engine.play_turn(dice_override=1)
        self.assertEqual(self.engine.current_player().name, "Bob")

    def test_move_with_ladder(self):
        result = self.engine.play_turn(dice_override=3)
        self.assertEqual(result["to"], 12)  # ladder 3->12

    def test_move_with_snake(self):
        self.engine.play_turn(dice_override=2)  # Alice -> 2
        self.engine.play_turn(dice_override=1)  # Bob -> 1
        # Move Alice to 15 (snake)
        self.engine.play_turn(dice_override=13)  # 2+13=15 -> snake -> 5
        self.assertEqual(self.engine._players[0].position, 5)

    def test_cant_exceed_board(self):
        self.engine._players[0].position = 19
        result = self.engine.play_turn(dice_override=5)
        self.assertFalse(result["moved"])
        self.assertEqual(self.engine._players[0].position, 19)

    def test_win(self):
        self.engine._players[0].position = 14
        result = self.engine.play_turn(dice_override=6)  # 14+6=20
        self.assertTrue(result["won"])
        self.assertEqual(self.engine.get_winner().name, "Alice")

    def test_undo_redo(self):
        self.engine.play_turn(dice_override=2)
        self.assertEqual(self.engine._players[0].position, 2)
        self.assertTrue(self.engine.undo())
        self.assertEqual(self.engine._players[0].position, 0)
        self.assertTrue(self.engine.redo())
        self.assertEqual(self.engine._players[0].position, 2)

    def test_undo_empty(self):
        self.assertFalse(self.engine.undo())

    def test_game_over_blocks_play(self):
        self.engine._players[0].position = 14
        self.engine.play_turn(dice_override=6)
        with self.assertRaises(RuntimeError):
            self.engine.play_turn(dice_override=1)

    def test_standings(self):
        self.engine.play_turn(dice_override=5)
        self.engine.play_turn(dice_override=2)
        standings = self.engine.get_standings()
        self.assertEqual(standings[0]["player"], "Alice")  # pos 5 > 2


if __name__ == "__main__":
    unittest.main()
