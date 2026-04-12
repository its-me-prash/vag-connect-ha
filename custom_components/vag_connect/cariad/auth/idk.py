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

from yarl import URL as _URL

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

        IDK migrated to Auth0 Universal Login (/u/login) in 2025.
        New flow:
          1. GET /oidc/v1/authorize → redirects to /u/login?state=AUTH0_STATE
          2. POST /usernamepassword/login with email+password (Auth0 API)
          3. Parse form_post HTML response, POST to /login/callback
          4. Follow redirects to app:// URI → extract auth code
          5. Exchange code for tokens (PKCE)
        """
        verifier, challenge = _pkce_pair()
        pkce_state = base64.urlsafe_b64encode(os.urandom(16)).rstrip(b"=").decode()
        nonce = base64.urlsafe_b64encode(os.urandom(16)).rstrip(b"=").decode()

        # Step 1 — GET authorize, follow to Auth0 /u/login page
        params: dict[str, str] = {
            "client_id": self._brand.client_id,
            "redirect_uri": self._brand.redirect_uri,
            "response_type": "code",
            "scope": self._brand.scope,
            "state": pkce_state,
            "nonce": nonce,
            "prompt": "login",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        async with self._session.get(
            _AUTHORIZE_URL, params=params, headers=self._base_headers(),
            allow_redirects=True,
        ) as resp:
            login_url = str(resp.url)
            html = await resp.text(errors="replace")
            _LOGGER.debug(
                "IDK step1: status=%s url=%s html_len=%d",
                resp.status, login_url[:80], len(html),
            )
            if resp.status != 200:
                raise AuthenticationError(
                    f"Authorization page HTTP {resp.status} at {login_url}"
                )

        # Determine which login variant we landed on
        if "/u/login" in login_url:
            # Auth0 Universal Login (new IDK, 2025+)
            return await self._authenticate_auth0(
                login_url, html, email, password, verifier
            )

        # Legacy signin-service flow (kept as fallback)
        return await self._authenticate_legacy(html, email, password, verifier)

    async def _authenticate_auth0(
        self,
        login_url: str,
        html: str,
        email: str,
        password: str,
        verifier: str,
    ) -> TokenSet:
        """Auth0 Universal Login flow (/u/login).

        IDK migrated to Auth0 in 2025. The /u/login page is a React SPA;
        credentials are submitted to /usernamepassword/login as JSON.
        Reference: audiconnect/audi_connect_ha (MIT), myskoda (MIT).
        """
        # Extract Auth0 state from URL: /u/login?state=AUTH0_STATE
        auth0_state: str = parse_qs(urlparse(login_url).query).get("state", [""])[0]
        if not auth0_state:
            raise AuthenticationError("Could not extract Auth0 state from login URL.")
        _LOGGER.debug("IDK Auth0: state=%s", auth0_state[:20])

        # Extract CSRF token — Auth0 sets a cookie named '_csrf' when the page loads.
        # We can also find it in the page HTML as a script variable.
        csrf_cookie = self._session.cookie_jar.filter_cookies(_URL("https://identity.vwgroup.io")).get("_csrf")
        csrf_token = csrf_cookie.value if csrf_cookie else self._extract_auth0_csrf(html)
        _LOGGER.debug("IDK Auth0: csrf=%s", csrf_token[:8] + "..." if csrf_token else "(none)")

        # Step 2 — POST credentials to Auth0 /usernamepassword/login
        login_payload: dict[str, Any] = {
            "client_id":     self._brand.client_id,
            "redirect_uri":  self._brand.redirect_uri,
            "tenant":        "vwgroup",
            "response_type": "code",
            "connection":    "Username-Password-Authentication",
            "username":      email,
            "password":      password,
            "state":         auth0_state,
            "_csrf":         csrf_token or "",
            "_intstate":     "deprecated",
            "scope":         self._brand.scope,
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/html, */*",
            "User-Agent": self._brand.user_agent,
            "Origin": _IDK_BASE,
            "Referer": f"{_IDK_BASE}/u/login",
        }
        async with self._session.post(
            f"{_IDK_BASE}/usernamepassword/login",
            json=login_payload,
            headers=headers,
            allow_redirects=False,
        ) as resp:
            resp_text = await resp.text(errors="replace")
            _LOGGER.debug(
                "IDK Auth0 step2: status=%s len=%d",
                resp.status, len(resp_text),
            )
            if resp.status == 401:
                raise AuthenticationError("Invalid email or password.")
            if resp.status == 429:
                raise RateLimitError()
            if resp.status not in (200, 302):
                raise AuthenticationError(
                    f"Auth0 login returned HTTP {resp.status}: {resp_text[:200]}"
                )

        # Step 3 — handle response
        if resp.status == 302:
            # Direct redirect — follow to app URI
            location = resp.headers.get("Location", "")
            _LOGGER.debug("IDK Auth0 step3: direct redirect to %s", location[:60])
        else:
            # Auth0 returns HTML form_post: parse and POST to /login/callback
            loc2 = await self._submit_auth0_callback(resp_text)
            location = loc2 or ""
            _LOGGER.debug("IDK Auth0 step3: callback location %s", location[:60] if location else "(none)")

        if not location:
            raise AuthenticationError("Auth0: no redirect location after login.")

        # Step 4 — follow redirect chain to app:// URI
        final_loc = await self._follow_to_app_redirect_get(location, self._brand.redirect_uri)
        location = final_loc or ""
        _LOGGER.debug("IDK Auth0 step4: app redirect = %s", location[:60] if location else "(none)")
        if not location:
            raise AuthenticationError("Auth0: no app:// redirect after callback.")

        auth_code = _extract_auth_code(location, self._brand.redirect_uri)
        if not auth_code:
            raise AuthenticationError(f"Auth0: no code in redirect: {location}")

        _LOGGER.debug("IDK Auth0: got code, exchanging for tokens")
        return await self._exchange_code(auth_code, verifier)

    async def _authenticate_legacy(
        self,
        html: str,
        email: str,
        password: str,
        verifier: str,
    ) -> TokenSet:
        """Legacy signin-service flow (pre-2025 IDK)."""
        csrf = self._parse_csrf_robust(html)
        if not csrf.fields.get("_csrf") and not csrf.fields.get("hmac"):
            raise AuthenticationError(
                "Could not parse IDK login page CSRF (legacy flow)."
            )

        email_url = _absolute_url(
            _IDK_BASE,
            csrf.form_action or f"{_SIGNIN_BASE}/{self._brand.client_id}/login/identifier",
        )
        async with self._session.post(
            email_url, data={**csrf.fields, "email": email},
            headers=self._form_headers(), allow_redirects=True,
        ) as resp:
            if resp.status != 200:
                raise AuthenticationError(f"Email submission HTTP {resp.status}")
            html2 = await resp.text()

        csrf2 = self._parse_csrf_robust(html2)
        if "hmac" not in csrf2.fields:
            m = re.search(r'"hmac"\s*:\s*"([0-9a-fA-F]+)"', html2)
            if m:
                csrf2.fields["hmac"] = m.group(1)

        pw_url = _absolute_url(
            _IDK_BASE,
            f"{_SIGNIN_BASE}/{self._brand.client_id}/login/authenticate",
        )
        location = await self._follow_to_app_redirect(
            pw_url, {**csrf2.fields, "email": email, "password": password},
            self._brand.redirect_uri,
        )
        if not location:
            raise AuthenticationError("Legacy: no redirect after password.")

        auth_code = _extract_auth_code(location, self._brand.redirect_uri)
        if not auth_code:
            raise AuthenticationError(f"Legacy: no code in redirect: {location}")

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

    # ── Auth0 Universal Login helpers ─────────────────────────────────────────

    @staticmethod
    def _extract_auth0_csrf(html: str) -> str:
        """Extract Auth0 CSRF token from page HTML (fallback if cookie missing)."""
        patterns = [
            r'"csrf"\s*:\s*"([^"]{8,})"',
            r"_csrf[\"']\s*:\s*[\"']([^\"']{8,})[\"']",
            r'name=["\']_csrf["\'][^>]+value=["\']([^"\']+)["\']',
            r'value=["\']([^"\']+)["\'][^>]+name=["\']_csrf["\']',
        ]
        for p in patterns:
            m = re.search(p, html)
            if m:
                return m.group(1)
        return ""

    async def _submit_auth0_callback(self, html: str) -> str | None:
        """Parse Auth0 form_post response and POST to /login/callback.

        After /usernamepassword/login, Auth0 returns an HTML page with:
          <form method="post" action="https://identity.vwgroup.io/login/callback">
            <input name="wctx" value="...">
            <input name="wresult" value="...">
          </form>
        We must POST these fields to continue the flow.
        """
        parser = _CSRFParser()
        parser.feed(html)

        # Also try regex for the hidden fields
        for tag in re.finditer(r"<input[^>]+>", html, re.IGNORECASE):
            t = tag.group(0)
            if 'type="hidden"' not in t.lower() and "type='hidden'" not in t.lower():
                continue
            nm = re.search(r'name=["\']([^"\']+)["\']', t)
            vm = re.search(r'value=["\']([^"\']*)["\']', t)
            if nm:
                parser.fields[nm.group(1)] = vm.group(1) if vm else ""

        if not parser.form_action and not parser.fields:
            # Might be a direct JSON response with location
            m = re.search(r'"location"\s*:\s*"([^"]+)"', html)
            if m:
                return m.group(1)
            _LOGGER.warning("Auth0 callback: no form fields in response (len=%d)", len(html))
            return None

        callback_url = parser.form_action or f"{_IDK_BASE}/login/callback"
        if not callback_url.startswith("http"):
            callback_url = _IDK_BASE + callback_url

        _LOGGER.debug("IDK Auth0: posting callback to %s fields=%s",
                      callback_url[:60], list(parser.fields.keys()))

        async with self._session.post(
            callback_url,
            data=parser.fields,
            headers=self._form_headers(),
            allow_redirects=False,
        ) as resp:
            location = resp.headers.get("Location", "")
            _LOGGER.debug("IDK Auth0: callback status=%s location=%s",
                          resp.status, location[:60])
            return location if location else None

    async def _follow_to_app_redirect_get(
        self, start_url: str, app_prefix_full: str
    ) -> str | None:
        """Follow GET redirects from a URL until we reach the app:// URI."""
        prefix = app_prefix_full.split("://")[0] + "://"
        location = start_url

        for _ in range(15):
            if location.startswith(prefix):
                return location
            if not location.startswith("http"):
                # Relative or app:// — return as-is
                return location if location.startswith(prefix) else None

            async with self._session.get(
                location,
                headers=self._base_headers(),
                allow_redirects=False,
            ) as resp:
                new_loc = resp.headers.get("Location", "")
                if resp.status in (301, 302, 303, 307, 308) and new_loc:
                    location = new_loc
                elif location.startswith(prefix):
                    return location
                else:
                    # Read body in case it's another form_post
                    body = await resp.text(errors="replace")
                    if "<form" in body.lower():
                        next_loc = await self._submit_auth0_callback(body)
                        if next_loc:
                            location = next_loc
                            continue
                    break

        return location if location.startswith(prefix) else None

    # ── Legacy signin-service helpers ─────────────────────────────────────────



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
