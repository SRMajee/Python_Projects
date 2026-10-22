"""
Problem 02: Command Parser Engine
Phase: Modern Data Modeling (Target: 80-100 LOC)

Staff Engineer Design Notes:
- Idiomatic Python 3.10+ Structural Pattern Matching (`match` / `case`).
- Evaluates sequence patterns, nested mapping patterns, and value guards.
- Extracts parameters into strongly typed command DTOs without manual dictionary digging.
- Provides granular error classification for unknown actions vs. malformed payloads.
"""

from dataclasses import dataclass
from typing import Any, Sequence

SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP"}
VALID_ROLES = {"admin", "member", "billing"}


class CommandParseError(Exception):
    """Base error for command parsing failures."""


class UnknownCommandError(CommandParseError):
    """Raised when an unrouted or unsupported command name is encountered."""


class InvalidPayloadError(CommandParseError):
    """Raised when a known command payload has missing keys or invalid guards."""


@dataclass(frozen=True)
class CreateUserCommand:
    name: str
    email: str
    role: str


@dataclass(frozen=True)
class ChargeCommand:
    amount_cents: int
    currency: str
    customer_id: str


@dataclass(frozen=True)
class DeployCommand:
    environment: str
    services: list[str]
    dry_run: bool


@dataclass(frozen=True)
class BatchCommand:
    commands: list[Any]


def parse_command(payload: Any) -> Any:
    """Route and parse deeply nested CLI / JSON payloads into typed command objects."""
    match payload:
        # Sequence Pattern: CLI-style with --dry-run flag first (more specific)
        case ["deploy", ("staging" | "production") as env, *services, "--dry-run"] if services:
            return DeployCommand(environment=env, services=list(services), dry_run=True)

        case ["deploy", ("staging" | "production") as env, *services] if services:
            return DeployCommand(environment=env, services=list(services), dry_run=False)

        # Mapping Pattern: Create User with nested 'user' dict and valid role guard
        case {
            "action": "user:create",
            "payload": {
                "user": {
                    "name": str(name),
                    "email": str(email),
                    "role": str(role),
                }
            },
        } if role in VALID_ROLES and "@" in email:
            return CreateUserCommand(name=name, email=email, role=role)

        # Guarded Failure for User Create: invalid role or bad email format
        case {"action": "user:create", "payload": {"user": {"role": str(role)}}} if role not in VALID_ROLES:
            raise InvalidPayloadError(f"Role '{role}' is invalid; must be one of {VALID_ROLES}")

        # Mapping Pattern: Payment charge with nested customer ID and currency validation
        case {
            "action": "payment:charge",
            "payload": {
                "amount": int(amount),
                "currency": str(currency),
                "customer": {"id": str(cust_id)},
            },
        } if amount > 0 and currency.upper() in SUPPORTED_CURRENCIES:
            return ChargeCommand(
                amount_cents=amount,
                currency=currency.upper(),
                customer_id=cust_id,
            )

        # Guarded Failure for Payment Charge: non-positive amount
        case {"action": "payment:charge", "payload": {"amount": int(amount)}} if amount <= 0:
            raise InvalidPayloadError(f"Charge amount must be positive, got {amount}")

        # Guarded Failure for Payment Charge: unsupported currency
        case {"action": "payment:charge", "payload": {"currency": str(curr)}} if curr.upper() not in SUPPORTED_CURRENCIES:
            raise InvalidPayloadError(f"Unsupported currency: {curr}")

        # Recursive Batch Pattern
        case {"action": "batch", "payload": {"items": list(items)}} if items:
            sub_commands = [parse_command(item) for item in items]
            return BatchCommand(commands=sub_commands)

        # Missing payload container or unknown action
        case {"action": str(action)}:
            raise UnknownCommandError(f"Unknown or unparseable command action: '{action}'")

        case _:
            raise InvalidPayloadError(f"Malformed command envelope structure: {payload!r}")


# ---------------------------------------------------------------------------
# Verification & Test Scenarios
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # 1. Sequence CLI deploy command
    cli_cmd = parse_command(["deploy", "production", "auth-api", "billing-worker"])
    assert isinstance(cli_cmd, DeployCommand)
    assert cli_cmd.environment == "production"
    assert cli_cmd.services == ["auth-api", "billing-worker"]
    assert cli_cmd.dry_run is False

    # 2. Sequence CLI with flag
    cli_dry = parse_command(["deploy", "staging", "search-svc", "--dry-run"])
    assert isinstance(cli_dry, DeployCommand)
    assert cli_dry.dry_run is True

    # 3. Deeply nested User Create mapping pattern
    user_payload = {
        "action": "user:create",
        "payload": {
            "user": {"name": "Alice Smith", "email": "alice@rippling.com", "role": "admin"}
        },
    }
    user_cmd = parse_command(user_payload)
    assert isinstance(user_cmd, CreateUserCommand)
    assert user_cmd.name == "Alice Smith"
    assert user_cmd.role == "admin"

    # 4. Nested payment charge with valid positive amount
    charge_payload = {
        "action": "payment:charge",
        "payload": {
            "amount": 4999,
            "currency": "usd",
            "customer": {"id": "cus_9x018ab3"},
        },
    }
    charge_cmd = parse_command(charge_payload)
    assert isinstance(charge_cmd, ChargeCommand)
    assert charge_cmd.amount_cents == 4999
    assert charge_cmd.currency == "USD"
    assert charge_cmd.customer_id == "cus_9x018ab3"

    # 5. Batch command processing
    batch_payload = {
        "action": "batch",
        "payload": {"items": [charge_payload, user_payload]},
    }
    batch_cmd = parse_command(batch_payload)
    assert isinstance(batch_cmd, BatchCommand)
    assert len(batch_cmd.commands) == 2
    assert isinstance(batch_cmd.commands[0], ChargeCommand)
    assert isinstance(batch_cmd.commands[1], CreateUserCommand)

    # 6. Failure: Guard clause rejecting invalid role
    try:
        parse_command({
            "action": "user:create",
            "payload": {"user": {"name": "Bob", "email": "bob@stripe.com", "role": "superuser"}},
        })
        assert False, "Should fail on invalid role"
    except InvalidPayloadError as e:
        assert "Role 'superuser' is invalid" in str(e)

    # 7. Failure: Guard clause rejecting negative charge
    try:
        parse_command({
            "action": "payment:charge",
            "payload": {"amount": -10, "currency": "USD", "customer": {"id": "cus_123"}},
        })
        assert False, "Should fail on negative amount"
    except InvalidPayloadError as e:
        assert "amount must be positive" in str(e)

    # 8. Failure: Unknown action
    try:
        parse_command({"action": "unsupported:op", "payload": {}})
        assert False, "Should fail on unknown action"
    except UnknownCommandError as e:
        assert "unsupported:op" in str(e)

    print("02_command_parser_engine: All assertions passed successfully.")
