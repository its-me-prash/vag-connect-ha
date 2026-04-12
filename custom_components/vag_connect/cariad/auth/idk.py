# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""VAG IDK authentication — PKCE/OAuth2 for VW EU, Audi, Škoda, SEAT, CUPRA.

Clean-room implementation of the standard PKCE flow documented in:
  IETF RFC 7636 — Proof Key for Code Exchange
  https://identity.vwgroup.io/.well-known/openid-configuration

No code copied from any GPL project. Auth flow discovered through
publicly available open-source research (see docs/research/VAG_GROUP_ECOSYSTEM.md).
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import parse_qs, urlparse, urlunparse

from aiohttp import ClientSession

from ..exceptions import (
    AuthenticationError,
    MarketingConsentError,
    TermsAndConditionsError,
    TwoFactorRequiredError,
    RateLimitError,
    TokenExpiredError,
)
from ..models import BrandConfig, TokenSet

_LOGGER = logging.getLogger(__name__)

_IDK_BASE = "https://identity.vwgroup.io"
_SIGNIN_BASE = f"{_IDK_BASE}/signin-service/v1"
_AUTHORIZE_URL = f"{_IDK_BASE}/oidc/v1/authorize"


class _CSRFParser(HTMLParser):
    """Minimal HTML parser — extracts hidden form fields from IDK login pages."""

    def __init__(self) -> None:
        super().__init__()
        self.fields: dict[str, str] = {}
        self.form_action: str = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "input" and attr.get("type") == "hidden":
            name = attr.get("name", "")
            value = attr.get("value", "")
            if name:
                self.fields[name] = value or ""
        if tag == "form" and not self.form_action:
            self.form_action = attr.get("action") or ""


def _pkce_pair() -> tuple[str, str]:
    """Generate a PKCE code_verifier + code_challenge (S256)."""
    verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def _extract_auth_code(location: str, redirect_uri: str) -> str | None:
    """Extract 'code' query param from a redirect-to-app URL."""
    prefix = redirect_uri.split("://")[0] + "://"
    if not location.startswith(prefix):
        return None
    parsed = urlparse(location)
    params = parse_qs(parsed.query or parsed.path.lstrip("?"))
    codes = params.get("code")
    return codes[0] if codes else None


def _absolute_url(base: str, path: str) -> str:
    """Resolve a relative form action against the IDK base URL."""
    if path.startswith("http"):
        return path
    parsed = urlparse(base)
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


