import unittest
from parking_lot import (
    Bus,
    Car,
    DynamicPricingStrategy,
    Motorcycle,
    ParkingLevel,
    ParkingLot,
    ParkingSpot,
    PricingStrategy,
    SpotSize,
    Ticket,
    Vehicle,
    VehicleFactory,
)


class TestVehicleHierarchyAndFactory(unittest.TestCase):
    """Test vehicle inheritance and the extensible VehicleFactory."""

    def test_vehicle_inheritance(self) -> None:
        moto = Motorcycle("MOTO-1")
        car = Car("CAR-1")
        bus = Bus("BUS-1")

        self.assertIsInstance(moto, Vehicle)
        self.assertIsInstance(car, Vehicle)
        self.assertIsInstance(bus, Vehicle)

        self.assertEqual(moto.spot_size, SpotSize.SMALL)
        self.assertEqual(moto.rate_multiplier, 0.5)

        self.assertEqual(car.spot_size, SpotSize.MEDIUM)
        self.assertEqual(car.rate_multiplier, 1.0)

        self.assertEqual(bus.spot_size, SpotSize.LARGE)
        self.assertEqual(bus.rate_multiplier, 2.0)

    def test_factory_creation(self) -> None:
        car = VehicleFactory.create_vehicle("car", "CAR-101")
        self.assertIsInstance(car, Car)
        self.assertEqual(car.license_plate, "CAR-101")

        moto = VehicleFactory.create_vehicle("MOTORCYCLE", "MOTO-202")
        self.assertIsInstance(moto, Motorcycle)

        bus = VehicleFactory.create_vehicle("Bus", "BUS-303")
        self.assertIsInstance(bus, Bus)

    def test_factory_unknown_vehicle(self) -> None:
        with self.assertRaises(ValueError):
            VehicleFactory.create_vehicle("helicopter", "COPTER-999")

    def test_factory_extensibility_with_new_vehicle_type(self) -> None:
        # Define a new vehicle type without touching the base codebase
        class ElectricTruck(Vehicle):
            @property
            def spot_size(self) -> SpotSize:
                return SpotSize.LARGE

            @property
            def rate_multiplier(self) -> float:
                return 1.8

        VehicleFactory.register_vehicle_type("electric_truck", ElectricTruck)

        ev_truck = VehicleFactory.create_vehicle("electric_truck", "EV-TRUCK-1")
        self.assertIsInstance(ev_truck, ElectricTruck)
        self.assertEqual(ev_truck.spot_size, SpotSize.LARGE)
        self.assertEqual(ev_truck.rate_multiplier, 1.8)


class TestParkingSpotAndLevel(unittest.TestCase):
    """Test individual parking spots and parking levels."""

    def test_spot_sizing_compatibility(self) -> None:
        small_spot = ParkingSpot(1, SpotSize.SMALL)
        med_spot = ParkingSpot(2, SpotSize.MEDIUM)
        large_spot = ParkingSpot(3, SpotSize.LARGE)

        moto = Motorcycle("M-1")
        car = Car("C-1")
        bus = Bus("B-1")

        # Motorcycle fits everywhere
        self.assertTrue(small_spot.can_fit(moto))
        self.assertTrue(med_spot.can_fit(moto))
        self.assertTrue(large_spot.can_fit(moto))

        # Car only fits MEDIUM or LARGE
        self.assertFalse(small_spot.can_fit(car))
        self.assertTrue(med_spot.can_fit(car))
        self.assertTrue(large_spot.can_fit(car))

        # Bus only fits LARGE
        self.assertFalse(small_spot.can_fit(bus))
        self.assertFalse(med_spot.can_fit(bus))
        self.assertTrue(large_spot.can_fit(bus))

    def test_best_spot_selection(self) -> None:
        # Level with 1 LARGE and 1 SMALL spot
        level = ParkingLevel(1, {SpotSize.LARGE: 1, SpotSize.SMALL: 1})
        moto = Motorcycle("M-1")

        # Best fit for motorcycle should be the SMALL spot, leaving LARGE available
        best_spot = level.find_best_spot(moto)
        self.assertIsNotNone(best_spot)
        self.assertEqual(best_spot.size, SpotSize.SMALL)


