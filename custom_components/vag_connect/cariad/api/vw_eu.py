# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Volkswagen EU API client — emea.bff.cariad.digital."""

from __future__ import annotations

import logging
from typing import Any

from ..models import BRAND_VW_EU, VehicleData
from .base import CariadBaseClient

_LOGGER = logging.getLogger(__name__)

_BASE = "https://emea.bff.cariad.digital"

_SELECTIVE_STATUS_JOBS = ",".join([
    "access",
    "automation",
    "batteryChargingCare",
    "charging",
    "climatisation",
    "climatisationTimers",
    "departureProfiles",
    "departureTimers",
    "fuelStatus",
    "measurements",
    "readiness",
    "userCapabilities",
    "vehicleLights",
    "vehicleHealthInspection",
])


class VWEUClient(CariadBaseClient):
    """VW EU / WeConnect client — emea.bff.cariad.digital.

    Also serves as base for AudiClient (same endpoints, extra auth).
    Data paths documented in docs/research/VAG_GROUP_ECOSYSTEM.md.
    """

    def __init__(self, session: Any, email: str, password: str, spin: str = "") -> None:
        super().__init__(session, BRAND_VW_EU, email, password, spin)

    async def get_vehicles(self) -> list[str]:
        """Return list of VINs from the CARIAD garage."""
        data = await self._get(f"{_BASE}/vehicle/v1/vehicles")
        vehicles: list[dict[str, Any]] = data.get("data", [])
        vins = [v["vin"] for v in vehicles if v.get("vin")]
        _LOGGER.debug("Found %d VW vehicle(s)", len(vins))
        return vins

    async def get_status(self, vin: str) -> VehicleData:
        """Fetch full vehicle status via selectivestatus."""
        url = f"{_BASE}/vehicle/v1/vehicles/{vin}/selectivestatus"
        raw: dict[str, Any] = await self._get(url, params={"jobs": _SELECTIVE_STATUS_JOBS})

        # Parking position (separate endpoint)
        parking: dict[str, Any] = {}
        try:
            parking = await self._get(f"{_BASE}/vehicle/v1/vehicles/{vin}/parkingposition")
        except Exception:  # noqa: BLE001
            pass

        return self._parse_status(vin, raw, parking)

    async def command_lock(self, vin: str) -> None:
        """Lock vehicle."""
        await self._post(
            f"{_BASE}/vehicle/v1/vehicles/{vin}/access/lock-unlock",
            json={"action": "lock"},
        )

    async def command_unlock(self, vin: str, spin: str = "") -> None:
        """Unlock vehicle — S-PIN required if set."""
        payload: dict[str, Any] = {"action": "unlock"}
        if spin or self._spin:
            payload["spin"] = spin or self._spin
        await self._post(
            f"{_BASE}/vehicle/v1/vehicles/{vin}/access/lock-unlock",
            json=payload,
        )

    async def command_start_climate(self, vin: str) -> None:
        """Start pre-conditioning."""
        await self._post(
            f"{_BASE}/vehicle/v1/vehicles/{vin}/climatisation/start-stop",
            json={"action": "start"},
        )

    async def command_stop_climate(self, vin: str) -> None:
        """Stop pre-conditioning."""
        await self._post(
            f"{_BASE}/vehicle/v1/vehicles/{vin}/climatisation/start-stop",
            json={"action": "stop"},
        )

    async def command_start_charging(self, vin: str) -> None:
        """Start charging."""
        await self._post(
            f"{_BASE}/vehicle/v1/vehicles/{vin}/charging/start-stop",
            json={"action": "start"},
        )

    async def command_stop_charging(self, vin: str) -> None:
        """Stop charging."""
        await self._post(
            f"{_BASE}/vehicle/v1/vehicles/{vin}/charging/start-stop",
            json={"action": "stop"},
        )

    async def command_flash(self, vin: str) -> None:
        """Honk and flash."""
        await self._post(
            f"{_BASE}/vehicle/v1/vehicles/{vin}/vehicleLights/flash",
            json={"action": "flash"},
        )

    async def command_wake(self, vin: str) -> None:
        """Wake vehicle."""
        await self._post(f"{_BASE}/vehicle/v1/vehicles/{vin}/vehicleWakeup")

    async def command_set_target_soc(self, vin: str, target: int) -> None:
        """Set charge target SoC."""
        await self._post(
            f"{_BASE}/vehicle/v1/vehicles/{vin}/charging/settings",
            json={"targetSOC_pct": target},
        )

    async def command_set_climate_temperature(self, vin: str, temp_c: float) -> None:
        """Set pre-conditioning temperature."""
        await self._post(
            f"{_BASE}/vehicle/v1/vehicles/{vin}/climatisation/settings",
            json={"targetTemperature_C": temp_c},
        )

    async def command_set_departure_timer(
        self,
        vin: str,
        timer_id: int,
        enabled: bool,
        departure_time: str | None,
    ) -> None:
        """Set a departure timer (1–3).

        Args:
            vin:            Vehicle VIN
            timer_id:       1, 2 or 3
            enabled:        True to enable, False to disable
            departure_time: "HH:MM" format, e.g. "07:30" (None = keep existing)
        """
        payload: dict[str, Any] = {"id": timer_id, "enabled": enabled}
        if departure_time:
            payload["departureTime"] = {"time": departure_time}
        await self._post(
            f"{_BASE}/vehicle/v1/vehicles/{vin}/climatisation/timers",
            json=payload,
        )

    # ── data parsing ───────────────────────────────────────────────────────────

    def _parse_status(
        self,
        vin: str,
        raw: dict[str, Any],
        parking: dict[str, Any],
    ) -> VehicleData:
        """Map raw selectivestatus JSON → VehicleData.

        Path documentation: docs/research/VAG_GROUP_ECOSYSTEM.md
        """
        v = self._val
        d = VehicleData(vin=vin)

        # ── Charging ──────────────────────────────────────────────────────────
        d.charging_state = v(raw, "charging", "chargingStatus", "value", "chargingState")
        d.is_charging = d.charging_state == "CHARGING"
        d.charging_power_kw = v(raw, "charging", "chargingStatus", "value", "chargePower_kW")
        d.charging_rate_kmh = v(raw, "charging", "chargingStatus", "value", "chargeRate_kmph")

        remaining_min: Any = v(raw, "charging", "chargingStatus", "value", "remainingChargingTimeToComplete_min")
        if remaining_min is not None:
            from datetime import datetime, timezone, timedelta  # noqa: PLC0415
            d.charge_complete_eta = datetime.now(tz=timezone.utc) + timedelta(minutes=int(remaining_min))

        d.battery_soc = v(raw, "charging", "batteryStatus", "value", "currentSOC_pct")
        battery_range = v(raw, "charging", "batteryStatus", "value", "cruisingRangeElectric_km")
        if battery_range is not None:
            d.range_km = int(battery_range)

        plug_state = v(raw, "charging", "plugStatus", "value", "plugConnectionState")
        d.plug_state = plug_state
        d.plug_connected = plug_state == "CONNECTED"
        d.connector_locked = v(raw, "charging", "plugStatus", "value", "plugLockState") == "LOCKED"

        d.target_soc = v(raw, "charging", "chargingSettings", "value", "targetSOC_pct")
        max_ac = v(raw, "charging", "chargingSettings", "value", "maxChargeCurrentAC_A")
        if max_ac is not None:
            d.max_charge_current = float(max_ac)
        d.auto_unlock_charge = (
            v(raw, "charging", "chargingSettings", "value", "autoUnlockPlugWhenChargedAC") == "ON"
        )

        charging_type = v(raw, "charging", "chargingStatus", "value", "chargeType")
        d.charging_type = charging_type

        # ── Drivetrain detection ───────────────────────────────────────────────
        primary_engine = v(raw, "fuelStatus", "rangeStatus", "value", "primaryEngine", "type")
        secondary_engine = v(raw, "fuelStatus", "rangeStatus", "value", "secondaryEngine", "type")
        car_type = v(raw, "measurements", "fuelLevelStatus", "value", "carType")

        electric_types = {"electric", "ev"}
        combustion_types = {"gasoline", "diesel", "gas", "cng", "lpg"}

        if primary_engine:
            d.has_battery = primary_engine.lower() in electric_types
            d.has_combustion = primary_engine.lower() in combustion_types

        if secondary_engine:
            if secondary_engine.lower() in electric_types:
                d.has_battery = True
            if secondary_engine.lower() in combustion_types:
                d.has_combustion = True

        if car_type:
            lower = car_type.lower()
            if "electric" in lower:
                d.has_battery = True
            if any(x in lower for x in ("gasoline", "diesel", "gas")):
                d.has_combustion = True

        d.is_electric = d.has_battery and not d.has_combustion
        d.is_hybrid = d.has_battery and d.has_combustion

        # ── Fuel / range ──────────────────────────────────────────────────────
        d.fuel_level = v(raw, "measurements", "fuelLevelStatus", "value", "currentFuelLevel_pct")
        total_range = v(raw, "fuelStatus", "rangeStatus", "value", "totalRange_km")
        if total_range is not None:
            d.range_km = int(total_range)

        elec_range = v(raw, "fuelStatus", "rangeStatus", "value", "primaryEngine", "remainingRange_km")
        if elec_range is not None and d.has_battery:
            d.range_km = int(elec_range)

        adblue = v(raw, "measurements", "rangeStatus", "value", "adBlueRange")
        if adblue is not None:
            d.adblue_range_km = int(adblue)

        # ── Measurements ──────────────────────────────────────────────────────
        d.odometer_km = v(raw, "measurements", "odometerStatus", "value", "odometer")
        d.outside_temp = v(raw, "measurements", "outsideTemperatureStatus", "value", "outsideTemperature_K")
        if d.outside_temp is not None:
            d.outside_temp = round(float(d.outside_temp) - 273.15, 1)  # Kelvin → Celsius

        bat_min = v(raw, "measurements", "temperatureBatteryStatus", "value", "temperatureHvBatteryMin_K")
        if bat_min is not None:
            d.battery_temp = round(float(bat_min) - 273.15, 1)

        # ── Access / doors / windows ──────────────────────────────────────────
        d.doors_locked = v(raw, "access", "accessStatus", "value", "doorLockStatus") == "LOCKED"
        overall = v(raw, "access", "accessStatus", "value", "overallStatus")
        d.doors_open = False
        d.windows_open = False
        if overall == "UNSAFE":
            doors: list[dict[str, Any]] = v(raw, "access", "accessStatus", "value", "doors") or []
            d.doors_open = any(
                door.get("status", [{}])[0].get("value") == "open"
                for door in doors
                if door.get("status")
            )
            windows: list[dict[str, Any]] = v(raw, "access", "accessStatus", "value", "windows") or []
            d.windows_open = any(
                w.get("status", [{}])[0].get("value") == "open"
                for w in windows
                if w.get("status")
            )
            # Per-door breakdown
            d.doors_individual = {
                door["name"]: door.get("status", [{}])[0].get("value") == "open"
                for door in doors
                if door.get("name") and door.get("status")
            }

        # ── Climatisation ─────────────────────────────────────────────────────
        d.climatisation_state = v(raw, "climatisation", "climatisationStatus", "value", "climatisationState")
        d.climatisation_active = d.climatisation_state not in (None, "OFF", "CLIMATISATION_STATUS_UNAVAILABLE")
        d.target_temperature = v(raw, "climatisation", "climatisationSettings", "value", "targetTemperature_C")

        wh_status = v(raw, "climatisation", "windowHeatingStatus", "value", "windowHeatingStatus") or []
        for wh in wh_status:
            location = wh.get("windowLocation", "")
            state = wh.get("windowHeatingState") == "ON"
            if "front" in location.lower():
                d.window_heating_front = state
            elif "rear" in location.lower() or "back" in location.lower():
                d.window_heating_back = state

        # ── Readiness / online ─────────────────────────────────────────────────
        d.is_online = v(raw, "readiness", "readinessStatus", "value", "connectionState", "isOnline") is True

        # ── Vehicle health / service ──────────────────────────────────────────
        d.service_km = v(raw, "vehicleHealthInspection", "maintenanceStatus", "value", "inspectionDue_km")
        d.service_due_at = v(raw, "vehicleHealthInspection", "maintenanceStatus", "value", "inspectionDue_days")
        d.oil_service_km = v(raw, "vehicleHealthInspection", "maintenanceStatus", "value", "oilServiceDue_km")
        d.oil_service_at = v(raw, "vehicleHealthInspection", "maintenanceStatus", "value", "oilServiceDue_days")

        # ── Departure timers ──────────────────────────────────────────────────
        timers: list[dict[str, Any]] = v(raw, "departureTimers", "departureTimersStatus", "value", "timers") or []
        for i, timer in enumerate(timers[:3], 1):
            enabled = timer.get("enabled", False)
            time_str = timer.get("departureTime", {}).get("time") if timer.get("departureTime") else None
            setattr(d, f"departure_timer_{i}_enabled", enabled)
            setattr(d, f"departure_timer_{i}_time", time_str)

        # ── Parking position ──────────────────────────────────────────────────
        if parking:
            d.latitude = parking.get("lat")
            d.longitude = parking.get("lon")

        return d