class IDKAuth:
    """Handles authentication against the VAG Identity Kit (IDK) server.

    Covers: VW EU, Audi, Škoda, SEAT, CUPRA.
    Uses the caller's injected aiohttp.ClientSession — no requests dependency.
    """

    def __init__(self, session: ClientSession, brand: BrandConfig) -> None:
        self._session = session
        self._brand = brand

    async def authenticate(self, email: str, password: str) -> TokenSet:
        """Full login flow → returns access/refresh/id tokens.

        Steps:
          1. GET authorize → parse CSRF fields
          2. POST email identifier
          3. POST password → follow redirects → get auth code
          4. POST token exchange with PKCE verifier
        """
        verifier, challenge = _pkce_pair()
        state = base64.urlsafe_b64encode(os.urandom(16)).rstrip(b"=").decode()
        nonce = base64.urlsafe_b64encode(os.urandom(16)).rstrip(b"=").decode()

        # Step 1 — authorization page
        params: dict[str, str] = {
            "client_id": self._brand.client_id,
            "redirect_uri": self._brand.redirect_uri,
            "response_type": "code",
            "scope": self._brand.scope,
            "state": state,
            "nonce": nonce,
            "prompt": "login",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        headers = self._base_headers()
        async with self._session.get(
            _AUTHORIZE_URL, params=params, headers=headers, allow_redirects=True
        ) as resp:
            final_url = str(resp.url)
            ctype = resp.headers.get("Content-Type", "")
            html = await resp.text(errors="replace")
            _LOGGER.debug(
                "IDK step1: status=%s url=%s ctype=%s html_len=%d",
                resp.status, final_url[:80], ctype[:40], len(html),
            )
            if resp.status != 200:
                raise AuthenticationError(
                    f"Authorization page returned HTTP {resp.status} at {final_url}"
                )

        if not html.strip():
            _LOGGER.error(
                "IDK step1: empty response — url=%s possible bot-detection or app-scheme redirect",
                final_url,
            )
            raise AuthenticationError(
                "IDK returned empty page. Possible bot detection — retry in a few minutes."
            )

        csrf = self._parse_csrf_robust(html)
        _LOGGER.debug(
            "IDK step1: fields=%s action=%s",
            list(csrf.fields.keys()),
            (csrf.form_action[:60] if csrf.form_action else "(none)"),
        )
        if not csrf.fields.get("_csrf") and not csrf.fields.get("hmac"):
            _LOGGER.error(
                "IDK step1: no CSRF fields — url=%s snippet=%r",
                final_url, html[:800],
            )
            raise AuthenticationError(
                "Could not parse IDK login page — IDK may have changed its HTML structure."
            )

        # Step 2 — submit email
        email_url = _absolute_url(
            _IDK_BASE,
            csrf.form_action or f"{_SIGNIN_BASE}/{self._brand.client_id}/login/identifier",
        )
        email_data = {**csrf.fields, "email": email}
        async with self._session.post(
            email_url, data=email_data, headers=self._form_headers(), allow_redirects=True
        ) as resp:
            if resp.status != 200:
                raise AuthenticationError(f"Email submission returned HTTP {resp.status}")
            html = await resp.text()

        # Extract updated CSRF for password step
        csrf2 = self._parse_csrf_robust(html)
        # IDK uses a JavaScript-injected hmac — extract via regex if form parser missed it
        if "hmac" not in csrf2.fields:
            m = re.search(r'"hmac"\s*:\s*"([0-9a-fA-F]+)"', html)
            if m:
                csrf2.fields["hmac"] = m.group(1)

        # Step 3 — submit password
        pw_url = _absolute_url(
            _IDK_BASE,
            f"{_SIGNIN_BASE}/{self._brand.client_id}/login/authenticate",
        )
        pw_data = {**csrf2.fields, "email": email, "password": password}
        _LOGGER.debug("IDK step3: posting password to %s", pw_url)
        location = await self._follow_to_app_redirect(
            pw_url, pw_data, self._brand.redirect_uri
        )
        _LOGGER.debug("IDK step3: redirect location = %s", location[:80] if location else "(none)")
        if not location:
            raise AuthenticationError("Password submission did not redirect to app — check credentials.")

        auth_code = _extract_auth_code(location, self._brand.redirect_uri)
        if not auth_code:
            _LOGGER.error("IDK: no auth code in location: %s", location)
            raise AuthenticationError(f"Could not extract authorization code from: {location}")
        _LOGGER.debug("IDK step4: got auth code, exchanging for tokens")

        # Step 4 — exchange code for tokens
        return await self._exchange_code(auth_code, verifier)

    async def refresh(self, refresh_token: str) -> TokenSet:
        """Exchange a refresh token for a fresh token set."""
        token_url = await self._get_token_endpoint()
        data = {
            "client_id": self._brand.client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        async with self._session.post(
            token_url, data=data, headers=self._form_headers()
        ) as resp:
            if resp.status == 400:
                raise TokenExpiredError("Refresh token rejected — full re-login required.")
            if resp.status != 200:
                raise AuthenticationError(f"Token refresh returned HTTP {resp.status}")
            payload: dict[str, Any] = await resp.json()

        return self._parse_tokens(payload)

    # ── private helpers ────────────────────────────────────────────────────────

    async def _follow_to_app_redirect(
        self, url: str, data: dict[str, str], app_prefix_full: str
    ) -> str | None:
        """POST data, then follow HTTP 302 redirects until we hit the app URI."""
        prefix = app_prefix_full.split("://")[0] + "://"
        async with self._session.post(
            url, data=data, headers=self._form_headers(), allow_redirects=False
        ) as resp:
            if resp.status == 200:
                body = await resp.text()
                if "terms-and-conditions" in body.lower():
                    raise TermsAndConditionsError()
                if "marketing" in body.lower() and "consent" in body.lower():
                    raise MarketingConsentError()
                if "two-factor" in body.lower() or "2fa" in body.lower():
                    raise TwoFactorRequiredError()
                raise AuthenticationError("Unexpected non-redirect after password submission.")
            if resp.status == 429:
                raise RateLimitError()
            location = resp.headers.get("Location", "")

        # Follow redirect chain until app:// or max 10 hops
        for _ in range(10):
            if location.startswith(prefix):
                return location
            if "terms-and-conditions" in location:
                raise TermsAndConditionsError()
            if "consent/marketing" in location:
                raise MarketingConsentError()
            async with self._session.get(
                location, headers=self._base_headers(), allow_redirects=False
            ) as resp:
                if resp.status in (301, 302, 303, 307, 308):
                    location = resp.headers.get("Location", "")
                elif location.startswith(prefix):
                    return location
                else:
                    break

        return location if location.startswith(prefix) else None

    async def _exchange_code(self, code: str, verifier: str) -> TokenSet:
        """POST authorization code + PKCE verifier → tokens."""
        token_url = await self._get_token_endpoint()
        data = {
            "client_id": self._brand.client_id,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._brand.redirect_uri,
            "code_verifier": verifier,
        }
        async with self._session.post(
            token_url, data=data, headers=self._form_headers()
        ) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise AuthenticationError(
                    f"Token exchange failed HTTP {resp.status}: {body[:200]}"
                )
            payload: dict[str, Any] = await resp.json()

        return self._parse_tokens(payload)

    async def _get_token_endpoint(self) -> str:
        """Fetch token endpoint from IDK OpenID configuration."""
        url = f"{_IDK_BASE}/.well-known/openid-configuration"
        try:
            async with self._session.get(url) as resp:
                cfg: dict[str, Any] = await resp.json()
                return str(cfg.get("token_endpoint", f"{_IDK_BASE}/oidc/v1/token"))
        except Exception:  # noqa: BLE001
            return f"{_IDK_BASE}/oidc/v1/token"

    def _parse_tokens(self, payload: dict[str, Any]) -> TokenSet:
        """Parse token response into a TokenSet."""
        try:
            return TokenSet(
                access_token=payload["access_token"],
                refresh_token=payload["refresh_token"],
                id_token=payload.get("id_token", ""),
            )
        except KeyError as err:
            raise AuthenticationError(
                f"Token response missing field {err}: {list(payload)}"
            ) from err

    @staticmethod
    def _parse_csrf(html: str) -> _CSRFParser:
        parser = _CSRFParser()
        parser.feed(html)
        return parser

    @staticmethod
    def _parse_csrf_robust(html: str) -> _CSRFParser:
        """Parse CSRF from IDK login page — handles multiple page structures.

        IDK has changed their login page over the years:
        - Classic (2022): <input type="hidden" name="_csrf" value="...">
        - Modern (2024+): CSRF embedded in <script> JSON block
        - Also tries regex fallback for all hidden inputs.
        """
        parser = _CSRFParser()
        parser.feed(html)

        # Fallback 1 — regex over ALL hidden inputs (HTMLParser can miss JS-rendered)
        for tag in re.finditer(r"<input[^>]+>", html, re.IGNORECASE):
            t = tag.group(0)
            if 'type="hidden"' not in t.lower() and "type='hidden'" not in t.lower():
                continue
            nm = re.search(r'name=["\']([^"\']+)["\']', t)
            vm = re.search(r'value=["\']([^"\']*)["\']', t)
            if nm:
                parser.fields[nm.group(1)] = vm.group(1) if vm else ""

        # Fallback 2 — form action via regex
        if not parser.form_action:
            fm = re.search(r'action=["\']([^"\']+/login/[^"\']+)["\']', html)
            if fm:
                parser.form_action = fm.group(1)

        # Fallback 3 — CSRF in JSON/script blocks (modern IDK SPA pages)
        # e.g.: {"_csrf":"token","hmac":"hexval",...}
        # or:   window.__STORE__ = {...,"csrf":"token",...}
        if not parser.fields.get("_csrf"):
            for pattern in [
                r'"_csrf"\s*:\s*"([^"]{8,})"',
                r'"csrf"\s*:\s*"([^"]{8,})"',
                r'"csrfToken"\s*:\s*"([^"]{8,})"',
            ]:
                m = re.search(pattern, html)
                if m:
                    parser.fields["_csrf"] = m.group(1)
                    _LOGGER.debug("IDK: _csrf extracted via JSON pattern")
                    break

        if not parser.fields.get("hmac"):
            m = re.search(r'"hmac"\s*:\s*"([0-9a-fA-F]{20,})"', html)
            if m:
                parser.fields["hmac"] = m.group(1)
                _LOGGER.debug("IDK: hmac extracted via JSON pattern")

        return parser

    def _base_headers(self) -> dict[str, str]:
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-de",
            "User-Agent": self._brand.user_agent,
        }

    def _form_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json,text/html,*/*",
            "User-Agent": self._brand.user_agent,
        }
