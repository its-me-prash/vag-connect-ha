# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Factory for creating the correct brand API client."""

from __future__ import annotations

from aiohttp import ClientSession

from .base import CariadBaseClient
from .vw_eu import VWEUClient
from .audi import AudiClient
from .skoda import SkodaClient
from .seat_cupra import SeatCupraClient


class CariadClientFactory:
    """Instantiate the correct API client for a given brand."""

    @staticmethod
    def create(
        brand: str,
        session: ClientSession,
        email: str,
        password: str,
        spin: str = "",
    ) -> CariadBaseClient:
        """Return an authenticated-ready client for the given brand.

        Supported brands: volkswagen, audi, skoda, seat, cupra
        """
        lower = brand.lower()
        if lower == "volkswagen":
            return VWEUClient(session, email, password, spin)
        if lower == "audi":
            return AudiClient(session, email, password, spin)
        if lower == "skoda":
            return SkodaClient(session, email, password, spin)
        if lower in ("seat", "cupra"):
            return SeatCupraClient(session, lower, email, password, spin)
        raise ValueError(
            f"Unknown brand '{brand}'. Supported: volkswagen, audi, skoda, seat, cupra"
        )
