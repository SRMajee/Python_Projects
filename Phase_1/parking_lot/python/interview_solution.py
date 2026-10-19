"""
Parking Lot Design - Concise Interview Solution (Python)

1. Primary Capabilities:
- Vehicle hierarchy (Motorcycle, Car, Bus) with spot size requirements.
- Multi-level spot allocation assigning the smallest available compatible spot.
- Dynamic fee calculation with occupancy surge pricing.

2. Error Handling:
- Returns None or raises ValueError if the lot is full for the vehicle type.
- Validates ticket existence before processing vehicle exit.

3. Out Of Scope:
- Hardware barrier gates and RFID license plate readers.
- Payment gateway integration (Stripe / Razorpay).
- Pre-reservation or slot booking algorithms.
"""

from enum import IntEnum
import time
from typing import Dict, List, Optional


class SpotSize(IntEnum):
    SMALL = 1
    MEDIUM = 2
    LARGE = 3


class Vehicle:
    def __init__(self, plate: str, size: SpotSize, rate_multiplier: float) -> None:
        self.plate = plate
        self.size = size
        self.rate_multiplier = rate_multiplier


class ParkingLot:
    def __init__(self, spots_per_size: Dict[SpotSize, int], base_rate: float = 20.0) -> None:
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

        # Surge pricing if occupancy >= 80%
        occupied = sum(sum(1 for s in slots if s is not None) for slots in self.spots.values())
        total = sum(len(slots) for slots in self.spots.values())
        surge = 1.5 if (occupied / total) >= 0.8 else 1.0
        return round(simulated_hours * self.base_rate * vehicle.rate_multiplier * surge, 2)


if __name__ == "__main__":
    lot = ParkingLot({SpotSize.SMALL: 1, SpotSize.MEDIUM: 1, SpotSize.LARGE: 1})
    car = Vehicle("KA-01-1234", SpotSize.MEDIUM, 1.0)
    tid = lot.park(car)
    assert tid is not None
    fee = lot.unpark(tid, 2.0)
    assert fee == 40.0
    print("Interview Python ParkingLot passed!")
