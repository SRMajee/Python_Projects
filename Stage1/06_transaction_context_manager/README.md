# Problem 06: Transaction Context Manager with Nested Savepoints

## 1. What This Solution Does (The 30-Second Pitch)
This module implements an atomic transactional key-value store supporting arbitrary nested sub-transactions (savepoints) via both class-based (`__enter__`, `__exit__`) and generator-based (`@contextmanager`) context managers. In core banking, ledger, and payroll services at Stripe and Rippling, database mutations must satisfy ACID atomicity: a multi-step operation (e.g., deducting a customer balance and crediting a merchant) must either succeed entirely or roll back completely on failure.

This engine isolates working state, captures isolated snapshots on transaction entry, applies changes speculatively, and automatically rolls back mutations to the pre-transaction snapshot if an exception occurs—without swallowing the exception.

**Core Invariants Enforced:**
1. **Atomic Rollback:** If an exception is raised anywhere inside a `with db.transaction():` block, state reverts exactly to its pre-transaction snapshot.
2. **Arbitrary Savepoint Nesting:** Inner transactions can fail and roll back independently while allowing enclosing outer transactions to catch the error and continue.
3. **Transparent Exception Propagation:** `__exit__` always returns `False` (or re-raises), ensuring exceptions propagate to callers for upstream observability.

---

## 2. How to Think About This Problem (First-Principles Mental Model)

### The Trigger
Reach for this pattern when the interviewer says:
> *"Implement an in-memory transactional database or state machine using Python context managers. It must support nested transactions (savepoints), roll back changes automatically on error, commit on success, and never silently swallow errors."*

### Why Naive Approaches Fail
- **Single-Level Backup Flags:** Saving a single `self._backup = dict(self._data)` fails immediately when transactions are nested. An inner rollback destroys the outer transaction's baseline state. A stack of snapshots (`_savepoint_stack = []`) is strictly required.
- **Returning `True` from `__exit__`:** Returning `True` in `__exit__` suppresses the exception. In transactional systems, swallowing exceptions hides data corruption from upstream application logic. It must return `False`.
- **Shallow Reference Mutations:** Simply storing `self._data` directly on the stack stores a reference to the mutable dict. When `self.set()` mutates `self._data`, it mutates the snapshot! You must snapshot via `dict(self._data)` or copy.

### The Architecture
```
db = TransactionalStore()  # _data = {"balance": 100}

with db.transaction():     # [Savepoint 1] Pushes {"balance": 100} to stack
    db.set("balance", 80)
    
    with db.transaction(): # [Savepoint 2] Pushes {"balance": 80} to stack
        db.set("balance", 10)
        raise Error()      # Exception raised!
                           # [Rollback 2] Pops {"balance": 80} -> Restores _data = {"balance": 80}
                           
    # Outer block resumes with {"balance": 80}
    db.set("balance", 70)  # [Commit 1] Pops Savepoint 1 -> _data = {"balance": 70}
```

---

## 3. How to Read the Code (`solution.py` Walkthrough)

### `TransactionalStore` (Lines 20–42)
- **Line 25 (`_savepoint_stack`):** List acting as a LIFO stack storing snapshot dictionaries.
- **Line 36 (`snapshot`):** `return dict(self._data)`. Creates an independent shallow copy of the state mapping.
- **Line 39 (`transaction`):** Factory method returning a new `Transaction` instance bound to `self`.

### Class-Based `Transaction` (Lines 44–63)
- **Lines 50–53 (`__enter__`):**
  Pushes `self.store.snapshot()` onto `self.store._savepoint_stack` and returns `self.store` so caller can use `with db.transaction() as tx:`.
- **Lines 55–62 (`__exit__`):**
  Pops the topmost snapshot.
  - If `exc_type is not None`: an exception occurred inside the block. Restores `self.store._data = snapshot`.
  - Returns `False`: This is Python's context manager contract to **re-raise/propagate** the active exception.

