"""Config flow for VAG Connect integration."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    BRANDS,
    CONF_BRAND,
    CONF_SCAN_INTERVAL,
    CONF_SPIN,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def _validate_credentials(
    hass: HomeAssistant, brand: str, username: str, password: str
) -> dict:
    """Try to connect with the given credentials. Returns {} on success, raises on error."""
    try:
        from carconnectivity import CarConnectivity

        def _test():
            cc = CarConnectivity(
                connectors=[
                    {
                        "type": brand,
                        "config": {
                            "username": username,
                            "password": password,
                            "no_cache": True,
                        },
                    }
                ]
            )
            # Just instantiate — full connect happens in coordinator
            return cc

        await hass.async_add_executor_job(_test)
        return {}
    except ImportError:
        raise ValueError("missing_library")
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("Credential validation error: %s", err)
        raise ValueError("cannot_connect") from err


class VagConnectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VAG Connect."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1: choose brand + enter credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            brand = user_input[CONF_BRAND]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            spin = user_input.get(CONF_SPIN, "")
            scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

            # Unique ID = brand + username to allow multiple accounts
            await self.async_set_unique_id(f"{brand}_{username}")
            self._abort_if_unique_id_configured()

            try:
                await _validate_credentials(
                    self.hass, brand, username, password
                )
            except ValueError as err:
                err_code = str(err)
                if err_code == "terms_and_conditions":
                    errors["base"] = "terms_and_conditions"
                elif err_code == "marketing_consent":
                    errors["base"] = "marketing_consent"
                elif err_code == "two_factor_required":
                    errors["base"] = "two_factor_required"
                elif err_code == "too_many_requests":
                    errors["base"] = "too_many_requests"
                elif err_code in ("invalid_credentials", "missing_library", "cannot_connect"):
                    errors["base"] = err_code
                else:
                    errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"{BRANDS[brand]} — {username}",
                    data={
                        CONF_BRAND: brand,
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        CONF_SPIN: spin,
                        CONF_SCAN_INTERVAL: max(scan_interval, MIN_SCAN_INTERVAL),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BRAND): vol.In(BRANDS),
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_SPIN, default=""): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)),
                    vol.Optional("force_enable_access", default=False): bool,
                }
            ),
            description_placeholders={
                "separate_account_hint": (
                    "💡 Tipp: Empfehlenswert ist ein separater App-Account "
                    "für Home Assistant (Fahrzeug teilen via Hersteller-App). "
                    "Das schützt vor API-Sperren wenn beide Geräte gleichzeitig zugreifen."
                )
            },
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "VagConnectOptionsFlow":  # noqa: F821
        """Return options flow."""
        return VagConnectOptionsFlow(config_entry)


class VagConnectOptionsFlow(config_entries.OptionsFlow):
    """Handle options (reconfigure after setup)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
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
                        CONF_SPIN,
                        default=current.get(CONF_SPIN, ""),
                    ): str,
                }
            ),
        )
