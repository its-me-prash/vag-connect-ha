# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Exceptions for the VAG Connect CARIAD API client."""

from __future__ import annotations

from enum import StrEnum


class CommandFailureReason(StrEnum):
    """Why a vehicle command failed.

    Used by the coordinator to decide whether an entity should be hidden,
    flagged as not-entitled, or just shown as temporarily unavailable.
    Three failures that look similar at the HTTP layer can have very
    different correct responses:

    - ``MISSING_CAPABILITY`` — the vehicle's VIN is not registered for the
      feature in the manufacturer backend (e.g. CUPRA Born without
      honk-and-flash). Hide the entity at next reload.
    - ``SUBSCRIPTION_EXPIRED`` — paid online-services subscription expired.
      Same vehicle would support the command if the user renewed; surface
      a clear error, do NOT hide the entity.
    - ``NOT_ENTITLED`` — free tier (e.g. We Connect Go) that never
      included remote commands. Same handling as expired but with
      different user messaging.
    - ``WRONG_API_PROFILE`` — newer model uses a different endpoint
      version. Needs the per-VIN command profile from #61.
    - ``VEHICLE_UNREACHABLE`` — car offline / asleep / out of coverage.
      Transient — entity stays available.
    - ``SPIN_REQUIRED`` — already raised as ``ServiceValidationError``
      before reaching the API; included here for completeness.
    - ``INVALID_PAYLOAD`` — our bug. Fix and ship.
    - ``BACKEND_ERROR`` — manufacturer 5xx or unexpected 4xx body.
      Transient; do not derive long-term decisions.
    - ``UNKNOWN`` — default. Don't make assumptions.
    """

    MISSING_CAPABILITY = "missing_capability"
    SUBSCRIPTION_EXPIRED = "subscription_expired"
    NOT_ENTITLED = "not_entitled"
    WRONG_API_PROFILE = "wrong_api_profile"
    VEHICLE_UNREACHABLE = "vehicle_unreachable"
    SPIN_REQUIRED = "spin_required"
    INVALID_PAYLOAD = "invalid_payload"
    BACKEND_ERROR = "backend_error"
    UNKNOWN = "unknown"


def classify_command_failure(exc: BaseException) -> CommandFailureReason:
    """Map a CARIAD ``APIError`` (or any exception) to a failure reason.

    Conservative on purpose — when in doubt return ``UNKNOWN`` or
    ``BACKEND_ERROR`` rather than ``MISSING_CAPABILITY``. The latter
    leads to entities being permanently hidden, so we only return it for
    backend responses that explicitly say so.
    """
    if not isinstance(exc, APIError):
        return CommandFailureReason.UNKNOWN

    status = getattr(exc, "status", 0) or 0
    body = str(exc).lower()

    if "missing-capability" in body or "missing_capability" in body:
        return CommandFailureReason.MISSING_CAPABILITY
    if status == 403:
        return CommandFailureReason.NOT_ENTITLED
    if status == 404:
        return CommandFailureReason.WRONG_API_PROFILE
    if status >= 500:
        return CommandFailureReason.BACKEND_ERROR
    if status == 400:
        # 400 with `internal-error` is ambiguous — could be expired
        # subscription, could be a transient backend error, could be
        # our payload. We can't tell from the HTTP layer alone, so we
        # return BACKEND_ERROR (the safe default) and let the
        # coordinator decide based on entitlement state if known.
        return CommandFailureReason.BACKEND_ERROR
    return CommandFailureReason.UNKNOWN


class CariadError(Exception):
    """Base exception for all CARIAD client errors."""


class AuthenticationError(CariadError):
    """Login failed — wrong credentials or account issue."""


class TermsAndConditionsError(AuthenticationError):
    """Terms and conditions must be accepted in the app before API access."""

    def __init__(self) -> None:
        super().__init__(
            "Terms and conditions pending. Open the brand app, sign in, and accept."
        )


class MarketingConsentError(AuthenticationError):
    """New privacy/marketing consent required."""

    def __init__(self) -> None:
        super().__init__(
            "Privacy consent required. App → Profile → Consents."
        )


class TwoFactorRequiredError(AuthenticationError):
    """2FA challenge — must be resolved once in the app."""

    def __init__(self) -> None:
        super().__init__(
            "2FA required. Sign in manually in the brand app once to confirm."
        )


class RateLimitError(CariadError):
    """Account temporarily blocked by VAG rate limiter."""

    def __init__(self) -> None:
        super().__init__(
            "Account temporarily rate-limited. Wait 15 minutes, then retry."
        )


class TokenExpiredError(CariadError):
    """Access token expired and could not be refreshed."""


class SpinError(CariadError):
    """S-PIN required or incorrect — needed for lock/unlock commands."""


class VehicleNotFoundError(CariadError):
    """VIN not found in the account garage."""

    def __init__(self, vin: str) -> None:
        super().__init__(f"Vehicle {vin} not found in account garage.")
        self.vin = vin


class VehicleCommandError(CariadError):
    """Remote command rejected or timed out."""

    def __init__(self, command: str, reason: str = "") -> None:
        msg = f"Command '{command}' failed"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)
        self.command = command


class APIError(CariadError):
    """Unexpected API response."""

    def __init__(self, status: int, url: str, body: str = "") -> None:
        super().__init__(f"API error {status} for {url}: {body[:200]}")
        self.status = status
        self.url = url
