# 🎲 Board Game Engine

> **Phase**: [Phase_6: Domain-Specific LLD](../Readme.md)
> **Status**: `Completed`
> **Target Size**: `200-350 lines`

## 📌 Project Overview
Command-pattern extensible board game framework implementing Snake & Ladder with undo/redo support, configurable board, dice rolling, turn management, and win detection.

## 📂 Structure
```text
board_game_engine/
├── python/
│   ├── game_engine.py, test_game_engine.py, interview_solution.py
├── cpp/
│   ├── solution.cpp, interview_solution.cpp
└── rust/
    ├── solution.rs, interview_solution.rs
```

## 🚀 Running
```bash
python python/test_game_engine.py
g++ -std=c++17 -pthread cpp/solution.cpp -o cpp/solution && ./cpp/solution
rustc rust/solution.rs -o rust/solution && ./rust/solution
```
