"""
Ride-Sharing Engine - Complete Solution (Python)
Uber-like matching engine with:
- Grid-based spatial indexing for O(1) nearest driver lookup
- State machine: IDLE -> REQUESTED -> MATCHED -> IN_PROGRESS -> COMPLETED / CANCELLED
- Dynamic pricing (surge) based on demand/supply ratio
- Driver/Rider registration, matching, trip lifecycle
Concurrency: threading.Lock for thread-safe booking and state transitions.
"""
import threading
import time
import math
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any


class TripState(Enum):
    REQUESTED = auto()
    MATCHED = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    CANCELLED = auto()


class DriverState(Enum):
    IDLE = auto()
    ASSIGNED = auto()
    ON_TRIP = auto()
    OFFLINE = auto()


@dataclass
class Location:
    x: float
    y: float

    def distance_to(self, other: "Location") -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


@dataclass
class Driver:
    id: str
    name: str
    location: Location
    state: DriverState = DriverState.IDLE
    rating: float = 5.0


@dataclass
class Rider:
    id: str
    name: str
    location: Location


@dataclass
class Trip:
    id: str
    rider: Rider
    pickup: Location
    dropoff: Location
    driver: Driver | None = None
    state: TripState = TripState.REQUESTED
    fare: float = 0.0
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None


