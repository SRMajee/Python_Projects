# Parking Lot Design

> **Phase**: [Phase_1: Object-Oriented Foundations](../Readme.md)  
> **Status**: `Completed`  
> **Target Size**: `150-200 lines`

## Overview

Design a multi-level parking lot with different spot sizes and dynamic pricing.

## Core Concepts & Patterns

- **Inheritance**: `Vehicle` base class with concrete specializations (`Motorcycle`, `Car`, `Bus`) defining minimum spot sizes and pricing rate multipliers.
- **Composition**: `ParkingLot` composed of multiple `ParkingLevel`s, which in turn contain `ParkingSpot`s. The lot delegates billing to pluggable `PricingStrategy` implementations.
- **Factory**: `VehicleFactory` utilizing a registry pattern to allow dynamically adding new vehicle types (e.g., `ElectricTruck`) without modifying core codebase.
- **Dynamic Pricing**: `DynamicPricingStrategy` computing fees based on parked hours, vehicle type multiplier, and surge multiplier when lot occupancy exceeds threshold (>= 80%).

## Key Rules & Constraints

- Must be easily extensible to new vehicle types (demonstrated via `VehicleFactory.register_vehicle_type`).
- Best-fit spot allocation: Vehicles are assigned the smallest compatible spot available to prevent spot waste.

## Structure

- [`parking_lot.py`](./parking_lot.py): Core implementation and class definitions.
- [`test_parking_lot.py`](./test_parking_lot.py): Unit test suite and verification scenarios.

## Running Tests

```bash
python test_parking_lot.py
```
