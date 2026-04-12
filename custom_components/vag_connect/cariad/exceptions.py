# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Exceptions for the VAG Connect CARIAD API client."""

from __future__ import annotations


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
