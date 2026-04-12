# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Config flow for VAG Connect — setup, reconfigure, and re-authentication."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback

from .const import (
    BRANDS,
    CONF_BRAND,
    CONF_FORCE_ACCESS,
    CONF_SCAN_INTERVAL,
    CONF_SPIN,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def _validate_credentials(
    hass: HomeAssistant, brand: str, username: str, password: str,
    mfa_code: str | None = None,
) -> None:
    """Validate credentials by authenticating with the CARIAD API.

    Creates a dedicated aiohttp session with a fresh CookieJar for auth —
    the IDK login flow is stateful (cookies between steps) and must not
    share the HA-wide session which may have cookies from other integrations.
    """
    import aiohttp  # noqa: PLC0415
    from .cariad import CariadClientFactory  # noqa: PLC0415
    from .cariad.exceptions import (  # noqa: PLC0415
        AuthenticationError,
        TermsAndConditionsError,
        MarketingConsentError,
        TwoFactorRequiredError,
        RateLimitError,
    )

    # Dedicated session with fresh CookieJar — required for IDK multi-step auth
    connector = aiohttp.TCPConnector(ssl=True)
    async with aiohttp.ClientSession(
        connector=connector,
        cookie_jar=aiohttp.CookieJar(unsafe=True),
    ) as auth_session:
        client = CariadClientFactory.create(brand, auth_session, username, password)
        try:
            await client.authenticate(mfa_code=mfa_code)
        except TermsAndConditionsError as err:
            raise ValueError("terms_and_conditions") from err
        except MarketingConsentError as err:
            raise ValueError("marketing_consent") from err
        except TwoFactorRequiredError as err:
            raise ValueError(f"two_factor_required:{err}") from err
        except RateLimitError as err:
            raise ValueError("too_many_requests") from err
        except AuthenticationError as err:
            _LOGGER.warning("VAG Connect auth failed (%s): %s", brand, err)
            raise ValueError("invalid_credentials") from err
        except Exception as err:  # noqa: BLE001
            import traceback  # noqa: PLC0415
            _LOGGER.error(
                "VAG Connect unexpected error during %s auth: %s — %s\nTraceback:\n%s",
                brand, type(err).__name__, err,
                "".join(traceback.format_tb(err.__traceback__)),
            )
            raise ValueError("cannot_connect") from err


def _user_schema(
    brand: str = "",
    username: str = "",
    scan_interval: int = DEFAULT_SCAN_INTERVAL,
    spin: str = "",
    force_access: bool = False,
) -> vol.Schema:
    """Build the user-step schema, pre-filled with current values for reconfigure."""
    return vol.Schema(
        {
            vol.Required(CONF_BRAND, default=brand or vol.UNDEFINED): vol.In(BRANDS),
            vol.Required(CONF_USERNAME, default=username or vol.UNDEFINED): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(CONF_SPIN, default=spin): str,
            vol.Optional(CONF_SCAN_INTERVAL, default=scan_interval): vol.All(
                vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)
            ),
            vol.Optional(CONF_FORCE_ACCESS, default=force_access): bool,
        }
    )


def _map_error(err_code: str) -> str:
    """Map ValueError string to strings.json error key."""
    return err_code if err_code in {
        "terms_and_conditions", "marketing_consent", "two_factor_required",
        "too_many_requests", "invalid_credentials", "missing_library",
    } else "cannot_connect"


class VagConnectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VAG Connect."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise — stores pending credentials for MFA step."""
        self._pending_brand: str = ""
        self._pending_username: str = ""
        self._pending_password: str = ""
        self._pending_entry_data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step 1: choose brand + enter credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            brand    = user_input[CONF_BRAND]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            await self.async_set_unique_id(f"{brand}_{username}")
            self._abort_if_unique_id_configured()

            try:
                await _validate_credentials(self.hass, brand, username, password)
            except ValueError as err:
                err_str = str(err)
                if err_str.startswith("two_factor_required"):
                    # Store credentials for MFA step
                    self._pending_brand    = brand
                    self._pending_username = username
                    self._pending_password = password
                    self._pending_entry_data = {
                        CONF_BRAND:         brand,
                        CONF_USERNAME:      username,
                        CONF_PASSWORD:      password,
                        CONF_SPIN:          user_input.get(CONF_SPIN, ""),
                        CONF_SCAN_INTERVAL: max(
                            user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                            MIN_SCAN_INTERVAL,
                        ),
                        CONF_FORCE_ACCESS:  user_input.get(CONF_FORCE_ACCESS, False),
                    }
                    return await self.async_step_mfa()
                errors["base"] = _map_error(err_str)
            else:
                return self.async_create_entry(
                    title=f"{BRANDS[brand]} — {username}",
                    data={
                        CONF_BRAND:         brand,
                        CONF_USERNAME:      username,
                        CONF_PASSWORD:      password,
                        CONF_SPIN:          user_input.get(CONF_SPIN, ""),
                        CONF_SCAN_INTERVAL: max(
                            user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                            MIN_SCAN_INTERVAL,
                        ),
                        CONF_FORCE_ACCESS:  user_input.get(CONF_FORCE_ACCESS, False),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(),
            errors=errors,
        )

    async def async_step_mfa(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Step 2 (optional): enter MFA code sent by email / authenticator app."""
        errors: dict[str, str] = {}

        if user_input is not None:
            mfa_code = user_input.get("mfa_code", "").strip()
            try:
                await _validate_credentials(
                    self.hass,
                    self._pending_brand,
                    self._pending_username,
                    self._pending_password,
                    mfa_code=mfa_code,
                )
            except ValueError as err:
                errors["base"] = _map_error(str(err))
            else:
                return self.async_create_entry(
                    title=f"{BRANDS[self._pending_brand]} — {self._pending_username}",
                    data=self._pending_entry_data,
                )

        return self.async_show_form(
            step_id="mfa",
            data_schema=vol.Schema({
                vol.Required("mfa_code"): str,
            }),
            errors=errors,
        )

    # Triggered automatically when coordinator raises ConfigEntryAuthFailed

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Initiate re-auth when credentials expire or are rejected."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Re-enter credentials to regain access."""
        errors: dict[str, str] = {}
        reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )

        if user_input is not None and reauth_entry is not None:
            brand    = reauth_entry.data[CONF_BRAND]
            username = reauth_entry.data[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            spin     = user_input.get(CONF_SPIN, reauth_entry.data.get(CONF_SPIN, ""))

            try:
                await _validate_credentials(self.hass, brand, username, password)
            except ValueError as err:
                errors["base"] = _map_error(str(err))
            else:
                self.hass.config_entries.async_update_entry(
                    reauth_entry,
                    data={**reauth_entry.data, CONF_PASSWORD: password, CONF_SPIN: spin},
                )
                await self.hass.config_entries.async_reload(reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(
                        CONF_SPIN,
                        default=reauth_entry.data.get(CONF_SPIN, "") if reauth_entry else "",
                    ): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "brand": BRANDS.get(
                    reauth_entry.data.get(CONF_BRAND, ""), ""
                ) if reauth_entry else "",
                "username": reauth_entry.data.get(CONF_USERNAME, "") if reauth_entry else "",
            },
        )

    # Allows changing ALL settings without removing and re-adding the integration

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Reconfigure credentials and settings for an existing entry."""
        errors: dict[str, str] = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if user_input is not None and entry is not None:
            brand    = user_input[CONF_BRAND]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            try:
                await _validate_credentials(self.hass, brand, username, password)
            except ValueError as err:
                errors["base"] = _map_error(str(err))
            else:
                new_unique_id = f"{brand}_{username}"
                await self.async_set_unique_id(new_unique_id)
                self._abort_if_unique_id_configured(updates={"entry_id": entry.entry_id})

                self.hass.config_entries.async_update_entry(
                    entry,
                    title=f"{BRANDS[brand]} — {username}",
                    unique_id=new_unique_id,
                    data={
                        CONF_BRAND:         brand,
                        CONF_USERNAME:      username,
                        CONF_PASSWORD:      password,
                        CONF_SPIN:          user_input.get(CONF_SPIN, ""),
                        CONF_SCAN_INTERVAL: max(
                            user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                            MIN_SCAN_INTERVAL,
                        ),
                        CONF_FORCE_ACCESS:  user_input.get(CONF_FORCE_ACCESS, False),
                    },
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")

        current = entry.data if entry else {}
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_user_schema(
                brand=current.get(CONF_BRAND, ""),
                username=current.get(CONF_USERNAME, ""),
                scan_interval=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                spin=current.get(CONF_SPIN, ""),
                force_access=current.get(CONF_FORCE_ACCESS, False),
            ),
            errors=errors,
        )


    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> VagConnectOptionsFlow:
        """Return options flow handler."""
        return VagConnectOptionsFlow(config_entry)


class VagConnectOptionsFlow(config_entries.OptionsFlow):
    """Handle options changes (scan interval + S-PIN) without full reconfigure."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialise options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Options: scan interval + S-PIN."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.data
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)),
                    vol.Optional(
                        CONF_SPIN, default=current.get(CONF_SPIN, "")
                    ): str,
                }
            ),
        )
