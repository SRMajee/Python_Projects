# Problem 03: Property Validation Micro-ORM

## 1. What This Solution Does (The 30-Second Pitch)
This module builds a lightweight, zero-dependency declarative micro-ORM model layer powered by Python's Data Descriptor Protocol (`__get__`, `__set__`, `__set_name__`) and `__init_subclass__`. In systems like Stripe's ledger or Rippling's employee directory, domain models must guarantee field-level invariants (e.g., non-negative employee IDs, strict username regex patterns, and string length bounds) directly upon assignment.

Instead of hand-writing repetitive `@property` getters and setters on every class, reusable field descriptors (`IntegerField`, `StringField`) encapsulate validation, default value assignment, and nullability enforcement cleanly at the class level.

**Core Invariants Enforced:**
1. **Zero Memory Leaks:** Instance state is stored exclusively within the instance's own `__dict__`, eliminating the need for `WeakKeyDictionary` or global descriptor dicts.
2. **Eager Descriptor Validation:** Assignments on init and runtime mutations (`user.age = 25`) trigger immediate type, range, length, and regex validation.
3. **Declarative Metaprogramming without Metaclasses:** `__init_subclass__` automatically discovers descriptors and supports deep MRO model inheritance.

---

## 2. How to Think About This Problem (First-Principles Mental Model)

### The Trigger
Reach for this pattern when the interviewer says:
> *"Design a declarative model framework like Django or SQLAlchemy fields from scratch. Create reusable fields (`IntegerField`, `StringField`) that validate data on assignment, support defaults and nullability, and avoid memory leaks across multiple instances."*

### Why Naive Approaches Fail
- **Storing values on `self` (the Descriptor):** If a descriptor stores `self.value = value`, that single descriptor instance is shared across *all* instances of the class! Changing `user1.age = 20` would overwrite `user2.age` to `20`.
- **Using a dictionary inside the descriptor `self.values = {}`:** Storing `self.values[instance] = value` prevents garbage collection of `instance` because the descriptor retains a strong reference to it, leaking memory.
- **Using Metaclasses unnecessarily:** Writing a full `type` metaclass adds 40 lines of boilerplate and makes the candidate look out of touch with modern Python 3.6+ features like `__init_subclass__` and `__set_name__`.

### The Architecture
```
UserAccount (class)
  ├── id = IntegerField()        ──> Shared descriptor on class
  └── username = StringField()   ──> Shared descriptor on class

user1 = UserAccount(id=101)
  └── user1.__dict__ = {
        "_field_id": 101,        <── Data stored on instance __dict__
        "_field_username": "alice"
      }
```

---

## 3. How to Read the Code (`solution.py` Walkthrough)

### `Field` Base Descriptor (Lines 22–54)
- **Lines 31–34 (`__set_name__`):** Called automatically when the containing class is created. It receives `name` (e.g. `"username"`) and constructs `self.storage_key = f"_field_{name}"`.
- **Lines 36–39 (`__get__`):**
  If accessed via the class (`UserAccount.id`), `instance` is `None`—it returns the descriptor itself. If accessed on an instance (`user1.id`), it fetches directly from `instance.__dict__`.
- **Lines 41–49 (`__set__`):**
  Intercepts every assignment. If value is `None`, it validates against `self.nullable`. Otherwise, it delegates to `self.validate(value)` before updating `instance.__dict__`.

### Subclass Descriptors (Lines 56–114)
- **`IntegerField` (Lines 56–84):** Validates that `type(value) is int` (disallowing `bool`), and enforces `min_value` / `max_value` bounds.
- **`StringField` (Lines 86–114):** Validates `isinstance(value, str)`, checks `len(value) <= max_length`, and executes compiled regex full-matching.

### `Model` Base Class (Lines 116–154)
- **Lines 121–134 (`__init_subclass__`):** Traverses the class MRO in reverse to inherit fields from parent models, then inspects `cls.__dict__` to register all `Field` instances into `cls._fields`.
- **Lines 135–146 (`__init__`):** Rejects unknown kwargs. For known fields, assigns passed values or defaults through `setattr(self, field_name, ...)`, thereby routing through descriptor validation.
- **Lines 147–153 (`to_dict` and `__repr__`):** Serializes registered fields into clean dictionaries and strings.

