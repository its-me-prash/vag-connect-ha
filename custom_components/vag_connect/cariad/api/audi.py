# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Audi EU API client — CARIAD BFF with legacy IDK signin-service auth.

The audiconnect client_id (09b6cbec-...) uses the old IDK signin-service
flow instead of Auth0. After successful PKCE login, the IDK access_token
is used directly with the CARIAD BFF — same as VW EU.

The AZS/MBB exchange used by the old audiconnect integration is for the
legacy fs-car API, which we do not use. CARIAD BFF requires the IDK
access_token directly (jtt: access).
"""

from __future__ import annotations

import logging

from aiohttp import ClientSession

from ..auth.idk import IDKAuth
from ..models import BRAND_AUDI
from .vw_eu import VWEUClient

_LOGGER = logging.getLogger(__name__)


class AudiClient(VWEUClient):
    """Audi EU client — same CARIAD BFF endpoints as VW EU.

    Auth uses the legacy IDK signin-service flow (client 09b6cbec-...)
    which returns a standard PKCE access_token usable with CARIAD BFF.
    No AZS/MBB exchange needed — those are for the old fs-car API.
    """

    def __init__(
        self, session: ClientSession, email: str, password: str, spin: str = ""
    ) -> None:
        super().__init__(session, email, password, spin)
        self._brand = BRAND_AUDI
        self._auth = IDKAuth(session, BRAND_AUDI)

    async def authenticate(self, mfa_code: str | None = None) -> None:
        """IDK PKCE login → CARIAD BFF access_token. No AZS/MBB needed."""
        self._tokens = await self._auth.authenticate(
            self._email, self._password, mfa_code=mfa_code
        )
        _LOGGER.debug(
            "Audi IDK auth complete — using access_token directly with CARIAD BFF"
        )
