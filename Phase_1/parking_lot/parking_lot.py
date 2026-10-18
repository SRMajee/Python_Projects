import math
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, List, Optional, Type


class SpotSize(IntEnum):
    """Size categories for parking spots and vehicle compatibility."""
    SMALL = 1
    MEDIUM = 2
    LARGE = 3


class Vehicle(ABC):
    """Abstract base class for all vehicle types."""

    def __init__(self, license_plate: str) -> None:
        self.license_plate = license_plate

    @property
    @abstractmethod
    def spot_size(self) -> SpotSize:
        """Minimum spot size required to park this vehicle."""
        ...

    @property
    @abstractmethod
    def rate_multiplier(self) -> float:
        """Pricing multiplier applied to the base rate."""
        ...


class Motorcycle(Vehicle):
    """Two-wheeler vehicle requiring a SMALL spot."""

    @property
    def spot_size(self) -> SpotSize:
        return SpotSize.SMALL

    @property
    def rate_multiplier(self) -> float:
        return 0.5


class Car(Vehicle):
    """Standard automobile requiring a MEDIUM spot."""

    @property
    def spot_size(self) -> SpotSize:
        return SpotSize.MEDIUM

    @property
    def rate_multiplier(self) -> float:
        return 1.0


class Bus(Vehicle):
    """Heavy vehicle requiring a LARGE spot."""

    @property
    def spot_size(self) -> SpotSize:
        return SpotSize.LARGE

    @property
    def rate_multiplier(self) -> float:
        return 2.0


class VehicleFactory:
    """Factory for creating vehicles with an extensible registry pattern."""

    _registry: Dict[str, Type[Vehicle]] = {}

    @classmethod
    def register_vehicle_type(cls, type_name: str, vehicle_cls: Type[Vehicle]) -> None:
        """Register a new vehicle type for factory instantiation."""
        cls._registry[type_name.lower()] = vehicle_cls

    @classmethod
    def create_vehicle(cls, type_name: str, license_plate: str) -> Vehicle:
        """Instantiate a registered vehicle by type name and license plate."""
        type_key = type_name.lower()
        if type_key not in cls._registry:
            raise ValueError(
                f"Unknown vehicle type: '{type_name}'. Available: {list(cls._registry.keys())}"
            )
        return cls._registry[type_key](license_plate)


# Register built-in vehicle types
VehicleFactory.register_vehicle_type("motorcycle", Motorcycle)
VehicleFactory.register_vehicle_type("car", Car)
VehicleFactory.register_vehicle_type("bus", Bus)


@dataclass
class Ticket:
    """Parking ticket issued upon successful parking."""
    ticket_id: str
    vehicle: Vehicle
    level_number: int
    spot_id: int
    entry_time: float


class ParkingSpot:
    """Represents a single parking spot."""

    def __init__(self, spot_id: int, size: SpotSize) -> None:
        self.spot_id = spot_id
        self.size = size
        self.current_vehicle: Optional[Vehicle] = None

    @property
    def is_occupied(self) -> bool:
        return self.current_vehicle is not None

    def can_fit(self, vehicle: Vehicle) -> bool:
        return not self.is_occupied and self.size >= vehicle.spot_size

    def park(self, vehicle: Vehicle) -> bool:
        if not self.can_fit(vehicle):
            return False
        self.current_vehicle = vehicle
        return True

    def vacate(self) -> Optional[Vehicle]:
        vehicle = self.current_vehicle
        self.current_vehicle = None
        return vehicle


class ParkingLevel:
    """A level/floor in the parking lot containing multiple spots."""

    def __init__(self, level_number: int, spot_configs: Dict[SpotSize, int]) -> None:
        self.level_number = level_number
        self.spots: List[ParkingSpot] = []
        next_id = 1
        for size in (SpotSize.SMALL, SpotSize.MEDIUM, SpotSize.LARGE):
            count = spot_configs.get(size, 0)
            for _ in range(count):
                self.spots.append(ParkingSpot(next_id, size))
                next_id += 1

    def find_best_spot(self, vehicle: Vehicle) -> Optional[ParkingSpot]:
        """Find the smallest available spot compatible with the vehicle."""
        compatible_spots = [s for s in self.spots if s.can_fit(vehicle)]
        if not compatible_spots:
            return None
        return min(compatible_spots, key=lambda s: s.size)

    @property
    def available_spots_count(self) -> int:
        return sum(1 for s in self.spots if not s.is_occupied)

    @property
    def total_spots_count(self) -> int:
        return len(self.spots)


