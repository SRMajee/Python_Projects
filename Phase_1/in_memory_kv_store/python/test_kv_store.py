import time
import unittest
from kv_store import InMemoryKVStore, Entry, BaseKeyValueStore


class TestInMemoryKVStore(unittest.TestCase):
    def setUp(self) -> None:
        self.store = InMemoryKVStore()

    def test_inheritance(self) -> None:
        self.assertIsInstance(self.store, BaseKeyValueStore)

    def test_basic_set_get(self) -> None:
        self.store.set("user:1", {"name": "Alice"})
        self.assertEqual(self.store.get("user:1"), {"name": "Alice"})
        self.assertIsNone(self.store.get("non_existent"))

    def test_exists_and_delete(self) -> None:
        self.store.set("counter", 42)
        self.assertTrue(self.store.exists("counter"))
        self.assertTrue(self.store.delete("counter"))
        self.assertFalse(self.store.exists("counter"))
        self.assertFalse(self.store.delete("counter"))
        self.assertIsNone(self.store.get("counter"))

    def test_ttl_expiration(self) -> None:
        self.store.set("temp", "value", ttl=0.05)
        self.assertTrue(self.store.exists("temp"))
        self.assertEqual(self.store.get("temp"), "value")
        time.sleep(0.06)
        self.assertFalse(self.store.exists("temp"))
        self.assertIsNone(self.store.get("temp"))

    def test_transaction_commit(self) -> None:
        self.store.set("balance", 100)
        self.store.begin()
        self.store.set("balance", 150)
        self.store.set("temp", "tx")
        self.assertEqual(self.store.get("balance"), 150)
        self.assertEqual(self.store.get("temp"), "tx")
        self.store.commit()

        self.assertEqual(self.store.get("balance"), 150)
        self.assertEqual(self.store.get("temp"), "tx")

    def test_transaction_rollback(self) -> None:
        self.store.set("balance", 100)
        self.store.begin()
        self.store.set("balance", 200)
        self.store.delete("balance")
        self.assertIsNone(self.store.get("balance"))
        self.store.rollback()

        self.assertEqual(self.store.get("balance"), 100)

    def test_nested_transaction_commit_then_outer_rollback(self) -> None:
        self.store.set("a", 1)
        self.store.begin()
        self.store.set("a", 2)
        self.store.begin()
        self.store.set("a", 3)
        self.assertEqual(self.store.get("a"), 3)
        self.store.commit()  # Commits into parent transaction layer

        self.assertEqual(self.store.get("a"), 3)
        self.store.rollback()  # Rolls back outer layer
        self.assertEqual(self.store.get("a"), 1)

    def test_nested_transaction_inner_rollback(self) -> None:
        self.store.set("a", 1)
        self.store.begin()
        self.store.set("a", 2)
        self.store.begin()
        self.store.set("a", 3)
        self.store.rollback()  # Discards inner layer
        self.assertEqual(self.store.get("a"), 2)
        self.store.commit()
        self.assertEqual(self.store.get("a"), 2)

    def test_context_manager_commit(self) -> None:
        with self.store.transaction():
            self.store.set("token", "secret123")
        self.assertEqual(self.store.get("token"), "secret123")

    def test_context_manager_exception_rollback(self) -> None:
        self.store.set("status", "pending")
        with self.assertRaises(ValueError):
            with self.store.transaction():
                self.store.set("status", "done")
                raise ValueError("Operation failed")
        self.assertEqual(self.store.get("status"), "pending")

    def test_errors_without_active_transaction(self) -> None:
        with self.assertRaises(RuntimeError):
            self.store.commit()
        with self.assertRaises(RuntimeError):
            self.store.rollback()

    def test_entry_dataclass_methods(self) -> None:
        entry = Entry(value="foo", expiry=100.0)
        self.assertFalse(entry.is_expired(current_time=99.0))
        self.assertTrue(entry.is_expired(current_time=100.0))
        self.assertTrue(entry.is_expired(current_time=101.0))
        permanent_entry = Entry(value="bar")
        self.assertFalse(permanent_entry.is_expired(current_time=9999999999.0))


if __name__ == "__main__":
    unittest.main()
