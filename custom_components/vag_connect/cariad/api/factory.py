# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Factory for creating the correct brand API client."""

from __future__ import annotations

from aiohttp import ClientSession

from .base import CariadBaseClient
from .vw_eu import VWEUClient
from .audi import AudiClient
from .skoda import SkodaClient
from .seat_cupra import SeatCupraClient
from .porsche import PorscheClient
from .vw_na import VWNAClient


class CariadClientFactory:
    """Instantiate the correct API client for a given brand."""

    @staticmethod
    def create(
        brand: str,
        session: ClientSession,
        email: str,
        password: str,
        spin: str = "",
        country: str = "us",
    ) -> CariadBaseClient | PorscheClient | VWNAClient:
        """Return an authenticated-ready client for the given brand.

        Supported brands:
          volkswagen    — VW EU (WeConnect ID, EMEA BFF)
          audi          — Audi EU (myAudi, EMEA BFF)
          skoda         — Škoda (MyŠkoda, mysmob.api.connect.skoda-auto.cz)
          seat          — SEAT (OLA server)
          cupra         — CUPRA (OLA server)
          volkswagen_na — VW North America (US/CA, b-h-s.spr.{cc}00.p.con-veh.net)
          porsche       — Porsche Connect (Auth0, api.ppa.porsche.com)
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
        if lower == "volkswagen_na":
            return VWNAClient(session, email, password, spin, country=country)
        if lower == "porsche":
            return PorscheClient(session, email, password, spin)
        raise ValueError(
            f"Unknown brand '{brand}'. Supported: "
            "volkswagen, audi, skoda, seat, cupra, volkswagen_na, porsche"
        )