### Generator-Based `generator_transaction` (Lines 65–76)
- **Lines 65–76 (`@contextmanager`):**
  Demonstrates Python's functional context manager protocol.
  - Setup before `yield`: pushes snapshot.
  - `yield store`: transfers execution to caller's `with` body.
  - `except BaseException`: restores snapshot and calls `raise`.
  - `else`: on clean completion, discards the snapshot from the stack.

---

## 4. How to Write It in a Live Interview (Step-by-Step Execution Order)

### Step 1: Skeleton & Core Data Structures (Mins 0–10)
Define `TransactionalStore` with state dict and stack:
```python
class TransactionalStore:
    def __init__(self):
        self._data = {}
        self._savepoint_stack = []
    def get(self, key, default=None): return self._data.get(key, default)
    def set(self, key, value): self._data[key] = value
    def snapshot(self): return dict(self._data)
```

### Step 2: The Happy Path Core Logic (Mins 10–22)
Implement class-based `Transaction`:
```python
class Transaction:
    def __init__(self, store): self.store = store
    def __enter__(self):
        self.store._savepoint_stack.append(self.store.snapshot())
        return self.store
    def __exit__(self, exc_type, exc_val, exc_tb):
        snapshot = self.store._savepoint_stack.pop()
        if exc_type is not None:
            self.store._data = snapshot
        return False
```

### Step 3: Edge Cases, Concurrency & Safety Invariants (Mins 22–35)
Address subtle Staff-level edge cases:
- Confirm `__exit__` returns `False` explicitly (do not omit or return True).
- Add generator-based alternative using `@contextmanager` to prove mastery of both paradigms.
- Catch `BaseException` in `@contextmanager` rather than `Exception` so cancellations and KeyboardInterrupts still roll back cleanly before propagating.

### Step 4: Verification Driver (Mins 35–45)
Write multi-layered transaction tests in `if __name__ == "__main__":`:
1. Commit test: clean `with db.transaction():` persists mutations.
2. Abort test: verify `try/with` restores initial state when an exception fires.
3. Nested savepoint test: verify inner transaction rollback does not roll back preceding outer transaction mutations.
4. Verify identical behavior under the generator-based implementation.

---

## 5. Must-Memorize Syntax & Idioms (The Cheat Sheet)

```python
# 1. Class-based Context Manager Protocol
class ContextManager:
    def __enter__(self):
        # setup state
        return resource
    def __exit__(self, exc_type, exc_val, exc_tb):
        # teardown state
        return False  # False propagates exceptions; True swallows them!

# 2. Generator-based Context Manager Pattern
from contextlib import contextmanager

@contextmanager
def managed_resource():
    setup()
    try:
        yield resource
    except BaseException:
        rollback()
        raise
    else:
        commit()
```

---

## 6. Common Traps & Follow-Up Curveballs

### 3 Mistakes That Fail the Interview
1. **Returning `True` from `__exit__`:** Returning `True` swallows all exceptions, hiding syntax errors and critical runtime exceptions from the caller. Always return `False`.
2. **Mutating the Snapshot in Place:** Appending `self._data` without creating a new copy `dict(self._data)` pushes a pointer to the live dict. Subsequent `set()` calls mutate the saved state.
3. **Leaking Savepoints on Exceptions:** Forgetting to `.pop()` the savepoint during rollback leaves stale snapshots on the stack, corrupting subsequent transactions.

### 2 Bar-Raiser Follow-Ups
1. **"How would you optimize this for massive databases where copying the entire dictionary on every savepoint is too expensive?"**
   *Answer:* Instead of full snapshots (copy-on-write), record a **Delta Log** (Undo Log) on the transaction stack. When `set(k, v)` is called, record `("SET", k, old_val)` in the active savepoint. On rollback, iterate the undo log backwards to reverse only modified keys in $O(\Delta)$ time and space.
2. **"How do you make this thread-safe or support concurrent transactions?"**
   *Answer:* Use Thread-Local storage (`threading.local()`) for transaction stacks, or implement Multi-Version Concurrency Control (MVCC) where each transaction reads from a committed version snapshot and detects write-write conflicts on commit.
