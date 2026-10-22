# Problem 01: Type-Strict Config Loader

## 1. What This Solution Does (The 30-Second Pitch)
This module implements a zero-dependency, runtime type-enforcing configuration loader built on Python 3.11+ standard library primitives. In financial backends like Stripe or core payroll platforms like Rippling, configuration errors (e.g., passing a string port `"5432"` or a boolean `True` instead of integer `1`) can cause catastrophic runtime crashes or subtle security bypasses downstream.

While external libraries like Pydantic solve this, top-tier interviewers frequently forbid third-party dependencies to test whether a candidate genuinely understands:
- How Python's type system is constructed under the hood.
- How to resolve forward references and inspect typing metadata at runtime.
- How to enforce data integrity invariants recursively on primitives, generics (`list[T]`, `dict[K, V]`), and unions (`T | None`).

**Core Invariants Enforced:**
1. **Zero-Coercion Runtime Validation:** Types must match their annotated specification strictly on instantiation; no silent casting.
2. **Recursive Generic Inspection:** Container contents (`list[str]`, `dict[str, int]`) are validated item-by-item down to primitive leaves.
3. **Subclass Safety:** Prevents standard Python type leakage (e.g., rejecting `bool` when `int` is expected, despite `issubclass(bool, int)` being `True`).

---

## 2. How to Think About This Problem (First-Principles Mental Model)

### The Trigger
Reach for this pattern when the interviewer says:
> *"We need a strongly-typed configuration or DTO class using standard Python dataclasses, but it must strictly validate field types and nested collections at runtime without installing Pydantic or Marshmallow."*

### Why Naive Approaches Fail
- **Naive `isinstance(val, expected)` fails on generics:** Running `isinstance(["a", "b"], list[str])` immediately raises `TypeError: Subscripted generics cannot be used with class and instance checks`.
- **Naive `isinstance(True, int)` passes silently:** In Python, `bool` inherits from `int`. If a port expects an `int` and someone passes `True`, naive `isinstance(val, int)` evaluates to `True`, creating a subtle bug.
- **Reading `cls.__annotations__` directly fails on inherited or forward-referenced types:** Accessing `__annotations__` directly yields raw strings if `from __future__ import annotations` is present, or misses base class attributes. `typing.get_type_hints(cls)` must be used instead.

### The Architecture
```
StrictConfig.__post_init__()
       │
       ▼
typing.get_type_hints(self.__class__)
       │
       ▼ (Iterate field_name, expected_type)
_validate_type(value, expected_type, field_name)
       ├── Any ──> Pass
       ├── Union / types.UnionType ──> Try each branch; pass if any succeed
       ├── type(None) ──> Assert value is None
       ├── list[T] ──> Assert isinstance(val, list) -> Recursively validate each item
       ├── dict[K, V] ──> Assert isinstance(val, dict) -> Recursively validate keys & values
       ├── int Guard ──> If expected is int and type(val) is bool -> Raise TypeError
       └── Concrete Class ──> isinstance(val, expected)
```

---

## 3. How to Read the Code (`solution.py` Walkthrough)

### `_validate_type(val: Any, expected: Any, field_name: str) -> None` (Lines 18–76)
This is the recursive workhorse.
- **Lines 22–23 (`get_origin`, `get_args`):** Deconstructs typing constructs. For `list[str]`, `get_origin(list[str])` returns `list`, while `get_args(list[str])` returns `(str,)`.
- **Lines 26–37 (Union & Python 3.10+ `UnionType`):** Handles both `typing.Union[int, str]` and modern pipe syntax `int | None` (`types.UnionType`). It iterates through candidate types in `args`. If at least one branch validates without raising `TypeError`, the value is valid. If all branches fail, it raises a comprehensive `TypeError`.
- **Lines 39–43 (NoneType Handling):** Explicitly checks for `type(None)` to support `Optional` fields and `None` defaults.
- **Lines 46–64 (Generic Collections):** Checks the base container type (`list` or `dict`), then extracts the generic type arguments (`args`) and recursively calls `_validate_type` on every member, formatting the failure path (e.g., `tags[1]` or `metadata['max_conn']`).
- **Lines 66–68 (The Bool Trap):** `if expected is int and isinstance(val, bool): raise TypeError(...)`. This prevents `True` or `False` from passing as valid integers.
- **Lines 70–76 (Concrete Types):** Fallback for standard non-generic types (`str`, `float`, concrete dataclass instances).

### `StrictConfig` (Lines 79–88)
- **Line 79 (`@dataclass(kw_only=True)`):** `kw_only=True` enforces explicit keyword arguments on instantiation, a mandatory best practice in financial APIs to eliminate positional argument transposition bugs.
- **Lines 83–88 (`__post_init__`):** Executes immediately after standard dataclass initialization. Calls `get_type_hints(self.__class__)` to resolve all annotations across the class hierarchy and triggers `_validate_type` on every field.

