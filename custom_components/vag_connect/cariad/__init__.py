# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""VAG Connect CARIAD API client — direct async access, no CarConnectivity."""

from .api.factory import CariadClientFactory
from .exceptions import (
    AuthenticationError,
    MarketingConsentError,
    RateLimitError,
    SpinError,
    TermsAndConditionsError,
    VehicleCommandError,
    VehicleNotFoundError,
)
from .models import BRANDS, BrandConfig, VehicleData

__all__ = [
    "CariadClientFactory",
    "BrandConfig",
    "VehicleData",
    "AuthenticationError",
    "MarketingConsentError",
    "RateLimitError",
    "SpinError",
    "TermsAndConditionsError",
    "VehicleCommandError",
    "VehicleNotFoundError",
    "BRANDS",
]
