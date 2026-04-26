# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Coordinator for VAG Connect — async polling via own CARIAD API client.

Data flow:
  CARIAD client polls VAG API → poll_loop pushes to HA via async_set_updated_data
  → asyncio.run_coroutine_threadsafe → async_set_updated_data → entities update.

Thread safety:
  _vehicles_lock (threading.Lock) guards self.vehicles.
  CARIAD client (async) writes vehicles dict; HA entities read via coordinator data.
"""

import asyncio
from datetime import datetime, timezone
import logging
import threading
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_BRAND,
    CONF_ENABLE_REVERSE_GEOCODING,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_SPIN,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from homeassistant.helpers import device_registry as dr
from .cariad.models import VehicleData

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

        # Per-VIN poll success tracking — entities use this for availability
        # so a single failing vehicle doesn't blank out the others.
        self.vehicle_success: dict[str, bool] = {}

        # Reverse-geocoding cache: {(round(lat,3), round(lon,3)): result}
        self._geocode_cache: dict[tuple[float, float], dict[str, str | None]] = {}

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
            results = await asyncio.gather(
                *[self._cariad_client.get_status(vin) for vin in vins],
                return_exceptions=True,
            )

            with self._vehicles_lock:
                for vin, result in zip(vins, results):
                    if isinstance(result, Exception):
                        _LOGGER.warning("Could not fetch status for %s: %s", vin, result)
                        self.vehicle_success[vin] = False
                        continue
                    if isinstance(result, VehicleData):
                        data = result.to_dict()
                        data["_client"] = self._cariad_client
                        self.vehicles[vin] = await self._enrich(data)
                        self.vehicle_success[vin] = True

            self._started = True
            found = len(self.vehicles)
            _LOGGER.info("VAG Connect: setup complete — %d vehicle(s)", found)

            # Start background polling — use background task so HA bootstrap doesn't wait
            self.hass.async_create_background_task(self._poll_loop(), f"{DOMAIN}_poll")
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
        """Background polling loop — runs independently of HA scheduler.

        Re-reads scan_interval from entry.options on every iteration so that
        Options-Flow changes take effect without a full integration reload.

        Nightly reduction (22:00–05:00): doubles the polling interval to reduce
        API calls and avoid rate limits during low-activity hours.
        """
        while self._started:
            # Re-read interval every iteration — picks up Options-Flow changes live
            interval_s = max(
                int(
                    self.entry.options.get(CONF_SCAN_INTERVAL)
                    or self.entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                ) * 60,
                _CC_MIN_INTERVAL_S,
            )
            # Nightly reduction: double interval between 22:00 and 05:00
            hour = datetime.now().hour
            if hour >= 22 or hour < 5:
                interval_s = interval_s * 2
                _LOGGER.debug("Nightly reduction active — interval doubled to %ds", interval_s)
            await asyncio.sleep(interval_s)
            if not self._started:
                break
            try:
                vins = list(self.vehicles.keys())
                results = await asyncio.gather(
                    *[self._cariad_client.get_status(vin) for vin in vins],
                    return_exceptions=True,
                )
                fresh: dict[str, Any] = {}
                any_success = False
                for vin, result in zip(vins, results):
                    if isinstance(result, Exception):
                        _LOGGER.debug("Poll failed for %s: %s", vin, result)
                        old = self.vehicles.get(vin, {})
                        old["_poll_failed"] = True
                        fresh[vin] = old
                        self.vehicle_success[vin] = False
                    elif isinstance(result, VehicleData):
                        data = result.to_dict()
                        data["_client"] = self._cariad_client
                        data["_poll_failed"] = False
                        fresh[vin] = await self._enrich(data)
                        any_success = True
                        self.vehicle_success[vin] = True
                    else:
                        fresh[vin] = self.vehicles.get(vin, {})
                        self.vehicle_success[vin] = False
                with self._vehicles_lock:
                    self.vehicles.update(fresh)
                await self._async_push_update(fresh, success=any_success)
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("VAG Connect poll error: %s", err)
                # Mark all known VINs as failed — avoids stale-as-fresh
                for vin in list(self.vehicles.keys()):
                    self.vehicle_success[vin] = False
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

    def is_vehicle_available(self, vin: str) -> bool:
        """Return True if the last poll for *vin* succeeded.

        Used by entities to expose per-VIN availability so a single failing
        vehicle does not blank out entities of other vehicles in the same
        account. Defaults to True for unknown VINs (covers initial setup).
        """
        return self.vehicle_success.get(vin, True)

    async def _async_push_update(self, data: dict, success: bool = True) -> None:
        """Push vehicle data to HA.

        Implements log_when_unavailable: logs once when going offline,
        once when coming back online — never fills logs with repeated errors.
        Also removes stale devices when vehicles disappear from the account.
        """
        if success:
            if not self._was_available:
                _LOGGER.info(
                    "VAG Connect: vehicle reachable again (%s)",
                    self.entry.data.get("username", ""),
                )
                self._was_available = True

            # Remove devices for VINs no longer present in the account
            await self._async_remove_stale_devices(set(data.keys()))

            self.async_set_updated_data(data)
            _LOGGER.debug("VAG Connect: pushed %d vehicle(s) to HA", len(data))
        else:
            if self._was_available:
                _LOGGER.warning(
                    "VAG Connect: vehicle unreachable — entities set to unavailable (%s)",
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


        device_reg = dr.async_get(self.hass)
        previous_vins = set(self.data.keys()) - {"_meta"}

        for stale_vin in previous_vins - current_vins:
            device_entry = device_reg.async_get_device(
                identifiers={(DOMAIN, stale_vin)}
            )
            if device_entry is not None:
                _LOGGER.info(
                    "VAG Connect: vehicle %s removed from account — device deleted",
                    stale_vin,
                )
                device_reg.async_remove_device(device_entry.id)



    async def _enrich(self, data: dict) -> dict:
        """Universal post-processing after every get_status() call.

        Sets fields that every brand should have but individual clients may omit:
        - last_updated_at: always UTC now
        - vehicle_state: derived from is_driving / charging_state / connection
        - is_driving: if not set by client, derive from vehicle_state
        - parking_address / parking_city: reverse geocode if lat/lon available (best-effort)
        """

        # Always stamp when we fetched
        data["last_updated_at"] = datetime.now(tz=timezone.utc)

        # Fix #32: Defensive is_charging reset.
        # When plug is disconnected, charging MUST be False regardless of API state.
        # Prevents is_charging staying stuck on "True" after charging ends.
        if not data.get("plug_connected") and data.get("is_charging"):
            data["is_charging"] = False
            _LOGGER.debug(
                "is_charging reset to False — plug not connected (defensive fix #32)"
            )

        # Derive vehicle_state if not set by client
        if not data.get("vehicle_state"):
            if not data.get("is_online", True):
                data["vehicle_state"] = "OFFLINE"
            elif data.get("is_driving"):
                data["vehicle_state"] = "DRIVING"
            elif data.get("is_charging"):
                data["vehicle_state"] = "CHARGING"
            else:
                data["vehicle_state"] = "PARKED"

        # Derive is_driving from vehicle_state if client didn't set it
        if not data.get("is_driving") and data.get("vehicle_state") == "DRIVING":
            data["is_driving"] = True

        # Reverse geocode parking position — opt-in, privacy-aware (#60).
        # Default OFF: vehicle GPS is sensitive and would otherwise be sent
        # to a third-party service (OpenStreetMap Nominatim) on every poll.
        if self._reverse_geocoding_enabled():
            lat = data.get("latitude")
            lon = data.get("longitude")
            if lat and lon and not data.get("parking_address"):
                try:
                    result = await self._reverse_geocode(float(lat), float(lon))
                    if result:
                        data["parking_address"] = result.get("address")
                        data["parking_city"] = result.get("city")
                except Exception:  # noqa: BLE001
                    pass  # geocoding is optional — never fail an update because of it

        return data

    def _reverse_geocoding_enabled(self) -> bool:
        """Return True if the user explicitly opted into reverse geocoding."""
        return bool(
            self.entry.options.get(CONF_ENABLE_REVERSE_GEOCODING, False)
            or self.entry.data.get(CONF_ENABLE_REVERSE_GEOCODING, False)
        )

    async def _reverse_geocode(
        self, lat: float, lon: float
    ) -> dict[str, str | None] | None:
        """Reverse geocode lat/lon via Nominatim using HA's shared aiohttp session.

        Coordinates are rounded to 3 decimals (~110m precision) for caching
        so we do not hit Nominatim every poll for the same parking spot.
        """
        from homeassistant.helpers.aiohttp_client import (  # noqa: PLC0415
            async_get_clientsession,
        )

        cache_key = (round(lat, 3), round(lon, 3))
        if cache_key in self._geocode_cache:
            return self._geocode_cache[cache_key]

        session = async_get_clientsession(self.hass)
        url = (
            "https://nominatim.openstreetmap.org/reverse"
            f"?lat={lat}&lon={lon}&format=json&addressdetails=1"
        )
        headers = {"User-Agent": "VAGConnect/1.x (+https://github.com/its-me-prash/vag-connect-ha)"}
        try:
            async with session.get(url, headers=headers, timeout=5) as resp:
                if resp.status != 200:
                    return None
                payload = await resp.json()
        except Exception:  # noqa: BLE001
            return None

        addr = payload.get("address", {}) if isinstance(payload, dict) else {}
        road = addr.get("road") or addr.get("pedestrian") or addr.get("path", "")
        house = addr.get("house_number", "")
        city = (
            addr.get("city")
            or addr.get("town")
            or addr.get("village")
            or addr.get("municipality", "")
        )
        display = payload.get("display_name", "") if isinstance(payload, dict) else ""

        street = f"{road} {house}".strip() if house else road
        address = (
            f"{street}, {city}".strip(", ")
            if street and city
            else (city or display[:60])
        )

        result: dict[str, str | None] = {
            "address": address or None,
            "city": city or None,
        }
        self._geocode_cache[cache_key] = result
        return result

    async def _async_update_data(self) -> dict[str, Any]:
        """Manual refresh — fetches fresh status for all known VINs."""
        if not self._started or self._cariad_client is None:
            with self._vehicles_lock:
                return dict(self.vehicles)
        try:
            vins = list(self.vehicles.keys())
            results = await asyncio.gather(
                *[self._cariad_client.get_status(vin) for vin in vins],
                return_exceptions=True,
            )
            with self._vehicles_lock:
                for vin, result in zip(vins, results):
                    if isinstance(result, Exception):
                        _LOGGER.debug("Refresh failed for %s: %s", vin, result)
                        continue
                    if isinstance(result, VehicleData):
                        data = result.to_dict()
                        data["_client"] = self._cariad_client
                        self.vehicles[vin] = await self._enrich(data)
            _LOGGER.debug("VAG Connect: Manual refresh OK")
            return dict(self.vehicles)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("VAG Connect: Manual refresh failed: %s", err)
            with self._vehicles_lock:
                return dict(self.vehicles)


    async def async_lock(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_lock")

    async def async_unlock(self, vin: str) -> None:
        spin = self.entry.options.get(CONF_SPIN) or self.entry.data.get(CONF_SPIN) or ""
        if not spin:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="spin_required",
            )
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
        # SEAT/CUPRA require the user position in the honk-and-flash payload
        # (HTTP 400 otherwise). Other brands accept and ignore it.
        vehicle = self.vehicles.get(vin, {})
        await self._cariad_cmd(
            vin,
            "command_flash",
            latitude=vehicle.get("latitude"),
            longitude=vehicle.get("longitude"),
        )

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

    async def async_set_charge_mode(self, vin: str, mode: str) -> None:
        """Set charging mode (MANUAL / TIMER / PREFERRED_CHARGING_TIMES)."""
        await self._cariad_cmd(vin, "command_set_charge_mode", mode=mode)

    async def async_set_min_soc(self, vin: str, min_soc: int) -> None:
        """Set minimum SoC for PHEV departure timer."""
        await self._cariad_cmd(vin, "command_set_min_soc", min_soc=min_soc)

    async def async_set_max_charge_current(self, vin: str, ampere: int) -> None:
        """Set max charge current — not supported by current API client.

        Raises ServiceValidationError so HA shows a clear error to the user
        instead of silently swallowing the action (#60). The entity itself
        is hidden in number.py until a real API command exists.
        """
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="feature_not_supported",
            translation_placeholders={"feature": "max_charge_current"},
        )

    async def async_start_window_heating(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_start_window_heating")

    async def async_stop_window_heating(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_stop_window_heating")

    async def async_wake_vehicle(self, vin: str) -> None:
        await self._cariad_cmd(vin, "command_wake")

