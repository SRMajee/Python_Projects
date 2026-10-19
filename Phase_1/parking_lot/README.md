# Parking Lot Design

> **Phase**: [Phase_1: Object-Oriented Foundations](../Readme.md)  
> **Status**: `Completed`  
> **Target Size**: `150-200 lines`

---

## 📌 Project Overview
Design an extensible, multi-level parking lot supporting different vehicle types (`Motorcycle`, `Car`, `Bus`), best-fit spot sizing (`SMALL`, `MEDIUM`, `LARGE`), dynamic factory instantiation, and surge-pricing algorithms.

---

## 🧠 Core Concepts & Patterns
- **Inheritance & Polymorphism**: Abstract `Vehicle` base class with vehicle-specific spot sizes and billing multipliers.
- **Composition**: `ParkingLot` composed of `ParkingLevel`s, which consist of `ParkingSpot`s.
- **Factory Pattern**: Registry-based vehicle creation extensible at runtime without modifying existing core logic.
- **Dynamic Pricing**: Fee calculation combining parked duration, vehicle multiplier, and occupancy surge rates.

---

## ⚠️ Key Rules & Constraints
- Must be easily extensible to new vehicle types without modifying existing classes (Open/Closed Principle).
- Best-fit spot allocation: assign the smallest compatible available spot to maximize space efficiency.
- Releasing a spot calculates accurate billing and updates lot occupancy.

---

## 📂 Project Structure & Multi-Language Solutions

```text
parking_lot/
├── README.md
├── python/
│   ├── parking_lot.py           # Complete implementation with VehicleFactory & levels
│   ├── test_parking_lot.py      # Full unit test suite (extensibility, allocation, pricing)
│   └── interview_solution.py    # Concise 45-min interview code with scoping & error handling
├── cpp/
│   ├── solution.cpp             # Complete C++17 solution with tests
│   └── interview_solution.cpp   # Concise interview solution with scoping & error handling
└── rust/
    ├── solution.rs              # Complete Rust solution with tests
    └── interview_solution.rs    # Concise interview solution with scoping & error handling
```

---

## 🚀 Running Tests & Verification

### 🐍 Python
```bash
# Run complete test suite
python python/test_parking_lot.py

# Run concise interview solution
python python/interview_solution.py
```

### ⚡ C++
```bash
# Run complete C++ solution with tests
g++ -std=c++17 cpp/solution.cpp -o cpp/solution && ./cpp/solution

# Run concise interview C++ solution
g++ -std=c++17 cpp/interview_solution.cpp -o cpp/interview_solution && ./cpp/interview_solution
```

### 🦀 Rust
```bash
# Run complete Rust solution with tests
rustc rust/solution.rs -o rust/solution && ./rust/solution

# Run concise interview Rust solution
rustc rust/interview_solution.rs -o rust/interview_solution && ./rust/interview_solution
```
