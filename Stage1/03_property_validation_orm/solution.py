"""
Problem 03: Property Validation Micro-ORM
Phase: Advanced OOP (Target: 100-150 LOC)

Staff Engineer Design Notes:
- Idiomatic Python Data Descriptors (`__get__`, `__set__`, `__set_name__`).
- Zero memory leaks: State is stored on the instance's private attributes
  (namespaced via `__set_name__`), avoiding weakref/dict-in-descriptor traps.
- `__init_subclass__` automatically discovers and indexes field schemas,
  supporting class inheritance without metaclass ceremony.
- Comprehensive runtime validation for types, ranges, lengths, regex, and nullability.
"""

import re
from typing import Any


class ValidationError(ValueError):
    """Raised when field descriptor validation fails."""


class Field:
    """Base descriptor enforcing attribute namespacing, storage, and nullability."""

    def __init__(self, *, nullable: bool = False, default: Any = None) -> None:
        self.nullable = nullable
        self.default = default
        self.name: str = ""
        self.storage_key: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        # Storing state directly on the target instance prevents descriptor memory leaks
        self.storage_key = f"_field_{name}"

    def __get__(self, instance: Any, owner: type | None = None) -> Any:
        if instance is None:
            return self
        return instance.__dict__.get(self.storage_key, self.default)

    def __set__(self, instance: Any, value: Any) -> None:
        if value is None:
            if not self.nullable:
                raise ValidationError(f"Field '{self.name}' is non-nullable; cannot set to None")
            instance.__dict__[self.storage_key] = None
            return

        self.validate(value)
        instance.__dict__[self.storage_key] = value

    def validate(self, value: Any) -> None:
        """Override in subclasses to enforce concrete validation rules."""
        pass


class IntegerField(Field):
    """Descriptor validating strict integer type and optional bounds."""

    def __init__(
        self,
        *,
        min_value: int | None = None,
        max_value: int | None = None,
        nullable: bool = False,
        default: int | None = None,
    ) -> None:
        super().__init__(nullable=nullable, default=default)
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value: Any) -> None:
        if type(value) is not int:  # Explicitly disallow bool
            raise ValidationError(
                f"Field '{self.name}' expects int, got {type(value).__name__} ({value!r})"
            )
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                f"Field '{self.name}' must be >= {self.min_value}, got {value}"
            )
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                f"Field '{self.name}' must be <= {self.max_value}, got {value}"
            )


class StringField(Field):
    """Descriptor validating string length and optional regex patterns."""

    def __init__(
        self,
        *,
        max_length: int | None = None,
        regex: str | None = None,
        nullable: bool = False,
        default: str | None = None,
    ) -> None:
        super().__init__(nullable=nullable, default=default)
        self.max_length = max_length
        self.regex = re.compile(regex) if regex else None

    def validate(self, value: Any) -> None:
        if not isinstance(value, str):
            raise ValidationError(
                f"Field '{self.name}' expects str, got {type(value).__name__} ({value!r})"
            )
        if self.max_length is not None and len(value) > self.max_length:
            raise ValidationError(
                f"Field '{self.name}' exceeds max_length={self.max_length} (length={len(value)})"
            )
        if self.regex is not None and not self.regex.fullmatch(value):
            raise ValidationError(
                f"Field '{self.name}' with value '{value}' failed regex pattern {self.regex.pattern}"
            )


class Model:
    """Micro-ORM base model discovering descriptors via __init_subclass__."""

    _fields: dict[str, Field] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Inherit fields from parent models, then add current class fields
        fields: dict[str, Field] = {}
        for base in reversed(cls.__mro__):
            if hasattr(base, "_fields"):
                fields.update(base._fields)

        for attr_name, attr_val in cls.__dict__.items():
            if isinstance(attr_val, Field):
                fields[attr_name] = attr_val

        cls._fields = fields

    def __init__(self, **kwargs: Any) -> None:
        for key in kwargs:
            if key not in self._fields:
                raise TypeError(f"Unknown attribute '{key}' for model {self.__class__.__name__}")

        # Set values or apply defaults through descriptors to trigger validation
        for field_name, field_obj in self._fields.items():
            if field_name in kwargs:
                setattr(self, field_name, kwargs[field_name])
            else:
                setattr(self, field_name, field_obj.default)

    def to_dict(self) -> dict[str, Any]:
        """Serialize model instance fields into a primitive dictionary."""
        return {field_name: getattr(self, field_name) for field_name in self._fields}

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={getattr(self, k)!r}" for k in self._fields)
        return f"{self.__class__.__name__}({attrs})"


# ---------------------------------------------------------------------------
# Verification & Test Scenarios
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    class UserAccount(Model):
        id = IntegerField(min_value=1)
        username = StringField(max_length=20, regex=r"^[a-z0-9_]+$")
        age = IntegerField(min_value=18, max_value=120, nullable=True, default=None)
        status = StringField(default="active")

    # 1. Happy path instantiation and attribute assignment
    user1 = UserAccount(id=101, username="alice_stripe", age=29)
    assert user1.id == 101
    assert user1.username == "alice_stripe"
    assert user1.age == 29
    assert user1.status == "active"
    assert user1.to_dict() == {
        "id": 101,
        "username": "alice_stripe",
        "age": 29,
        "status": "active",
    }

    # 2. Verify independent instance state (No cross-instance descriptor leaks)
    user2 = UserAccount(id=102, username="bob_rippling")
    user2.age = 35
    assert user1.age == 29
    assert user2.age == 35

    # 3. Validation Failure: Integer out of bounds
    try:
        UserAccount(id=0, username="charlie")
        assert False, "Should have failed min_value validation for id"
    except ValidationError as e:
        assert "must be >= 1" in str(e)

    # 4. Validation Failure: Bool passed as int
    try:
        user1.id = True  # type: ignore
        assert False, "Should have rejected bool for IntegerField"
    except ValidationError as e:
        assert "expects int, got bool" in str(e)

    # 5. Validation Failure: String exceeding max_length
    try:
        user1.username = "a" * 21
        assert False, "Should have rejected username exceeding max length"
    except ValidationError as e:
        assert "exceeds max_length" in str(e)

    # 6. Validation Failure: String violating regex
    try:
        user1.username = "Alice-With-Dashes!"
        assert False, "Should have rejected username failing regex"
    except ValidationError as e:
        assert "failed regex pattern" in str(e)

    # 7. Validation Failure: Setting None on non-nullable field
    try:
        user1.username = None
        assert False, "Should have rejected None on non-nullable field"
    except ValidationError as e:
        assert "is non-nullable" in str(e)

    # 8. Setting None on nullable field succeeds
    user1.age = None
    assert user1.age is None

    print("03_property_validation_orm: All assertions passed successfully.")