class SpatialGrid:
    """Grid-based spatial index for O(1) amortized nearest-neighbor lookup."""

    def __init__(self, cell_size: float = 1.0):
        self._cell_size = cell_size
        self._grid: dict[tuple[int, int], set[str]] = {}
        self._driver_cells: dict[str, tuple[int, int]] = {}
        self._lock = threading.Lock()

    def _cell(self, loc: Location) -> tuple[int, int]:
        return (int(loc.x // self._cell_size), int(loc.y // self._cell_size))

    def update(self, driver_id: str, location: Location):
        with self._lock:
            # Remove from old cell
            if driver_id in self._driver_cells:
                old_cell = self._driver_cells[driver_id]
                self._grid.get(old_cell, set()).discard(driver_id)
            # Add to new cell
            cell = self._cell(location)
            self._grid.setdefault(cell, set()).add(driver_id)
            self._driver_cells[driver_id] = cell

    def remove(self, driver_id: str):
        with self._lock:
            if driver_id in self._driver_cells:
                cell = self._driver_cells.pop(driver_id)
                self._grid.get(cell, set()).discard(driver_id)

    def find_nearby(self, location: Location, radius_cells: int = 3) -> list[str]:
        """Return driver IDs in nearby cells (spiral outward)."""
        with self._lock:
            cx, cy = self._cell(location)
            result = []
            for dx in range(-radius_cells, radius_cells + 1):
                for dy in range(-radius_cells, radius_cells + 1):
                    cell = (cx + dx, cy + dy)
                    result.extend(self._grid.get(cell, set()))
            return result


class RideSharingEngine:
    """Main engine coordinating drivers, riders, and trips."""

    BASE_FARE = 5.0
    PER_UNIT_RATE = 2.0
    SURGE_THRESHOLD = 2.0  # demand/supply ratio threshold

    def __init__(self, grid_cell_size: float = 1.0):
        self._drivers: dict[str, Driver] = {}
        self._riders: dict[str, Rider] = {}
        self._trips: dict[str, Trip] = {}
        self._grid = SpatialGrid(grid_cell_size)
        self._trip_counter = 0
        self._lock = threading.Lock()
        self._active_requests = 0

    def register_driver(self, driver_id: str, name: str, x: float, y: float) -> Driver:
        with self._lock:
            if driver_id in self._drivers:
                raise ValueError(f"Driver '{driver_id}' already registered")
            loc = Location(x, y)
            driver = Driver(id=driver_id, name=name, location=loc)
            self._drivers[driver_id] = driver
            self._grid.update(driver_id, loc)
            return driver

    def register_rider(self, rider_id: str, name: str, x: float, y: float) -> Rider:
        with self._lock:
            if rider_id in self._riders:
                raise ValueError(f"Rider '{rider_id}' already registered")
            rider = Rider(id=rider_id, name=name, location=Location(x, y))
            self._riders[rider_id] = rider
            return rider

    def update_driver_location(self, driver_id: str, x: float, y: float):
        with self._lock:
            driver = self._drivers.get(driver_id)
            if not driver:
                raise KeyError(f"Driver '{driver_id}' not found")
            driver.location = Location(x, y)
            if driver.state == DriverState.IDLE:
                self._grid.update(driver_id, driver.location)

    def set_driver_offline(self, driver_id: str):
        with self._lock:
            driver = self._drivers.get(driver_id)
            if not driver:
                raise KeyError(f"Driver '{driver_id}' not found")
            driver.state = DriverState.OFFLINE
            self._grid.remove(driver_id)

    def request_ride(self, rider_id: str, pickup_x: float, pickup_y: float,
                     dropoff_x: float, dropoff_y: float) -> Trip:
        with self._lock:
            rider = self._riders.get(rider_id)
            if not rider:
                raise KeyError(f"Rider '{rider_id}' not found")
            self._trip_counter += 1
            trip_id = f"trip_{self._trip_counter}"
            pickup = Location(pickup_x, pickup_y)
            dropoff = Location(dropoff_x, dropoff_y)
            trip = Trip(id=trip_id, rider=rider, pickup=pickup, dropoff=dropoff)
            self._trips[trip_id] = trip
            self._active_requests += 1
            return trip

    def match_driver(self, trip_id: str, max_distance: float = 10.0) -> Driver | None:
        with self._lock:
            trip = self._trips.get(trip_id)
            if not trip or trip.state != TripState.REQUESTED:
                raise ValueError(f"Trip '{trip_id}' not in REQUESTED state")

            nearby_ids = self._grid.find_nearby(trip.pickup)
            best_driver = None
            best_dist = float("inf")

            for did in nearby_ids:
                driver = self._drivers.get(did)
                if driver and driver.state == DriverState.IDLE:
                    dist = driver.location.distance_to(trip.pickup)
                    if dist <= max_distance and dist < best_dist:
                        best_dist = dist
                        best_driver = driver

            if best_driver:
                best_driver.state = DriverState.ASSIGNED
                trip.driver = best_driver
                trip.state = TripState.MATCHED
                self._grid.remove(best_driver.id)
                self._active_requests -= 1
                return best_driver
            return None

    def start_trip(self, trip_id: str):
        with self._lock:
            trip = self._trips.get(trip_id)
            if not trip or trip.state != TripState.MATCHED:
                raise ValueError(f"Trip '{trip_id}' not in MATCHED state")
            trip.state = TripState.IN_PROGRESS
            trip.driver.state = DriverState.ON_TRIP

    def complete_trip(self, trip_id: str) -> float:
        with self._lock:
            trip = self._trips.get(trip_id)
            if not trip or trip.state != TripState.IN_PROGRESS:
                raise ValueError(f"Trip '{trip_id}' not in IN_PROGRESS state")
            trip.state = TripState.COMPLETED
            trip.completed_at = time.time()
            trip.driver.state = DriverState.IDLE
            # Calculate fare with surge
            distance = trip.pickup.distance_to(trip.dropoff)
            surge = self._calculate_surge()
            trip.fare = (self.BASE_FARE + distance * self.PER_UNIT_RATE) * surge
            # Put driver back on grid
            self._grid.update(trip.driver.id, trip.dropoff)
            trip.driver.location = trip.dropoff
            return trip.fare

    def cancel_trip(self, trip_id: str):
        with self._lock:
            trip = self._trips.get(trip_id)
            if not trip or trip.state in (TripState.COMPLETED, TripState.CANCELLED):
                raise ValueError(f"Trip '{trip_id}' cannot be cancelled")
            if trip.driver:
                trip.driver.state = DriverState.IDLE
                self._grid.update(trip.driver.id, trip.driver.location)
            trip.state = TripState.CANCELLED
            if trip.state == TripState.REQUESTED:
                self._active_requests -= 1

    def _calculate_surge(self) -> float:
        idle_count = sum(1 for d in self._drivers.values() if d.state == DriverState.IDLE)
        if idle_count == 0:
            return 2.0
        ratio = self._active_requests / idle_count
        if ratio > self.SURGE_THRESHOLD:
            return min(3.0, 1.0 + ratio * 0.5)
        return 1.0

    def get_trip(self, trip_id: str) -> Trip | None:
        return self._trips.get(trip_id)