---

## 4. How to Write It in a Live Interview (Step-by-Step Execution Order)

### Step 1: Skeleton & Core Data Structures (Mins 0–10)
Establish the descriptor protocol and `__set_name__` mechanics:
```python
class ValidationError(ValueError): pass

class Field:
    def __init__(self, *, nullable=False, default=None):
        self.nullable = nullable; self.default = default
    def __set_name__(self, owner, name):
        self.name = name; self.storage_key = f"_field_{name}"
    def __get__(self, instance, owner=None):
        if instance is None: return self
        return instance.__dict__.get(self.storage_key, self.default)
    def __set__(self, instance, value):
        ...
```

### Step 2: The Happy Path Core Logic (Mins 10–22)
Implement `IntegerField` and `StringField`:
- In `IntegerField.validate`, guard with `type(val) is int` and min/max checks.
- In `StringField.validate`, guard with `isinstance(val, str)`, max length, and `re.fullmatch`.
- Implement `Model.__init__` reading `cls._fields`.

### Step 3: Edge Cases, Concurrency & Safety Invariants (Mins 22–35)
Now add the bar-raising design details:
- Implement `Model.__init_subclass__` traversing `reversed(cls.__mro__)` to properly inherit fields across model hierarchies.
- Implement strict nullability handling in `Field.__set__`: raise `ValidationError` if `not self.nullable and value is None`.
- Reject unexpected keyword arguments in `Model.__init__` with descriptive `TypeError`.

### Step 4: Verification Driver (Mins 35–45)
Write comprehensive assertions in `if __name__ == "__main__":`:
1. Happy path instantiation and `to_dict()` equality.
2. Verify cross-instance isolation (`user1.age` must not mutate `user2.age`).
3. Out-of-bounds integer check (`id=0`).
4. Type coercion guard (`user1.id = True`).
5. Regex failure and nullability violations.

---

## 5. Must-Memorize Syntax & Idioms (The Cheat Sheet)

```python
# 1. Descriptor Protocol with automatic name capture
class Descriptor:
    def __set_name__(self, owner, name):
        self.storage_key = f"_{name}"
    def __get__(self, instance, owner=None):
        return instance.__dict__.get(self.storage_key) if instance else self
    def __set__(self, instance, value):
        instance.__dict__[self.storage_key] = value

# 2. Schema discovery across inheritance without metaclasses
def __init_subclass__(cls, **kwargs):
    super().__init_subclass__(**kwargs)
    cls._fields = {k: v for k, v in cls.__dict__.items() if isinstance(v, Field)}

# 3. Direct instance dictionary bypass (avoids infinite recursion in descriptors)
instance.__dict__[self.storage_key] = value
```

---

## 6. Common Traps & Follow-Up Curveballs

### 3 Mistakes That Fail the Interview
1. **Calling `setattr(instance, self.name, value)` inside `__set__`:** This triggers the descriptor's `__set__` again, resulting in `RecursionError: maximum recursion depth exceeded`. You must write to `instance.__dict__[self.storage_key]`.
2. **Forgetting `if instance is None: return self` in `__get__`:** If someone accesses `UserAccount.id`, `instance` is `None`. Without this check, it tries to access `None.__dict__` and crashes with an `AttributeError`.
3. **Sharing mutable defaults across instances:** Passing `default=[]` will share the same list instance across all model records. Always use immutable defaults or factory callables.

### 2 Bar-Raiser Follow-Ups
1. **"How would you support Foreign Key relationships or nested sub-models?"**
   *Answer:* Introduce a `ForeignKey(target_model)` or `EmbeddedField(ModelClass)` descriptor. Inside `__set__`, enforce `isinstance(value, target_model)`. Inside `to_dict()`, recursively call `value.to_dict()`.
2. **"How does this interact with `__slots__`?"**
   *Answer:* By default, descriptors write to `instance.__dict__`. If the model defines `__slots__`, `instance.__dict__` does not exist. To support `__slots__`, `__init_subclass__` must automatically allocate slot names for each field's private storage key.
