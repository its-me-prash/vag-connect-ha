# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""v2.2.0 Phase 5b PR #19/20 — Pydantic v2 dual-write validation foundation.

**Read-only "dual-write" pattern.** Builds the validation layer in
v2.2.0 so v3.0.0 can remove the legacy dataclass parsing path with
confidence.

## What this module does

Provides ``validate_response(raw, model_cls)`` — a defensive helper
that:

1. Attempts to validate the raw JSON dict against a Pydantic v2 model
2. On success: returns the validated model instance (for diagnostics)
3. On schema mismatch: logs at DEBUG level + returns None (no raise)
4. On Pydantic-not-importable: returns None (no raise)

Callers ALWAYS keep their existing dataclass parsing path as the
canonical source of vehicle state. The Pydantic call sits ALONGSIDE
the dataclass parse as a non-blocking diagnostic — its purpose is
to surface schema drift in the logs so we can iterate on the model
definitions BEFORE the v3.0.0 cut-over.

## Why "dual-write"

Phase 5b sets up Pydantic validation but does NOT remove the legacy
parsing. Two reads happen on every coordinator update:

1. Legacy dataclass parse (canonical — entity state comes from here)
2. Pydantic validate (diagnostic — log-only, never affects entities)

When v3.0.0 ships, the legacy parse will be removed and Pydantic
will become the canonical source — but only AFTER weeks of dual-
write telemetry confirm the models match production responses.

## Failsafe

- **Pydantic-not-importable** (rare — HA Core 2024+ ships pydantic
  v2 mandatorily, but defensive in case a user has a stripped-down
  install): returns None silently
- **Schema mismatch**: logs raw exception at DEBUG (NOT WARNING —
  don't spam users while we tune the models), returns None
- **Any other unexpected error**: catch-all returns None
- The caller's existing dataclass parse runs unchanged regardless

## Why this won't break anything

The function NEVER raises. Worst case it returns None. The caller's
existing dataclass parse is unaffected. Even if every Pydantic call
silently fails for a week, users see zero behaviour change.

"In two years, we will all look back on this dataclass code and say
'D'oh — why didn't we use Pydantic from the start?'"
— Homer Simpson, on technical debt
"""

from __future__ import annotations

import logging
from typing import Any, TypeVar

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


def _pydantic_available() -> bool:
    """Check if Pydantic v2 is importable.

    HA Core 2024+ ships Pydantic v2 mandatorily, but we keep this
    defensive in case a user has a stripped-down install or runs the
    parser in a minimal environment (e.g. our test runner without
    HA).
    """
    try:
        import pydantic  # noqa: F401, PLC0415

        return True
    except ImportError:
        return False


def validate_response(
    raw: Any,
    model_cls: type[T],
    *,
    context: str = "",
) -> T | None:
    """Validate ``raw`` against ``model_cls`` (a Pydantic v2 BaseModel).

    Returns the parsed model on success, None on any failure mode.
    NEVER raises — safe to call from any parser hot-path.

    Args:
        raw: Raw response dict from the backend.
        model_cls: A ``pydantic.BaseModel`` subclass.
        context: Optional string identifier for debug logs (e.g.
            "vw_eu/charging.batteryStatus"). Helps when sifting
            through dual-write telemetry.

    Returns:
        Validated model instance, or None on any failure.
    """
    if not _pydantic_available():
        return None
    if raw is None:
        return None
    try:
        # Pydantic v2 uses ``model_validate`` for dict → instance.
        # The cast through Any is to satisfy mypy without forcing
        # the import-time pydantic dependency on the module level.
        return model_cls.model_validate(raw)  # type: ignore[attr-defined,no-any-return]
    except Exception as err:  # noqa: BLE001
        # Schema mismatch — log at DEBUG (NOT warning, don't spam
        # while we tune the models). The caller's existing dataclass
        # parse handles the data; this is diagnostic only.
        _LOGGER.debug(
            "Pydantic validation mismatch%s: %s (type=%s)",
            f" [{context}]" if context else "",
            err,
            type(err).__name__,
        )
        return None


def is_pydantic_available() -> bool:
    """Public accessor — useful for tests + diagnostics.

    Production users on HA Core 2024+ will always get True. Returns
    False in dev environments without HA / Pydantic installed.
    """
    return _pydantic_available()
