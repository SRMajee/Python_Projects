"""
Problem 06: Transaction Context Manager with Nested Savepoints
Phase: Iterators & Contexts (Target: 60-80 LOC)

Staff Engineer Design Notes:
- Atomicity & Isolation: Simulates an in-memory transactional key-value store.
- Supports arbitrary savepoint nesting (sub-transactions) via an internal state stack.
- Dual context manager paradigms:
  1. Class-based (`__enter__`, `__exit__`) for explicit state lifecycle control.
  2. Generator-based (`@contextmanager`) illustrating Python's functional context protocol.
- Strict invariant: Rollback restores pre-transaction snapshot on failure and always
  re-raises / propagates exceptions (`return False` in `__exit__`).
"""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any


class TransactionalStore:
    """In-memory KV store supporting atomic nested transactions with rollback."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._savepoint_stack: list[dict[str, Any]] = []

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def snapshot(self) -> dict[str, Any]:
        return dict(self._data)

    def transaction(self) -> "Transaction":
        """Factory for class-based transaction context manager."""
        return Transaction(self)


class Transaction:
    """Class-based transaction context manager managing savepoint lifecycle."""

    def __init__(self, store: TransactionalStore) -> None:
        self.store = store

    def __enter__(self) -> TransactionalStore:
        # Push isolated snapshot to savepoint stack
        self.store._savepoint_stack.append(self.store.snapshot())
        return self.store

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> bool:
        snapshot = self.store._savepoint_stack.pop()
        if exc_type is not None:
            # Atomically rollback to the snapshot captured at savepoint entry
            self.store._data = snapshot
            return False  # Strict requirement: Propagate exception to caller
        # Success: Changes remain committed in store._data
        return False


@contextmanager
def generator_transaction(store: TransactionalStore) -> Iterator[TransactionalStore]:
    """Generator-based context manager delivering identical atomic savepoint semantics."""
    snapshot = store.snapshot()
    store._savepoint_stack.append(snapshot)
    try:
        yield store
    except BaseException:
        store._data = store._savepoint_stack.pop()
        raise
    else:
        store._savepoint_stack.pop()


# ---------------------------------------------------------------------------
# Verification & Test Scenarios
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    db = TransactionalStore()
    db.set("balance:alice", 100)
    db.set("balance:bob", 50)

    # 1. Clean transaction commits state mutations
    with db.transaction():
        db.set("balance:alice", 80)
        db.set("balance:bob", 70)

    assert db.get("balance:alice") == 80
    assert db.get("balance:bob") == 70

    # 2. Failed transaction triggers atomic rollback without swallowing exception
    try:
        with db.transaction():
            db.set("balance:alice", 0)
            raise RuntimeError("Database connection dropped mid-write")
            db.set("balance:bob", 200)  # Unreachable
        assert False, "Should have propagated RuntimeError"
    except RuntimeError as e:
        assert "Database connection dropped" in str(e)

    # Assert balances restored to state before the aborted transaction
    assert db.get("balance:alice") == 80
    assert db.get("balance:bob") == 70

    # 3. Nested transaction savepoints: inner rolls back, outer commits
    with db.transaction():
        db.set("balance:alice", 60)
        try:
            with db.transaction():  # Nested Savepoint
                db.set("balance:alice", 10)
                db.set("balance:bob", 999)
                raise ValueError("Card declined on inner ledger update")
        except ValueError:
            pass  # Inner failure handled by outer business logic

        # Outer transaction continues with pre-inner state
        assert db.get("balance:alice") == 60
        assert db.get("balance:bob") == 70
        db.set("balance:alice", 50)

    assert db.get("balance:alice") == 50
    assert db.get("balance:bob") == 70

    # 4. Generator-based transaction validation
    with generator_transaction(db):
        db.set("balance:charlie", 300)
    assert db.get("balance:charlie") == 300

    try:
        with generator_transaction(db):
            db.set("balance:charlie", 0)
            raise KeyError("Failed in generator transaction")
    except KeyError:
        pass
    assert db.get("balance:charlie") == 300

    print("06_transaction_context_manager: All assertions passed successfully.")
