# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Coordinator for VAG Connect — async polling via own CARIAD API client.

Data flow:
  CARIAD client polls VAG API → poll_loop pushes to HA via async_set_updated_data
  → asyncio.run_coroutine_threadsafe → async_set_updated_data → entities update.

Thread safety:
  _vehicles_lock (threading.Lock) guards self.vehicles.
  CARIAD client (async) writes vehicles dict; HA entities read via coordinator data.
"""

import logging
import threading
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_BRAND,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_SPIN,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Minimum interval enforced by Audi/VW connector (Sekunden)
_CC_MIN_INTERVAL_S = 180


class VagConnectCoordinator(DataUpdateCoordinator):
    """Coordinates vehicle data via own CARIAD API client (direct async polling).

    update_interval=None — polling is handled by _poll_loop(), not HA scheduler.
    Updates flow: CARIAD client → _poll_loop → async_set_updated_data → Entities.
    """

    def __init__(self, hass: HomeAssistant, entry: Any) -> None:
        """Initialise coordinator."""
        self.entry = entry
        self._started = False
        self._was_available: bool = True  # tracks availability for log_when_unavailable
        self._cariad_client: Any = None

        # Thread-safe dict for vehicle data
        self.vehicles: dict[str, Any] = {}
        self._vehicles_lock = threading.Lock()

        # update_interval=None: no HA-level polling
        # Updates arrive reactively via _on_cc_update → async_set_updated_data
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=None,
        )


    async def async_setup(self) -> bool:
        """Authenticate and fetch initial vehicle data via own CARIAD client."""
        from homeassistant.helpers.aiohttp_client import async_get_clientsession  # noqa: PLC0415
        from .cariad import CariadClientFactory  # noqa: PLC0415
        from .cariad.exceptions import (  # noqa: PLC0415
            AuthenticationError,
            TermsAndConditionsError,
            MarketingConsentError,
            TwoFactorRequiredError,
            RateLimitError,
        )

        brand    = self.entry.data[CONF_BRAND]
        username = self.entry.data[CONF_USERNAME]
        password = self.entry.data[CONF_PASSWORD]
        spin     = self.entry.data.get(CONF_SPIN) or ""

        session = async_get_clientsession(self.hass)
        self._cariad_client = CariadClientFactory.create(brand, session, username, password, spin)

        try:
            await self._cariad_client.authenticate()
            vins = await self._cariad_client.get_vehicles()
            if not vins:
                return False

            # Fetch status for all vehicles
            import asyncio as _asyncio  # noqa: PLC0415
            results = await _asyncio.gather(
                *[self._cariad_client.get_status(vin) for vin in vins],
                return_exceptions=True,
            )

            with self._vehicles_lock:
                for vin, result in zip(vins, results):
                    if isinstance(result, Exception):
                        _LOGGER.warning("Could not fetch status for %s: %s", vin, result)
                        continue
                    from .cariad.models import VehicleData  # noqa: PLC0415
                    if isinstance(result, VehicleData):
                        data = result.to_dict()
                        data["_client"] = self._cariad_client
                        self.vehicles[vin] = data

            self._started = True
            found = len(self.vehicles)
            _LOGGER.info("VAG Connect: setup complete — %d vehicle(s)", found)

            # Start background polling
            self.hass.loop.call_soon_threadsafe(
                lambda: _asyncio.ensure_future(self._poll_loop(), loop=self.hass.loop)
            )
            return found > 0

        except TermsAndConditionsError as err:
            raise ValueError("terms_and_conditions") from err
        except MarketingConsentError as err:
            raise ValueError("marketing_consent") from err
        except TwoFactorRequiredError as err:
            raise ValueError("two_factor_required") from err
        except RateLimitError as err:
            raise ValueError("too_many_requests") from err
        except AuthenticationError as err:
            raise ValueError("invalid_credentials") from err
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("VAG Connect setup failed: %s", err)
            return False

    async def _poll_loop(self) -> None:
        """Background polling loop — runs independently of HA scheduler."""
        import asyncio as _asyncio  # noqa: PLC0415
        interval_s = max(
            self.entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL) * 60,
            _CC_MIN_INTERVAL_S,
        )
        while self._started:
            await _asyncio.sleep(interval_s)
            if not self._started:
                break
            try:
                vins = list(self.vehicles.keys())
                results = await _asyncio.gather(
                    *[self._cariad_client.get_status(vin) for vin in vins],
                    return_exceptions=True,
                )
                fresh: dict[str, Any] = {}
                for vin, result in zip(vins, results):
                    if isinstance(result, Exception):
                        _LOGGER.debug("Poll failed for %s: %s", vin, result)
                        fresh[vin] = self.vehicles.get(vin, {})
                    else:
                        from .cariad.models import VehicleData  # noqa: PLC0415
                        if isinstance(result, VehicleData):
                            data = result.to_dict()
                            data["_client"] = self._cariad_client
                            fresh[vin] = data
                with self._vehicles_lock:
                    self.vehicles.update(fresh)
                await self._async_push_update(fresh, success=True)
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("VAG Connect poll error: %s", err)
                await self._async_push_update({}, success=False)

    async def async_shutdown(self) -> None:
        """Stop polling loop and release resources."""
        self._started = False
        self._cariad_client = None
        _LOGGER.debug("VAG Connect: shutdown complete")

    @property
    def is_active(self) -> bool:
        """Return True if the CARIAD polling loop is active."""
        return self._started

    def _tokenstore_path(self) -> str:
        """Pfad zur Token-Datei im HA-Config-Verzeichnis.
        Tokens persist across HA restarts — no re-authentication needed.
        """
        import os  # noqa: PLC0415
        storage_dir = os.path.join(self.hass.config.config_dir, ".storage")
        os.makedirs(storage_dir, exist_ok=True)
        return os.path.join(
            storage_dir,
            f"vag_connect_tokens_{self.entry.entry_id}.json"
        )


    async def _async_push_update(self, data: dict, success: bool = True) -> None:
        """Push vehicle data to HA.

        Implements log_when_unavailable: logs once when going offline,
        once when coming back online — never fills logs with repeated errors.
        Also removes stale devices when vehicles disappear from the account.
        """
        if success:
            if not self._was_available:
                _LOGGER.info(
                    "VAG Connect: Fahrzeug wieder erreichbar (%s)",
                    self.entry.data.get("username", ""),
                )
                self._was_available = True

            # Remove devices for VINs no longer present in the account
            await self._async_remove_stale_devices(set(data.keys()))

            self.async_set_updated_data(data)
            _LOGGER.debug("VAG Connect: Push zu HA — %d Fahrzeug(e)", len(data))
        else:
            if self._was_available:
                _LOGGER.warning(
                    "VAG Connect: Fahrzeug nicht erreichbar — Entities auf unavailable gesetzt (%s)",
                    self.entry.data.get("username", ""),
                )
                self._was_available = False
            self.last_update_success = False
            self.async_update_listeners()

    async def _async_remove_stale_devices(self, current_vins: set) -> None:
        """Remove device registry entries for VINs no longer in the account.

        Implements the stale-devices Gold quality scale rule.
        Only removes devices that were previously seen (in coordinator.data)
        but are no longer returned by the API.
        """
        if not self.data:
            return  # First run — nothing to clean up

        from homeassistant.helpers import device_registry as dr  # noqa: PLC0415
        from .const import DOMAIN as _DOMAIN  # noqa: PLC0415

        device_reg = dr.async_get(self.hass)
        previous_vins = set(self.data.keys()) - {"_meta"}

        for stale_vin in previous_vins - current_vins:
            device_entry = device_reg.async_get_device(
                identifiers={(_DOMAIN, stale_vin)}
            )
            if device_entry is not None:
                _LOGGER.info(
                    "VAG Connect: Fahrzeug %s nicht mehr im Account — Gerät entfernt",
                    stale_vin,
                )
                device_reg.async_remove_device(device_entry.id)


    async def _async_update_data(self) -> dict[str, Any]:
        """Manual refresh — fetches fresh status for all known VINs."""
        if not self._started or self._cariad_client is None:
            with self._vehicles_lock:
                return dict(self.vehicles)
        try:
            import asyncio as _asyncio  # noqa: PLC0415
            vins = list(self.vehicles.keys())
            results = await _asyncio.gather(
                *[self._cariad_client.get_status(vin) for vin in vins],
                return_exceptions=True,
            )
            with self._vehicles_lock:
                for vin, result in zip(vins, results):
                    if isinstance(result, Exception):
                        _LOGGER.debug("Refresh failed for %s: %s", vin, result)
                        continue
                    from .cariad.models import VehicleData  # noqa: PLC0415
                    if isinstance(result, VehicleData):
                        data = result.to_dict()
                        data["_client"] = self._cariad_client
                        self.vehicles[vin] = data
            _LOGGER.debug("VAG Connect: Manual refresh OK")
            return dict(self.vehicles)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("VAG Connect: Manual refresh failed: %s", err)
            with self._vehicles_lock:
                return dict(self.vehicles)


    async def async_lock(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_lock")

    async def async_unlock(self, vin: str) -> None:
        spin = self.entry.data.get(CONF_SPIN) or ""
        await self._cariad_cmd(vin, "command_unlock", spin=spin)

    async def async_start_climatisation(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_start_climate")

    async def async_stop_climatisation(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_stop_climate")

    async def async_start_charging(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_start_charging")

    async def async_stop_charging(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_stop_charging")

    async def async_flash_lights(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_flash")

    async def async_set_target_soc(self, vin: str, target: int) -> None:
        await self._cariad_cmd(vin, "command_set_target_soc", target=target)

    async def async_set_climatisation_temperature(self, vin: str, temp_c: float) -> None:
        await self._cariad_cmd(vin, "command_set_climate_temperature", temp_c=temp_c)

    async def async_set_departure_timer(
        self,
        vin: str,
        timer_id: int,
        enabled: bool,
        departure_time: str | None,
    ) -> None:
        """Set a departure timer via CARIAD API."""
        await self._cariad_cmd(
            vin,
            "command_set_departure_timer",
            timer_id=timer_id,
            enabled=enabled,
            departure_time=departure_time,
        )

    async def _cariad_cmd(self, vin: str, method: str, **kwargs: Any) -> None:
        """Dispatch a command to the CARIAD client then refresh state."""
        if self._cariad_client is None:
            _LOGGER.error("VAG Connect: no CARIAD client — cannot execute %s", method)
            return
        try:
            fn = getattr(self._cariad_client, method)
            await fn(vin, **kwargs)
            await self.async_request_refresh()
            _LOGGER.debug("VAG Connect: %s(%s) OK", method, vin)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("VAG Connect: %s(%s) failed: %s", method, vin, err)
            raise

    async def async_set_max_charge_current(self, vin: str, ampere: int) -> None:
        """Set max charge current — informational, refresh state."""
        _LOGGER.info("VAG: max_charge_current %sA for %s", ampere, vin)
        await self.async_request_refresh()

    async def async_start_window_heating(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_start_climate")

    async def async_stop_window_heating(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_stop_climate")

    async def async_wake_vehicle(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_wake")