class TestParkingLotOperations(unittest.TestCase):
    """Test multi-level parking lot management and parking lifecycle."""

    def setUp(self) -> None:
        # 2 levels: Level 1 has 1 SMALL, 1 MEDIUM. Level 2 has 1 MEDIUM, 1 LARGE.
        config = [
            {SpotSize.SMALL: 1, SpotSize.MEDIUM: 1},
            {SpotSize.MEDIUM: 1, SpotSize.LARGE: 1},
        ]
        self.lot = ParkingLot(config)

    def test_lot_initialization(self) -> None:
        self.assertEqual(self.lot.total_capacity, 4)
        self.assertEqual(self.lot.total_available_spots, 4)
        self.assertEqual(self.lot.occupancy_ratio, 0.0)

    def test_parking_allocation_across_levels(self) -> None:
        car1 = Car("CAR-1")
        car2 = Car("CAR-2")

        ticket1 = self.lot.park(car1)
        self.assertIsNotNone(ticket1)
        self.assertEqual(ticket1.level_number, 1)

        # Level 1 has no more MEDIUM/LARGE spots, so car2 goes to Level 2
        ticket2 = self.lot.park(car2)
        self.assertIsNotNone(ticket2)
        self.assertEqual(ticket2.level_number, 2)

    def test_lot_full_rejection(self) -> None:
        bus1 = Bus("BUS-1")
        bus2 = Bus("BUS-2")

        ticket1 = self.lot.park(bus1)
        self.assertIsNotNone(ticket1)

        # Only 1 LARGE spot exists across all levels; second bus should fail
        ticket2 = self.lot.park(bus2)
        self.assertIsNone(ticket2)

    def test_unpark_and_vacate(self) -> None:
        car = Car("CAR-1")
        ticket = self.lot.park(car)
        self.assertIsNotNone(ticket)
        self.assertEqual(self.lot.total_available_spots, 3)

        fee = self.lot.unpark(ticket.ticket_id, exit_time=ticket.entry_time + 3600)
        self.assertEqual(fee, 10.0)
        self.assertEqual(self.lot.total_available_spots, 4)

        # Trying to unpark again should raise KeyError
        with self.assertRaises(KeyError):
            self.lot.unpark(ticket.ticket_id)


class TestDynamicPricing(unittest.TestCase):
    """Test hourly pricing and dynamic surge pricing based on occupancy."""

    def test_hourly_rounding_and_vehicle_multipliers(self) -> None:
        lot = ParkingLot([{SpotSize.SMALL: 10, SpotSize.MEDIUM: 10, SpotSize.LARGE: 10}])

        # Car for 2 hours and 1 minute (should round up to 3 hours @ $10/hr = $30.00)
        car = Car("CAR-1")
        t_car = lot.park(car)
        fee_car = lot.unpark(t_car.ticket_id, exit_time=t_car.entry_time + 7260)
        self.assertEqual(fee_car, 30.0)

        # Motorcycle for 1 hour (1 hr * $10 * 0.5 = $5.00)
        moto = Motorcycle("MOTO-1")
        t_moto = lot.park(moto)
        fee_moto = lot.unpark(t_moto.ticket_id, exit_time=t_moto.entry_time + 3600)
        self.assertEqual(fee_moto, 5.0)

        # Bus for 2 hours (2 hrs * $10 * 2.0 = $40.00)
        bus = Bus("BUS-1")
        t_bus = lot.park(bus)
        fee_bus = lot.unpark(t_bus.ticket_id, exit_time=t_bus.entry_time + 7200)
        self.assertEqual(fee_bus, 40.0)

    def test_surge_pricing_trigger(self) -> None:
        # Small lot with 5 spots: 80% occupancy is 4 occupied spots
        lot = ParkingLot(
            [{SpotSize.MEDIUM: 5}],
            pricing_strategy=DynamicPricingStrategy(
                base_hourly_rate=10.0,
                surge_threshold=0.8,
                surge_multiplier=1.5,
            ),
        )

        tickets = [lot.park(Car(f"C-{i}")) for i in range(5)]
        self.assertAlmostEqual(lot.occupancy_ratio, 1.0)

        # Unparking ticket[0] while 4 cars remain parked (occupancy = 4/5 = 80%)
        # Surge multiplier of 1.5x should apply: 1 hr * $10 * 1.0 * 1.5 = $15.00
        fee = lot.unpark(tickets[0].ticket_id, exit_time=tickets[0].entry_time + 3600)
        self.assertEqual(fee, 15.0)

    def test_custom_pricing_strategy_injection(self) -> None:
        class FlatRatePricing(PricingStrategy):
            def calculate_fee(
                self, ticket: Ticket, exit_time: float, occupancy_ratio: float
            ) -> float:
                return 50.0

        lot = ParkingLot([{SpotSize.MEDIUM: 2}], pricing_strategy=FlatRatePricing())
        ticket = lot.park(Car("FLAT-1"))
        fee = lot.unpark(ticket.ticket_id)
        self.assertEqual(fee, 50.0)


if __name__ == "__main__":
    unittest.main()