class PricingStrategy(ABC):
    """Abstract strategy for dynamic fee calculation."""

    @abstractmethod
    def calculate_fee(
        self, ticket: Ticket, exit_time: float, occupancy_ratio: float
    ) -> float:
        ...


class DynamicPricingStrategy(PricingStrategy):
    """Dynamic pricing using duration, vehicle rate multiplier, and surge pricing."""

    def __init__(
        self,
        base_hourly_rate: float = 10.0,
        surge_threshold: float = 0.8,
        surge_multiplier: float = 1.5,
    ) -> None:
        self.base_hourly_rate = base_hourly_rate
        self.surge_threshold = surge_threshold
        self.surge_multiplier = surge_multiplier

    def calculate_fee(
        self, ticket: Ticket, exit_time: float, occupancy_ratio: float
    ) -> float:
        duration_seconds = max(0.0, exit_time - ticket.entry_time)
        hours = max(1, math.ceil(duration_seconds / 3600.0))
        surge = self.surge_multiplier if occupancy_ratio >= self.surge_threshold else 1.0
        return round(
            hours * self.base_hourly_rate * ticket.vehicle.rate_multiplier * surge, 2
        )


class ParkingLot:
    """Multi-level parking lot managing spots, vehicle allocation, and billing."""

    def __init__(
        self,
        levels_config: List[Dict[SpotSize, int]],
        pricing_strategy: Optional[PricingStrategy] = None,
    ) -> None:
        self.levels = [
            ParkingLevel(idx + 1, cfg) for idx, cfg in enumerate(levels_config)
        ]
        self.pricing_strategy: PricingStrategy = (
            pricing_strategy if pricing_strategy is not None else DynamicPricingStrategy()
        )
        self.active_tickets: Dict[str, Ticket] = {}

    @property
    def total_capacity(self) -> int:
        return sum(lvl.total_spots_count for lvl in self.levels)

    @property
    def total_available_spots(self) -> int:
        return sum(lvl.available_spots_count for lvl in self.levels)

    @property
    def occupancy_ratio(self) -> float:
        if self.total_capacity == 0:
            return 0.0
        occupied = self.total_capacity - self.total_available_spots
        return occupied / self.total_capacity

    def park(self, vehicle: Vehicle) -> Optional[Ticket]:
        """Park vehicle in the lowest available level with a suitable spot."""
        for level in self.levels:
            spot = level.find_best_spot(vehicle)
            if spot and spot.park(vehicle):
                ticket_id = f"TICKET-{uuid.uuid4().hex[:8].upper()}"
                ticket = Ticket(
                    ticket_id=ticket_id,
                    vehicle=vehicle,
                    level_number=level.level_number,
                    spot_id=spot.spot_id,
                    entry_time=time.time(),
                )
                self.active_tickets[ticket_id] = ticket
                return ticket
        return None

    def unpark(self, ticket_id: str, exit_time: Optional[float] = None) -> float:
        """Unpark vehicle, vacate the spot, and return the calculated parking fee."""
        if ticket_id not in self.active_tickets:
            raise KeyError(f"Invalid ticket ID: {ticket_id}")

        ticket = self.active_tickets.pop(ticket_id)
        current_exit_time = exit_time if exit_time is not None else time.time()

        level = self.levels[ticket.level_number - 1]
        spot = next(s for s in level.spots if s.spot_id == ticket.spot_id)
        spot.vacate()

        return self.pricing_strategy.calculate_fee(
            ticket, current_exit_time, self.occupancy_ratio
        )
