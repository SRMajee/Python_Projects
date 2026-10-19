"""Tests for Ride-Sharing Engine."""
import threading
import unittest
from ride_engine import RideSharingEngine, TripState, DriverState


class TestRideSharingEngine(unittest.TestCase):
    def setUp(self):
        self.engine = RideSharingEngine(grid_cell_size=1.0)
        self.engine.register_driver("d1", "Alice", 0.0, 0.0)
        self.engine.register_driver("d2", "Bob", 5.0, 5.0)
        self.engine.register_driver("d3", "Carol", 10.0, 10.0)
        self.engine.register_rider("r1", "Dave", 1.0, 1.0)

    def test_request_and_match(self):
        trip = self.engine.request_ride("r1", 0.5, 0.5, 8.0, 8.0)
        self.assertEqual(trip.state, TripState.REQUESTED)
        driver = self.engine.match_driver(trip.id)
        self.assertIsNotNone(driver)
        self.assertEqual(driver.id, "d1")  # nearest
        self.assertEqual(trip.state, TripState.MATCHED)

    def test_full_trip_lifecycle(self):
        trip = self.engine.request_ride("r1", 0.0, 0.0, 5.0, 5.0)
        self.engine.match_driver(trip.id)
        self.engine.start_trip(trip.id)
        self.assertEqual(trip.state, TripState.IN_PROGRESS)
        fare = self.engine.complete_trip(trip.id)
        self.assertEqual(trip.state, TripState.COMPLETED)
        self.assertGreater(fare, 0)

    def test_no_available_driver(self):
        # Put all drivers on trip
        for did in ["d1", "d2", "d3"]:
            self.engine._drivers[did].state = DriverState.ON_TRIP
            self.engine._grid.remove(did)
        trip = self.engine.request_ride("r1", 0.0, 0.0, 5.0, 5.0)
        driver = self.engine.match_driver(trip.id)
        self.assertIsNone(driver)

    def test_cancel_trip(self):
        trip = self.engine.request_ride("r1", 0.0, 0.0, 5.0, 5.0)
        self.engine.match_driver(trip.id)
        self.engine.cancel_trip(trip.id)
        self.assertEqual(trip.state, TripState.CANCELLED)
        self.assertEqual(trip.driver.state, DriverState.IDLE)

    def test_driver_offline(self):
        self.engine.set_driver_offline("d1")
        self.assertEqual(self.engine._drivers["d1"].state, DriverState.OFFLINE)
        trip = self.engine.request_ride("r1", 0.0, 0.0, 5.0, 5.0)
        driver = self.engine.match_driver(trip.id, max_distance=2.0)
        # d1 is offline, so d1 should not be matched
        if driver:
            self.assertNotEqual(driver.id, "d1")

    def test_update_driver_location(self):
        self.engine.update_driver_location("d1", 4.9, 4.9)
        trip = self.engine.request_ride("r1", 5.0, 5.0, 10.0, 10.0)
        driver = self.engine.match_driver(trip.id, max_distance=1.0)
        self.assertIsNotNone(driver)
        self.assertIn(driver.id, {"d1", "d2"})

    def test_duplicate_registration(self):
        with self.assertRaises(ValueError):
            self.engine.register_driver("d1", "Dup", 0, 0)
        with self.assertRaises(ValueError):
            self.engine.register_rider("r1", "Dup", 0, 0)

    def test_invalid_state_transitions(self):
        trip = self.engine.request_ride("r1", 0, 0, 5, 5)
        with self.assertRaises(ValueError):
            self.engine.start_trip(trip.id)  # not MATCHED yet
        self.engine.match_driver(trip.id)
        with self.assertRaises(ValueError):
            self.engine.complete_trip(trip.id)  # not IN_PROGRESS yet

    def test_thread_safety(self):
        for i in range(20):
            self.engine.register_driver(f"td{i}", f"T{i}", float(i), float(i))
            self.engine.register_rider(f"tr{i}", f"R{i}", float(i), float(i))

        results = []
        def request_and_match(idx):
            trip = self.engine.request_ride(f"tr{idx}", float(idx), float(idx), float(idx + 5), float(idx + 5))
            driver = self.engine.match_driver(trip.id, max_distance=5.0)
            results.append(driver is not None)

        threads = [threading.Thread(target=request_and_match, args=(i,)) for i in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertGreater(sum(results), 0)


if __name__ == "__main__":
    unittest.main()
