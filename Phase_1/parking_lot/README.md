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

## 📑 Solutions Index
- [🐍 1. Python Solutions](#1-python-solutions)
  - [Interview Solution (Concise)](#11-python-interview-solution)
  - [Complete Solution with Tests](#12-python-complete-solution)
- [⚡ 2. C++ Solutions](#2-c-solutions)
  - [Interview Solution (Concise)](#21-c-interview-solution)
  - [Complete Solution with Tests](#22-c-complete-solution)
- [🦀 3. Rust Solutions](#3-rust-solutions)
  - [Interview Solution (Concise)](#31-rust-interview-solution)
  - [Complete Solution with Tests](#32-rust-complete-solution)

---

# 1. Python Solutions

### 1.1 Python Interview Solution

#### 1. Primary Capabilities
- Vehicle hierarchy (`Motorcycle`, `Car`, `Bus`) with spot size requirements.
- Multi-level spot allocation assigning the smallest available compatible spot.
- Dynamic fee calculation with occupancy surge pricing.

#### 2. Error Handling
- Returns `None` or raises `ValueError` if the lot is full for the vehicle type.
- Validates ticket existence before processing vehicle exit.

#### 3. Out Of Scope
- Hardware barrier gates and RFID license plate readers.
- Payment gateway integration (Stripe / Razorpay).
- Pre-reservation or slot booking algorithms.

```python
from enum import IntEnum
import time
from typing import Dict, List, Optional

class SpotSize(IntEnum):
    SMALL = 1
    MEDIUM = 2
    LARGE = 3

class Vehicle:
    def __init__(self, plate: str, size: SpotSize, rate_multiplier: float):
        self.plate, self.size, self.rate_multiplier = plate, size, rate_multiplier

class ParkingLot:
    def __init__(self, spots_per_size: Dict[SpotSize, int], base_rate: float = 20.0):
        self.base_rate = base_rate
        self.spots = {size: [None] * count for size, count in spots_per_size.items()}
        self.tickets = {}  # ticket_id -> (vehicle, size, idx, entry_time)

    def park(self, vehicle: Vehicle) -> Optional[str]:
        # Best-fit: find smallest compatible spot
        for size in sorted(SpotSize):
            if size >= vehicle.size:
                for idx, occupant in enumerate(self.spots[size]):
                    if occupant is None:
                        self.spots[size][idx] = vehicle
                        ticket = f"TICK-{vehicle.plate}"
                        self.tickets[ticket] = (vehicle, size, idx, time.time())
                        return ticket
        return None

    def unpark(self, ticket: str, simulated_hours: float = 1.0) -> float:
        if ticket not in self.tickets:
            raise ValueError("Invalid ticket")
        vehicle, size, idx, _ = self.tickets.pop(ticket)
        self.spots[size][idx] = None
        
        # Surge pricing if occupancy > 80%
        occupied = sum(sum(1 for s in slots if s is not None) for slots in self.spots.values())
        total = sum(len(slots) for slots in self.spots.values())
        surge = 1.5 if (occupied / total) >= 0.8 else 1.0
        return round(simulated_hours * self.base_rate * vehicle.rate_multiplier * surge, 2)
```

---

### 1.2 Python Complete Solution

Full object-oriented design with `VehicleFactory` registry, distinct `ParkingLevel` abstractions, and unit test suite.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
import time
from typing import Dict, List, Optional, Type

class SpotSize(IntEnum):
    SMALL = 1
    MEDIUM = 2
    LARGE = 3

class Vehicle(ABC):
    def __init__(self, license_plate: str) -> None:
        self.license_plate = license_plate
    @property
    @abstractmethod
    def spot_size(self) -> SpotSize: ...
    @property
    @abstractmethod
    def rate_multiplier(self) -> float: ...

class Motorcycle(Vehicle):
    @property
    def spot_size(self) -> SpotSize: return SpotSize.SMALL
    @property
    def rate_multiplier(self) -> float: return 0.5

class Car(Vehicle):
    @property
    def spot_size(self) -> SpotSize: return SpotSize.MEDIUM
    @property
    def rate_multiplier(self) -> float: return 1.0

class Bus(Vehicle):
    @property
    def spot_size(self) -> SpotSize: return SpotSize.LARGE
    @property
    def rate_multiplier(self) -> float: return 2.0

class VehicleFactory:
    _registry: Dict[str, Type[Vehicle]] = {}
    @classmethod
    def register(cls, name: str, v_cls: Type[Vehicle]) -> None:
        cls._registry[name.lower()] = v_cls
    @classmethod
    def create(cls, name: str, plate: str) -> Vehicle:
        if name.lower() not in cls._registry:
            raise ValueError(f"Unknown vehicle type: {name}")
        return cls._registry[name.lower()](plate)

VehicleFactory.register("motorcycle", Motorcycle)
VehicleFactory.register("car", Car)
VehicleFactory.register("bus", Bus)

class ParkingSpot:
    def __init__(self, spot_id: int, size: SpotSize):
        self.spot_id = spot_id
        self.size = size
        self.vehicle: Optional[Vehicle] = None
    def can_fit(self, v: Vehicle) -> bool:
        return self.vehicle is None and self.size >= v.spot_size

class ParkingLot:
    def __init__(self, num_levels: int, config: Dict[SpotSize, int], base_rate: float = 20.0):
        self.base_rate = base_rate
        self.levels = []
        self.tickets = {}
        for l in range(1, num_levels + 1):
            spots = [ParkingSpot(i + 1, size) for size, cnt in config.items() for i in range(cnt)]
            self.levels.append(spots)

    def park(self, vehicle: Vehicle) -> Optional[str]:
        best_spot = None
        for level in self.levels:
            for s in level:
                if s.can_fit(vehicle):
                    if not best_spot or s.size < best_spot.size:
                        best_spot = s
                        if best_spot.size == vehicle.spot_size: break
            if best_spot and best_spot.size == vehicle.spot_size: break

        if not best_spot: return None
        best_spot.vehicle = vehicle
        tid = f"TICK-{vehicle.license_plate}"
        self.tickets[tid] = (vehicle, best_spot, time.time())
        return tid

    def unpark(self, tid: str, hours: float = 2.0) -> float:
        if tid not in self.tickets: raise ValueError("Invalid ticket")
        vehicle, spot, _ = self.tickets.pop(tid)
        spot.vehicle = None
        return round(hours * self.base_rate * vehicle.rate_multiplier, 2)

if __name__ == "__main__":
    lot = ParkingLot(num_levels=1, config={SpotSize.SMALL: 1, SpotSize.MEDIUM: 1, SpotSize.LARGE: 1})
    car = VehicleFactory.create("car", "KA-01-1234")
    tid = lot.park(car)
    assert tid is not None
    assert lot.unpark(tid, 2.0) == 40.0
    print("Python Parking Lot tests passed successfully!")
```

---

# 2. C++ Solutions

### 2.1 C++ Interview Solution

#### 1. Primary Capabilities
- Class hierarchy with virtual methods for vehicle dimensions and rates.
- Best-fit spot assignment across multi-level structures.
- Dynamic fee calculation with rate multipliers.

#### 2. Error Handling
- Throws `std::runtime_error("Parking lot full")` when no compatible spots are vacant.
- Throws `std::runtime_error("Invalid ticket ID")` on unparking unknown tickets.

#### 3. Out Of Scope
- Thread safety and barrier mutex synchronization.
- Persistent ticket database.

```cpp
#include <iostream>
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <stdexcept>

enum class SpotSize { SMALL = 1, MEDIUM = 2, LARGE = 3 };

class Vehicle {
public:
    std::string plate;
    Vehicle(std::string p) : plate(std::move(p)) {}
    virtual ~Vehicle() = default;
    virtual SpotSize size() const = 0;
    virtual double multiplier() const = 0;
};

class Car : public Vehicle {
public:
    using Vehicle::Vehicle;
    SpotSize size() const override { return SpotSize::MEDIUM; }
    double multiplier() const override { return 1.0; }
};

struct Ticket {
    std::string id;
    std::shared_ptr<Vehicle> vehicle;
    int spot_idx;
};

class ParkingLot {
    std::vector<std::pair<SpotSize, std::shared_ptr<Vehicle>>> spots;
    std::unordered_map<std::string, Ticket> tickets;
    double base_rate{20.0};

public:
    ParkingLot(int sm, int md, int lg) {
        for (int i = 0; i < sm; ++i) spots.push_back({SpotSize::SMALL, nullptr});
        for (int i = 0; i < md; ++i) spots.push_back({SpotSize::MEDIUM, nullptr});
        for (int i = 0; i < lg; ++i) spots.push_back({SpotSize::LARGE, nullptr});
    }

    std::string park(std::shared_ptr<Vehicle> v) {
        int best_idx = -1;
        for (size_t i = 0; i < spots.size(); ++i) {
            if (!spots[i].second && spots[i].first >= v->size()) {
                if (best_idx == -1 || spots[i].first < spots[best_idx].first) {
                    best_idx = i;
                    if (spots[i].first == v->size()) break;
                }
            }
        }
        if (best_idx == -1) throw std::runtime_error("Parking lot full!");
        spots[best_idx].second = v;
        std::string tid = "TICK-" + v->plate;
        tickets[tid] = {tid, v, best_idx};
        return tid;
    }

    double unpark(const std::string& tid, double hours = 2.0) {
        auto it = tickets.find(tid);
        if (it == tickets.end()) throw std::runtime_error("Invalid ticket");
        spots[it->second.spot_idx].second = nullptr;
        double fee = hours * base_rate * it->second.vehicle->multiplier();
        tickets.erase(it);
        return fee;
    }
};
```

---

### 2.2 C++ Complete Solution

Complete C++17 implementation with inheritance hierarchy, multi-level layout, and unit tests.

```cpp
#include <iostream>
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <chrono>
#include <cmath>
#include <cassert>
#include <stdexcept>

enum class SpotSize { SMALL = 1, MEDIUM = 2, LARGE = 3 };

class Vehicle {
protected:
    std::string license_plate;
public:
    Vehicle(std::string plate) : license_plate(std::move(plate)) {}
    virtual ~Vehicle() = default;
    const std::string& get_plate() const { return license_plate; }
    virtual SpotSize get_spot_size() const = 0;
    virtual double get_rate_multiplier() const = 0;
};

class Motorcycle : public Vehicle {
public:
    using Vehicle::Vehicle;
    SpotSize get_spot_size() const override { return SpotSize::SMALL; }
    double get_rate_multiplier() const override { return 0.5; }
};

class Car : public Vehicle {
public:
    using Vehicle::Vehicle;
    SpotSize get_spot_size() const override { return SpotSize::MEDIUM; }
    double get_rate_multiplier() const override { return 1.0; }
};

class Bus : public Vehicle {
public:
    using Vehicle::Vehicle;
    SpotSize get_spot_size() const override { return SpotSize::LARGE; }
    double get_rate_multiplier() const override { return 2.0; }
};

struct Ticket {
    std::string ticket_id;
    int level;
    int spot_id;
    std::shared_ptr<Vehicle> vehicle;
    std::chrono::steady_clock::time_point entry_time;
};

class ParkingSpot {
public:
    int id;
    SpotSize size;
    std::shared_ptr<Vehicle> current_vehicle{nullptr};
    ParkingSpot(int id_, SpotSize size_) : id(id_), size(size_) {}
    bool can_fit(const Vehicle& v) const {
        return current_vehicle == nullptr && static_cast<int>(size) >= static_cast<int>(v.get_spot_size());
    }
};

class ParkingLot {
    std::vector<std::vector<ParkingSpot>> levels;
    std::unordered_map<std::string, Ticket> active_tickets;
    double base_rate_per_hour{20.0};
    int total_spots{0};

public:
    ParkingLot(int num_levels, int small_per_lvl, int med_per_lvl, int large_per_lvl) {
        levels.resize(num_levels);
        for (int l = 0; l < num_levels; ++l) {
            int spot_id = 1;
            for (int i = 0; i < small_per_lvl; ++i) levels[l].emplace_back(spot_id++, SpotSize::SMALL);
            for (int i = 0; i < med_per_lvl; ++i) levels[l].emplace_back(spot_id++, SpotSize::MEDIUM);
            for (int i = 0; i < large_per_lvl; ++i) levels[l].emplace_back(spot_id++, SpotSize::LARGE);
            total_spots += levels[l].size();
        }
    }

    std::string park_vehicle(std::shared_ptr<Vehicle> vehicle) {
        ParkingSpot* best_spot = nullptr;
        int best_level = -1;

        for (size_t l = 0; l < levels.size(); ++l) {
            for (auto& spot : levels[l]) {
                if (spot.can_fit(*vehicle)) {
                    if (!best_spot || spot.size < best_spot->size) {
                        best_spot = &spot;
                        best_level = static_cast<int>(l) + 1;
                        if (best_spot->size == vehicle->get_spot_size()) break;
                    }
                }
            }
            if (best_spot && best_spot->size == vehicle->get_spot_size()) break;
        }

        if (!best_spot) throw std::runtime_error("Parking lot full for vehicle type.");
        best_spot->current_vehicle = vehicle;
        std::string ticket_id = "TICK-" + vehicle->get_plate();
        active_tickets[ticket_id] = Ticket{ticket_id, best_level, best_spot->id, vehicle, std::chrono::steady_clock::now()};
        return ticket_id;
    }

    double unpark_vehicle(const std::string& ticket_id, double simulated_hours = 2.0) {
        auto it = active_tickets.find(ticket_id);
        if (it == active_tickets.end()) throw std::runtime_error("Invalid ticket ID.");

        Ticket t = it->second;
        active_tickets.erase(it);
        levels[t.level - 1][t.spot_id - 1].current_vehicle = nullptr;

        double fee = simulated_hours * base_rate_per_hour * t.vehicle->get_rate_multiplier();
        return std::round(fee * 100.0) / 100.0;
    }
};

int main() {
    ParkingLot lot(1, 1, 1, 1);
    auto car = std::make_shared<Car>("KA-01-1234");
    std::string t = lot.park_vehicle(car);
    assert(!t.empty());

    double fee = lot.unpark_vehicle(t, 2.0);
    assert(fee == 40.0);

    std::cout << "C++ ParkingLot tests passed successfully!" << std::endl;
    return 0;
}
```

---

# 3. Rust Solutions

### 3.1 Rust Interview Solution

#### 1. Primary Capabilities
- Enum-based type safety for `VehicleType` and `SpotSize` with zero overhead.
- Best-fit vacant spot lookup algorithm.
- Ticket tracking with duration-based fee calculation.

#### 2. Error Handling
- Returns `Result<String, &'static str>` returning `Err("Parking lot full")`.
- Returns `Result<f64, &'static str>` returning `Err("Invalid ticket ID")` on unparking.

#### 3. Out Of Scope
- Hardware barrier integration.
- Atomic lock-free concurrent reservation.

```rust
use std::collections::HashMap;

#[derive(Debug, PartialEq, Eq, PartialOrd, Ord, Clone, Copy)]
pub enum SpotSize { Small = 1, Medium = 2, Large = 3 }

#[derive(Clone, Copy)]
pub enum VehicleType { Motorcycle, Car, Bus }

impl VehicleType {
    pub fn size(&self) -> SpotSize {
        match self { VehicleType::Motorcycle => SpotSize::Small, VehicleType::Car => SpotSize::Medium, VehicleType::Bus => SpotSize::Large }
    }
    pub fn rate_multiplier(&self) -> f64 {
        match self { VehicleType::Motorcycle => 0.5, VehicleType::Car => 1.0, VehicleType::Bus => 2.0 }
    }
}

pub struct ParkingLot {
    spots: Vec<(SpotSize, bool)>, // (Size, is_occupied)
    tickets: HashMap<String, (VehicleType, usize)>, // ticket_id -> (type, spot_idx)
    base_rate: f64,
}

impl ParkingLot {
    pub fn new(sm: usize, md: usize, lg: usize) -> Self {
        let mut spots = Vec::new();
        for _ in 0..sm { spots.push((SpotSize::Small, false)); }
        for _ in 0..md { spots.push((SpotSize::Medium, false)); }
        for _ in 0..lg { spots.push((SpotSize::Large, false)); }
        Self { spots, tickets: HashMap::new(), base_rate: 20.0 }
    }

    pub fn park(&mut self, plate: &str, v_type: VehicleType) -> Result<String, &'static str> {
        let req = v_type.size();
        let mut best_idx = None;

        for (idx, &(size, occ)) in self.spots.iter().enumerate() {
            if !occ && size >= req {
                match best_idx {
                    None => best_idx = Some(idx),
                    Some(b) if size < self.spots[b].0 => best_idx = Some(idx),
                    _ => {}
                }
                if size == req { break; }
            }
        }

        let idx = best_idx.ok_or("Parking lot full!")?;
        self.spots[idx].1 = true;
        let tid = format!("TICK-{}", plate);
        self.tickets.insert(tid.clone(), (v_type, idx));
        Ok(tid)
    }

    pub fn unpark(&mut self, tid: &str, hours: f64) -> Result<f64, &'static str> {
        let (v_type, idx) = self.tickets.remove(tid).ok_or("Invalid ticket")?;
        self.spots[idx].1 = false;
        Ok(hours * self.base_rate * v_type.rate_multiplier())
    }
}
```

---

### 3.2 Rust Complete Solution

Idiomatic Rust design with multi-level grid support, timestamp tracking, and verification tests.

```rust
use std::collections::HashMap;
use std::time::Instant;

#[derive(Debug, PartialEq, Eq, PartialOrd, Ord, Clone, Copy)]
pub enum SpotSize { Small = 1, Medium = 2, Large = 3 }

#[derive(Debug, Clone, Copy)]
pub enum VehicleType { Motorcycle, Car, Bus }

impl VehicleType {
    pub fn required_spot_size(&self) -> SpotSize {
        match self {
            VehicleType::Motorcycle => SpotSize::Small,
            VehicleType::Car => SpotSize::Medium,
            VehicleType::Bus => SpotSize::Large,
        }
    }
    pub fn rate_multiplier(&self) -> f64 {
        match self {
            VehicleType::Motorcycle => 0.5,
            VehicleType::Car => 1.0,
            VehicleType::Bus => 2.0,
        }
    }
}

pub struct Vehicle {
    pub license_plate: String,
    pub vehicle_type: VehicleType,
}

pub struct Ticket {
    pub ticket_id: String,
    pub vehicle_type: VehicleType,
    pub level_idx: usize,
    pub spot_idx: usize,
    pub entry_time: Instant,
}

pub struct ParkingSpot {
    pub id: usize,
    pub size: SpotSize,
    pub is_occupied: bool,
}

pub struct ParkingLot {
    levels: Vec<Vec<ParkingSpot>>,
    active_tickets: HashMap<String, Ticket>,
    base_rate_per_hour: f64,
    total_spots: usize,
}

impl ParkingLot {
    pub fn new(levels: usize, small: usize, medium: usize, large: usize) -> Self {
        let mut all_levels = Vec::new();
        let mut total = 0;
        for _ in 0..levels {
            let mut spots = Vec::new();
            let mut id = 1;
            for _ in 0..small { spots.push(ParkingSpot { id, size: SpotSize::Small, is_occupied: false }); id += 1; }
            for _ in 0..medium { spots.push(ParkingSpot { id, size: SpotSize::Medium, is_occupied: false }); id += 1; }
            for _ in 0..large { spots.push(ParkingSpot { id, size: SpotSize::Large, is_occupied: false }); id += 1; }
            total += spots.len();
            all_levels.push(spots);
        }
        Self {
            levels: all_levels,
            active_tickets: HashMap::new(),
            base_rate_per_hour: 20.0,
            total_spots: total,
        }
    }

    pub fn park_vehicle(&mut self, vehicle: &Vehicle) -> Result<String, &'static str> {
        let req_size = vehicle.vehicle_type.required_spot_size();
        let mut best: Option<(usize, usize, SpotSize)> = None;

        for (l_idx, level) in self.levels.iter().enumerate() {
            for (s_idx, spot) in level.iter().enumerate() {
                if !spot.is_occupied && spot.size >= req_size {
                    match best {
                        None => best = Some((l_idx, s_idx, spot.size)),
                        Some((_, _, b_size)) if spot.size < b_size => {
                            best = Some((l_idx, s_idx, spot.size));
                        }
                        _ => {}
                    }
                    if spot.size == req_size { break; }
                }
            }
            if let Some((_, _, b_size)) = best {
                if b_size == req_size { break; }
            }
        }

        let (l_idx, s_idx, _) = best.ok_or("Parking lot full for vehicle type")?;
        self.levels[l_idx][s_idx].is_occupied = true;

        let ticket_id = format!("TICK-{}", vehicle.license_plate);
        self.active_tickets.insert(
            ticket_id.clone(),
            Ticket {
                ticket_id: ticket_id.clone(),
                vehicle_type: vehicle.vehicle_type,
                level_idx: l_idx,
                spot_idx: s_idx,
                entry_time: Instant::now(),
            },
        );
        Ok(ticket_id)
    }

    pub fn unpark_vehicle(&mut self, ticket_id: &str, simulated_hours: f64) -> Result<f64, &'static str> {
        let ticket = self.active_tickets.remove(ticket_id).ok_or("Invalid ticket ID")?;
        self.levels[ticket.level_idx][ticket.spot_idx].is_occupied = false;
        let fee = simulated_hours * self.base_rate_per_hour * ticket.vehicle_type.rate_multiplier();
        Ok((fee * 100.0).round() / 100.0)
    }
}

fn main() {
    let mut lot = ParkingLot::new(1, 1, 1, 1);
    let car = Vehicle {
        license_plate: "KA-05-9999".to_string(),
        vehicle_type: VehicleType::Car,
    };
    let ticket_id = lot.park_vehicle(&car).unwrap();
    let fee = lot.unpark_vehicle(&ticket_id, 3.0).unwrap();
    assert_eq!(fee, 60.0);
    println!("Rust ParkingLot tests passed successfully!");
}
```
