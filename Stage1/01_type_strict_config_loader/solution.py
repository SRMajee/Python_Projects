"""
Problem 01: Type-Strict Config Loader
Phase: Modern Data Modeling (Target: 50-80 LOC)

Staff Engineer Design Notes:
- Standard library runtime type enforcement without Pydantic.
- Evaluates resolved typing annotations via `get_type_hints`, `get_origin`, and `get_args`.
- Recursively validates primitives, unions (including Python 3.10+ UnionType `X | Y`),
  and nested generics (`list[T]`, `dict[K, V]`).
- Prevents standard Python type coercion traps (e.g., bool subclassing int).
"""

from dataclasses import dataclass
import types
from typing import Any, Union, get_args, get_origin, get_type_hints


def _validate_type(val: Any, expected: Any, field_name: str) -> None:
    if expected is Any:
        return

    origin = get_origin(expected)
    args = get_args(expected)

    # Handle Union types: typing.Union and Python 3.10+ types.UnionType (T1 | T2)
    if origin is Union or origin is types.UnionType:
        for branch in args:
            try:
                _validate_type(val, branch, field_name)
                return
            except TypeError:
                continue
        type_names = " | ".join(getattr(a, "__name__", str(a)) for a in args)
        raise TypeError(
            f"Field '{field_name}' must match one of ({type_names}), "
            f"got {type(val).__name__} with value {val!r}"
        )

    # Handle None / NoneType
    if expected is type(None):
        if val is not None:
            raise TypeError(f"Field '{field_name}' expected None, got {type(val).__name__}")
        return

    # Handle list generics
    if origin is list or expected is list:
        if not isinstance(val, list):
            raise TypeError(f"Field '{field_name}' expected list, got {type(val).__name__}")
        if args:
            elem_type = args[0]
            for idx, item in enumerate(val):
                _validate_type(item, elem_type, f"{field_name}[{idx}]")
        return

    # Handle dict generics
    if origin is dict or expected is dict:
        if not isinstance(val, dict):
            raise TypeError(f"Field '{field_name}' expected dict, got {type(val).__name__}")
        if args:
            k_type, v_type = args
            for k, v in val.items():
                _validate_type(k, k_type, f"{field_name}.key({k!r})")
                _validate_type(v, v_type, f"{field_name}[{k!r}]")
        return

    # Guard: Python bool is an int subclass; strictly forbid bool when int is expected
    if expected is int and isinstance(val, bool):
        raise TypeError(f"Field '{field_name}' expected int, got bool ({val})")

    # Handle standard concrete classes / nested dataclasses
    if not isinstance(val, expected):
        expected_name = getattr(expected, "__name__", str(expected))
        raise TypeError(
            f"Field '{field_name}' expected {expected_name}, "
            f"got {type(val).__name__} with value {val!r}"
        )


@dataclass(kw_only=True)
class StrictConfig:
    """Base configuration class enforcing strict runtime types on initialization."""

    def __post_init__(self) -> None:
        hints = get_type_hints(self.__class__)
        for name, expected_type in hints.items():
            val = getattr(self, name)
            _validate_type(val, expected_type, name)


# ---------------------------------------------------------------------------
# Verification & Test Scenarios
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from dataclasses import field

    @dataclass(kw_only=True)
    class DatabaseConfig(StrictConfig):
        host: str
        port: int
        timeout: float | None = None
        tags: list[str] = field(default_factory=list)
        metadata: dict[str, int] = field(default_factory=dict)

    # 1. Happy path: valid types with default arguments
    cfg = DatabaseConfig(
        host="db.internal.stripe.com",
        port=5432,
        timeout=2.5,
        tags=["primary", "us-east-1"],
        metadata={"connections": 100, "retries": 3},
    )
    assert cfg.host == "db.internal.stripe.com"
    assert cfg.port == 5432
    assert cfg.timeout == 2.5
    assert cfg.tags == ["primary", "us-east-1"]

    # 2. Happy path: Optional field as None
    cfg_nullable = DatabaseConfig(host="localhost", port=3306, timeout=None)
    assert cfg_nullable.timeout is None

    # 3. Failure: primitive type mismatch (int passed where str expected)
    try:
        DatabaseConfig(host=127001, port=5432)  # type: ignore
        assert False, "Should have raised TypeError for int host"
    except TypeError as e:
        assert "Field 'host' expected str" in str(e)

    # 4. Failure: bool passed where int is expected (bool subclassing int trap)
    try:
        DatabaseConfig(host="localhost", port=True)  # type: ignore
        assert False, "Should have raised TypeError for bool port"
    except TypeError as e:
        assert "expected int, got bool" in str(e)

    # 5. Failure: nested list element type mismatch
    try:
        DatabaseConfig(host="localhost", port=5432, tags=["valid", 123])  # type: ignore
        assert False, "Should have raised TypeError for non-string item in tags list"
    except TypeError as e:
        assert "tags[1]" in str(e)

    # 6. Failure: nested dict value type mismatch
    try:
        DatabaseConfig(host="localhost", port=5432, metadata={"max_conn": "infinite"})  # type: ignore
        assert False, "Should have raised TypeError for non-int dict value"
    except TypeError as e:
        assert "metadata['max_conn']" in str(e)

    print("01_type_strict_config_loader: All assertions passed successfully.")
