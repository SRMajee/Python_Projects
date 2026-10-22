# Problem 02: Command Parser Engine

## 1. What This Solution Does (The 30-Second Pitch)
This module implements a production-grade CLI and webhook command dispatch engine using Python 3.10+ Structural Pattern Matching (`match` / `case`). In modern event-driven architectures (such as Stripe webhook processors or Rippling employee lifecycle event dispatchers), heterogeneous JSON payloads and CLI commands arrive with deeply nested structures, varied schemas, and optional flags.

Instead of writing brittle cascades of `if "key" in data and isinstance(...)` statements, this engine uses declarative pattern matching to:
1. Match sequences (CLI syntax), nested mappings (JSON payloads), and recursive batches in a unified dispatch pipeline.
2. Extract and bind variables conditionally using guard clauses (`if`).
3. Return strongly typed, immutable dataclass commands (`CreateUserCommand`, `ChargeCommand`, `DeployCommand`) while isolating malformed payloads from unrecognized commands.

**Core Invariants Enforced:**
1. **Schema Conformity:** Commands are only constructed if required nested keys exist and satisfy runtime value and type guards.
2. **Defensive Ordering:** More specific patterns (e.g., flags like `--dry-run`) take precedence over greedy wildcards.
3. **Deterministic Error Boundary:** Missing/invalid payload fields raise `InvalidPayloadError`, while unmapped operations raise `UnknownCommandError`.

---

## 2. How to Think About This Problem (First-Principles Mental Model)

### The Trigger
Reach for this pattern when the interviewer says:
> *"We have an incoming stream of polymorphic payloads (CLI argument lists, nested webhook dictionaries, batch commands). Parse them into domain command objects and reject bad payloads cleanly."*

### Why Naive Approaches Fail
- **Dictionary "Digging" Hell:** Writing `payload.get("payload", {}).get("user", {}).get("email")` quickly degrades into 50 lines of unreadable nested checks where missing keys produce silent `None` bugs instead of crisp schema errors.
- **Pattern Matching Misconceptions:** Candidates often don't realize that in Python `match/case`, mapping patterns `{ "k": v }` automatically allow extra unlisted keys by default (unlike sequences). Adding `**_` in mapping patterns causes a `SyntaxError`.
- **Greedy Sequence Wildcards:** In sequence matching, `["deploy", env, *services]` greedily consumes trailing tokens like `"--dry-run"`. The specific flag pattern must be declared *before* the general wildcard.

### The Architecture
```
parse_command(payload)
      │
      ├── ["deploy", ("staging"|"production"), *services, "--dry-run"] ──> DeployCommand(dry_run=True)
      ├── ["deploy", ("staging"|"production"), *services] ───────────────> DeployCommand(dry_run=False)
      ├── {"action": "user:create", "payload": {"user": {...}}} ──────────> CreateUserCommand
      ├── {"action": "payment:charge", "payload": {...}} ────────────────> ChargeCommand
      ├── {"action": "batch", "payload": {"items": [...]}} ──────────────> BatchCommand(recursive)
      ├── Guarded Fallbacks (bad role, negative amount) ─────────────────> raise InvalidPayloadError
      ├── {"action": str(unknown)} ──────────────────────────────────────> raise UnknownCommandError
      └── _ ─────────────────────────────────────────────────────────────> raise InvalidPayloadError
```

---

## 3. How to Read the Code (`solution.py` Walkthrough)

### Command DTOs & Custom Exceptions (Lines 19–54)
- **Lines 19–28:** Explicit exception hierarchy distinguishing between `UnknownCommandError` (route does not exist) and `InvalidPayloadError` (route recognized, but data failed validation).
- **Lines 31–54:** Immutable command dataclasses (`@dataclass(frozen=True)`). Once parsed, commands are immutable value objects.

### `parse_command(payload: Any) -> Any` (Lines 57–118)
- **Lines 61–65 (Sequence Pattern with Precedence):**
  Matches CLI argument lists. Notice that line 61 (`*services, "--dry-run"`) is matched *before* line 64 (`*services`). If line 64 came first, `*services` would consume `"--dry-run"` as a service string.
- **Lines 67–78 (Deeply Nested Mapping Pattern):**
  Deconstructs `{"action": "user:create", "payload": {"user": {"name": str(name), ...}}}`. Notice `str(name)`: this matches and asserts type without an explicit `isinstance` call, and the guard clause `if role in VALID_ROLES and "@" in email` guarantees domain validity.
- **Lines 81–82 (Guarded Diagnostic Fallback):**
  Matches `{"action": "user:create", ...}` when `role not in VALID_ROLES`. This allows targeted error messaging rather than falling all the way through to a generic "invalid command" error.