---

## 4. How to Write It in a Live Interview (Step-by-Step Execution Order)

### Step 1: Skeleton & Core Data Structures (Mins 0–10)
State your approach out loud:
> *"I'll implement a `StrictConfig` base class using `@dataclass(kw_only=True)`. In `__post_init__`, we'll inspect the resolved type hints using `typing.get_type_hints` and pass each field to a recursive validator `_validate_type` that decomposes generics with `get_origin` and `get_args`."*

Write the skeleton:
```python
from dataclasses import dataclass
from typing import Any, get_args, get_origin, get_type_hints
import types

def _validate_type(val: Any, expected: Any, field_name: str) -> None:
    pass

@dataclass(kw_only=True)
class StrictConfig:
    def __post_init__(self) -> None:
        for name, hint in get_type_hints(self.__class__).items():
            _validate_type(getattr(self, name), hint, name)
```

### Step 2: The Happy Path Core Logic (Mins 10–22)
Implement primitive checking and collection unwrapping:
- Unpack `origin = get_origin(expected)` and `args = get_args(expected)`.
- If `origin is None`, handle standard `isinstance(val, expected)`.
- If `origin is list`, check `isinstance(val, list)` and iterate over elements with `_validate_type(item, args[0], ...)`.
- If `origin is dict`, check `isinstance(val, dict)` and validate both `args[0]` (key) and `args[1]` (value).

### Step 3: Edge Cases, Concurrency & Safety Invariants (Mins 22–35)
Now layer on the Senior/Staff safety guards:
- Support `Union` and Python 3.10+ pipe syntax: `origin is Union or origin is types.UnionType`.
- Handle `type(None)` cleanly for `Optional` / `T | None`.
- Insert the integer vs. boolean guard: `if expected is int and isinstance(val, bool): raise TypeError(...)`.
- Construct clear, diagnostic error messages indicating the exact nested path that failed.

### Step 4: Verification Driver (Mins 35–45)
Write a clean `DatabaseConfig` subclass in `if __name__ == "__main__":` testing:
1. Happy path instantiation with nested collections and optional fields.
2. Direct primitive mismatch (`host=127001`).
3. The `bool`-as-`int` edge case (`port=True`).
4. Nested list violation (`tags=["valid", 123]`).
5. Nested dict value violation (`metadata={"conn": "infinite"}`).

---

## 5. Must-Memorize Syntax & Idioms (The Cheat Sheet)

```python
# 1. Unpacking generic type origins and type parameters
origin = get_origin(hint)  # list[str] -> list; int | None -> types.UnionType
args = get_args(hint)      # list[str] -> (str,); dict[str, int] -> (str, int)

# 2. Resolving all inherited class annotations cleanly
hints = get_type_hints(cls)  # Evaluates forward refs and traverses MRO

# 3. Matching both typing.Union and Python 3.10+ union pipe syntax
import types
from typing import Union
is_union = origin is Union or origin is types.UnionType

# 4. Keyword-only dataclass declaration
@dataclass(kw_only=True)
class SafeConfig:
    host: str
    port: int = 5432
```

---

## 6. Common Traps & Follow-Up Curveballs

### 3 Mistakes That Fail the Interview
1. **Calling `isinstance(val, expected)` on subscripted generics:** Directly calling `isinstance([1], list[int])` crashes at runtime with `TypeError`. You must inspect `get_origin(expected)`.
2. **Missing `types.UnionType`:** Checking only `origin is typing.Union` will crash or misidentify modern Python 3.10+ `int | None` syntax. You must check both `Union` and `types.UnionType`.
3. **Allowing `bool` to pass as `int`:** In Python, `isinstance(False, int)` returns `True`. Failing to check `type(val) is bool` when `expected is int` demonstrates a lack of deep Python runtime knowledge.

### 2 Bar-Raiser Follow-Ups
1. **"How would you support nested `StrictConfig` instances automatically from raw dicts?"**
   *Answer:* In `_validate_type`, check if `isinstance(expected, type) and issubclass(expected, StrictConfig)`. If `isinstance(val, dict)`, automatically instantiate `val = expected(**val)` before validation.
2. **"How does this perform under high throughput (e.g., parsing 50k configs/sec)?"**
   *Answer:* `get_type_hints()` involves dynamic class inspection and string evaluation, which is expensive. Cache the result of `get_type_hints(cls)` in a class-level `_TYPE_CACHE` dictionary or `lru_cache` so inspection only occurs once per class rather than once per instance.