- **Lines 86–97 (Payment Charge Pattern):**
  Matches nested customer ID, positive integer amount, and converts currency to uppercase.
- **Lines 108–110 (Recursive Batch Pattern):**
  Recursively calls `parse_command` on each child item, assembling a `BatchCommand`.
- **Lines 113–117 (Wildcard Fallbacks):**
  If `"action"` is a recognized key type but didn't match any valid schema, it triggers `UnknownCommandError`. Any remaining malformed envelope triggers `InvalidPayloadError`.

---

## 4. How to Write It in a Live Interview (Step-by-Step Execution Order)

### Step 1: Skeleton & Core Data Structures (Mins 0–10)
Define the error classes and target dataclasses first:
```python
from dataclasses import dataclass
from typing import Any

class CommandParseError(Exception): pass
class UnknownCommandError(CommandParseError): pass
class InvalidPayloadError(CommandParseError): pass

@dataclass(frozen=True)
class CreateUserCommand:
    name: str; email: str; role: str

@dataclass(frozen=True)
class DeployCommand:
    environment: str; services: list[str]; dry_run: bool

def parse_command(payload: Any) -> Any:
    match payload:
        case _:
            raise InvalidPayloadError(f"Malformed payload: {payload!r}")
```

### Step 2: The Happy Path Core Logic (Mins 10–22)
Add sequence and mapping patterns:
- Implement the CLI list case: `case ["deploy", env, *services]: ...`
- Implement nested JSON dict case: `case {"action": "user:create", "payload": {"user": {"name": str(name), ...}}}: ...`
- Verify that valid inputs instantiate and return target dataclasses.

### Step 3: Edge Cases, Concurrency & Safety Invariants (Mins 22–35)
Now add the nuances that separate Senior from Staff:
- Add the `--dry-run` sequence pattern *above* the general deploy pattern.
- Add guards: `if role in VALID_ROLES`, `if amount > 0`.
- Add diagnostic fallback cases for invalid values (negative amount, unsupported currency) to raise `InvalidPayloadError` with actionable messages.
- Implement the recursive batch case: `case {"action": "batch", "payload": {"items": list(items)}}: ...`

### Step 4: Verification Driver (Mins 35–45)
Write `assert` scenarios in `if __name__ == "__main__":`:
1. CLI sequence with flags (`--dry-run`).
2. Deeply nested JSON mapping.
3. Recursive batch payload containing both.
4. Rejection of invalid role and negative monetary amounts.
5. Rejection of unknown actions.

---

## 5. Must-Memorize Syntax & Idioms (The Cheat Sheet)

```python
# 1. Matching sequences with prefix, rest, and suffix
case ["deploy", ("staging" | "production") as env, *services, "--dry-run"]:
    ...

# 2. Matching type and binding variable in one step
case {"user": {"name": str(name), "age": int(age)}} if age >= 18:
    ...

# 3. Matching multiple literal choices with 'as' binding
case ("USD" | "EUR" | "GBP") as currency:
    ...

# 4. Partial dictionary matching (ignores unmentioned keys automatically)
case {"action": "pay", "amount": int(amt)}:  # extra keys in subject dict are ignored!
    ...
```

---

## 6. Common Traps & Follow-Up Curveballs

### 3 Mistakes That Fail the Interview
1. **Adding `**_` to mapping patterns:** Writing `case {"action": "pay", **_}:` is a syntax error in Python. Dict patterns automatically permit additional keys unless matched against `{}`.
2. **Incorrect Sequence Pattern Precedence:** Putting `case ["cmd", *args]:` before `case ["cmd", *args, "--flag"]:` will cause the second case to be dead code—the wildcard swallows `"--flag"`.
3. **Not Casting Unpacked Slices:** In `case [op, *items]:`, `items` is bound as a `list` or `slice`. Always ensure type safety by casting `list(items)` if constructing a dataclass requiring a concrete `list`.

### 2 Bar-Raiser Follow-Ups
1. **"How would you allow commands to register their own patterns dynamically without modifying one massive `match/case` function?"**
   *Answer:* Use a registry of pattern handlers or an AST visitor. While `match/case` is compiled statically, you can match on top-level envelope `{"action": str(action), "payload": dict(p)}` and delegate to a `HANDLER_REGISTRY[action](p)` table.
2. **"How do you handle schema versioning (e.g., v1 vs v2 payloads)?"**
   *Answer:* Match on envelope metadata: `case {"version": 2, "action": "user:create", ...}:` before `case {"action": "user:create", ...}:` (defaulting to v1).
