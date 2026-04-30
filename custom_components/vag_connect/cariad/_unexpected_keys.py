# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Vehicle Data Scout — detects JSON fields the parser doesn't read.

Mirrors the `tillsteinbach/CarConnectivity-*` "Unexpected Keys found"
pattern that has been our richest source of API findings (CC-seatcupra
issue #109 with Rainer's CUPRA Born live dump, CC-skoda issue #50 with
the Kodiaq iV 2026 complete response).

Architecture:
- Pure data layer: ``EXPECTED_KEYS`` declares paths we already read; the
  ``detect_unexpected`` function walks an actual response and yields
  ``UnexpectedField`` entries for paths NOT in the expected set.
- Privacy: every yielded sample value is anonymised via ``mask_value``
  (VIN/userID/GPS/email/token redaction) before leaving this module.
- Brand-agnostic: the EXPECTED_KEYS table is keyed by ``(brand, endpoint)``
  so each brand client can register its known shape.

Usage from a brand client::

    from cariad._unexpected_keys import detect_unexpected
    findings = list(detect_unexpected("skoda", "vehicle-status", raw_status))
    if findings:
        coordinator.record_unexpected_keys(vin, findings)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from ._util import mask_vin

# Patterns we always mask in sample values, regardless of field name.
# VINs are 17 chars alphanumeric; rough match is fine for redaction.
_VIN_RE = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b")
# Email addresses
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
# JWT-shaped tokens (3 base64 segments)
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
# UUIDs (used for userIDs)
_UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)


@dataclass(frozen=True)
class UnexpectedField:
    """A JSON path observed in a live response that our parser doesn't read.

    Attributes:
        path: Dotted JSON path, e.g. ``"charging.batteryStatus.value.temp_C"``.
        sample_masked: Anonymised string snippet of the value seen
            (truncated to 80 chars). NEVER contains raw VIN, userID,
            GPS coordinate or token.
        endpoint: Logical endpoint name (e.g. ``"vehicle-status"``).
        first_seen_at: Timestamp of first observation (UTC ISO string).
    """

    path: str
    sample_masked: str
    endpoint: str
    first_seen_at: str


# `EXPECTED_KEYS[brand][endpoint]` is a set of dotted paths we know about.
# Paths use lowercase brand names (matching ``BrandConfig.name``).
# Add to these as new fields are integrated, so they stop appearing as
# "unexpected" findings.
#
# Convention:
#   - Top-level keys: just the key, e.g. ``"overall"``
#   - Nested: dot-separated, e.g. ``"charging.batteryStatus.value"``
#   - Wildcards: ``"*"`` matches any single segment
#     (e.g. ``"doors.*.locked"`` covers ``doors.frontLeft.locked`` etc.)
#   - Don't list scalar leaf values (we report parent paths)
EXPECTED_KEYS: dict[str, dict[str, set[str]]] = {
    "skoda": {
        "vehicle-status": {
            "overall", "overall.doors", "overall.doorsLocked",
            "overall.windows", "overall.lights", "overall.locked",
            "overall.reliableLockStatus",
            "detail", "detail.sunroof", "detail.trunk", "detail.bonnet",
            "carCapturedTimestamp",
            "renders", "renders.lightMode.*", "renders.darkMode.*",
            "compositeRenders", "compositeRenders.*",
            "engine",
        },
        "charging": {
            "status", "status.battery", "status.battery.stateOfChargeInPercent",
            "status.battery.remainingCruisingRangeInMeters",
            "status.battery.carCapturedTimestamp",
            "status.state", "status.chargingState",
            "status.chargePowerInKw", "status.chargingRateInKilometersPerHour",
            "status.chargeType", "status.fullyChargedAt",
            "status.remainingTimeToFullyChargedInMinutes",
            "status.carCapturedTimestamp",
            "settings", "settings.targetStateOfChargeInPercent",
            "settings.autoUnlockPlugWhenChargedAC",
            "settings.maxChargeCurrentAC",
            "settings.carCapturedTimestamp",
        },
        "air-conditioning": {
            "state", "targetTemperature", "targetTemperature.temperatureValue",
            "windowHeatingState", "windowHeatingState.front", "windowHeatingState.rear",
            "chargerConnectionState", "chargerLockState",
            "carCapturedTimestamp",
        },
        "parking": {
            "parkingPosition", "parkingPosition.gpsCoordinates",
            "parkingPosition.gpsCoordinates.latitude",
            "parkingPosition.gpsCoordinates.longitude",
            "parkingPosition.formattedAddress",
            "carCapturedTimestamp",
        },
        "driving-range": {
            "totalRangeInKm", "electricRange", "electricRange.distanceInKm",
            "combustionRange", "adBlueRange", "adBlueRange.distanceInKm",
            "carCapturedTimestamp",
        },
        "maintenance": {
            "maintenanceReport", "maintenanceReport.mileageInKm",
            "maintenanceReport.inspectionDueInKm",
            "maintenanceReport.inspectionDueInDays",
            "maintenanceReport.oilServiceDueInKm",
            "maintenanceReport.oilServiceDueInDays",
            "carCapturedTimestamp",
        },
        "readiness": {
            "unreachable", "inMotion", "carCapturedTimestamp",
        },
    },
    "cupra": {
        "status": {
            "doors", "doors.*", "doors.*.locked", "doors.*.open",
            "windows", "windows.*", "windows.sunroof",
            "trunk", "trunk.open", "trunk.locked",
            "hood", "hood.open",
            # v1.10.2 (#53 Gerhard's Born Live-Dump 2026-04-30) — newer
            # OLA firmware ships flat top-level overall fields alongside
            # the structured tree.
            "hood.locked",
            "locked",        # overall door-locked bool
            "lights",        # vehicle lights state ("off"/"on")
            "updatedAt",     # alternate to carCapturedTimestamp
            "sunroof", "sunRoof",
            "engine",
            "access", "access.doorClosedLeftFront", "access.doorClosedRightFront",
            "access.doorClosedLeftBack", "access.doorClosedRightBack",
            "access.doorsOpenedCount", "access.windowsOpenedCount",
            "access.trunk", "access.trunkLocked", "access.trunkStatus",
            "access.hood", "access.hoodOpen", "access.sunroof",
            "access.sunroofOpen",
            "carCapturedTimestamp",
        },
        "mycar": {
            "measurements", "measurements.mileage", "measurements.mileage.value",
            "measurements.fuelLevelStatus",
            "measurements.fuelLevelStatus.value",
            "measurements.fuelLevelStatus.value.currentFuelLevel_pct",
            "measurements.batteryStatus",
            "measurements.batteryStatus.value",
            "measurements.batteryStatus.value.currentSOC_pct",
            "access", "access.accessStatus", "access.accessStatus.value",
            "access.accessStatus.value.doorLockStatus",
            # v1.10.2 (#53 Gerhard's Born Live-Dump) — top-level meta blocks.
            # We don't drill into them yet but registering silences the Scout.
            "engines",       # vehicle engine info block
            "services",      # subscribed services info block
            "carCapturedTimestamp",
        },
        "charging": {
            "battery", "battery.stateOfChargeInPercent", "battery.currentSOC_pct",
            # v1.10.2 (#53 Gerhard's Born Live-Dump) — Born 2026 firmware
            # uses camelCase field names.
            "battery.currentSocPercentage",
            "battery.estimatedRangeInKm",
            "currentPct",
            "charging", "state", "status", "chargingState",
            "chargePowerInKw", "chargePower_kW", "chargedPowerInKw",
            "chargeRateInKmPerHour", "chargeRate_kmph",
            "remainingTimeInMinutes", "remainingTime",
            "remainingTimeToFullyChargedInMinutes", "remainingChargingTime",
            "chargeType", "chargingType", "type",
            "chargeMode", "preferredChargeMode", "mode",
            "settings", "active", "batteryCardStatus", "progressBarPct",
            "plug", "plug.connectionState", "plug.plugConnectionState",
            "plug.lockState", "plug.externalPower",
            # v1.10.2 (#53 Gerhard) — short field name variants on Born 2026.
            "plug.connection",
            "plug.lock",
            # v1.10.2 (#53 Gerhard) — nested ``charging.*`` paths (the
            # backend wraps the flat fields above into a nested object on
            # newer firmware as well).
            "charging.state",
            "charging.remainingTimeInMinutes",
            "charging.chargedPowerInKw",
            "charging.type",
            "charging.mode",
            "charging.settings",
        },
        "charging-info": {
            "targetSOC_pct", "targetSoc_pct", "targetStateOfChargeInPercent",
            "maxChargeCurrentAC", "maxChargeCurrent",
            "autoUnlockPlugWhenCharged", "autoUnlockPlugWhenChargedAC",
            # v1.10.2 (#53 Gerhard's Born Live-Dump) — wrapper blocks
            # for the new charge-care subsystem.
            "settings",
            "chargingCareSettings",
            "chargingCareStatus",
            "carCapturedTimestamp",
        },
        "climatisation": {
            "status", "status.climatisationState", "status.state",
            "settings", "settings.targetTemperature_K",
            "settings.targetTemperatureInCelsius", "targetTemperatureCelsius",
            "outsideTemperature",
            "windowHeatingStateFront", "windowHeatingStateRear",
            "carCapturedTimestamp",
        },
    },
    # SEAT shares OLA endpoints with CUPRA — same expected-keys table.
    "seat": {},  # populated at module load below
    "volkswagen": {
        "selectivestatus": {
            "access", "access.accessStatus", "access.accessStatus.value",
            "access.accessStatus.value.overallStatus",
            "access.accessStatus.value.carCapturedTimestamp",
            "access.accessStatus.value.doors", "access.accessStatus.value.windows",
            "access.accessStatus.value.doorLockStatus",
            "charging", "charging.batteryStatus", "charging.batteryStatus.value",
            "charging.batteryStatus.value.currentSOC_pct",
            "charging.batteryStatus.value.cruisingRangeElectric_km",
            "charging.batteryStatus.value.carCapturedTimestamp",
            "charging.chargingStatus", "charging.chargingStatus.value",
            "charging.chargingStatus.value.chargingState",
            "charging.chargingStatus.value.chargePower_kW",
            "charging.chargingStatus.value.chargeMode",
            "charging.chargingStatus.value.chargeType",
            "charging.chargingStatus.value.remainingChargingTimeToComplete_min",
            "charging.chargingStatus.value.chargingSettings",
            "charging.chargingStatus.value.chargingScenario",
            "charging.chargingStatus.value.carCapturedTimestamp",
            "charging.chargingSettings", "charging.chargingSettings.value",
            "charging.chargingSettings.value.targetSOC_pct",
            "charging.chargingSettings.value.maxChargeCurrentAC",
            # v1.9.1 (#90, Golf 7 GTE Live-Dump) — VW EU added the
            # explicit ampere variant alongside the legacy enum string.
            "charging.chargingSettings.value.maxChargeCurrentAC_A",
            "charging.chargingSettings.value.autoUnlockPlugWhenChargedAC",
            "charging.chargingSettings.value.carCapturedTimestamp",
            # v1.9.1 (#90) — top-level chargeMode block on selectivestatus.
            # Same content as chargingStatus.value.chargeMode, just exposed
            # at the brand level too. Don't recurse — already covered above.
            "charging.chargeMode",
            "charging.plugStatus", "charging.plugStatus.value",
            "charging.plugStatus.value.plugConnectionState",
            "charging.plugStatus.value.plugLockState",
            "charging.plugStatus.value.externalPower",
            "charging.plugStatus.value.ledColor",
            "charging.plugStatus.value.carCapturedTimestamp",
            "climatisation", "climatisation.climatisationStatus",
            "climatisation.climatisationStatus.value",
            "climatisation.climatisationStatus.value.climatisationState",
            "climatisation.climatisationStatus.value.remainingClimatisationTime_min",
            "climatisation.climatisationStatus.value.carCapturedTimestamp",
            "climatisation.climatisationSettings",
            "climatisation.climatisationSettings.value",
            "climatisation.climatisationSettings.value.targetTemperature_C",
            # v1.9.1 (#90) — Fahrenheit pair to celsius (US-region exposure).
            "climatisation.climatisationSettings.value.targetTemperature_F",
            # v1.9.1 (#90) — flag indicating climate without external power.
            "climatisation.climatisationSettings.value.climatisationWithoutExternalPower",
            "climatisation.climatisationSettings.value.carCapturedTimestamp",
            "climatisation.windowHeatingStatus",
            "climatisation.windowHeatingStatus.value",
            "climatisation.windowHeatingStatus.value.windowHeatingStatus",
            "climatisation.windowHeatingStatus.value.carCapturedTimestamp",
            "measurements", "measurements.rangeStatus",
            "measurements.rangeStatus.value",
            "measurements.rangeStatus.value.electricRange",
            # v1.9.1 (#91, Audi S6 TDI) — diesel range alongside electric
            # for ICE / plug-in vehicles. Same pattern as Skoda's
            # adblue_range exposure.
            "measurements.rangeStatus.value.dieselRange",
            "measurements.rangeStatus.value.gasolineRange",
            "measurements.rangeStatus.value.totalRange_km",
            "measurements.rangeStatus.value.carCapturedTimestamp",
            "measurements.odometerStatus",
            "measurements.odometerStatus.value",
            "measurements.odometerStatus.value.odometer",
            "measurements.odometerStatus.value.carCapturedTimestamp",
            "measurements.fuelLevelStatus",
            "measurements.fuelLevelStatus.value",
            "measurements.fuelLevelStatus.value.currentSOC_pct",
            # v1.9.1 (#91) — combustion fuel level percentage. Same key
            # pattern as currentSOC_pct but for the petrol/diesel tank.
            "measurements.fuelLevelStatus.value.currentFuelLevel_pct",
            "measurements.fuelLevelStatus.value.primaryEngineType",
            "measurements.fuelLevelStatus.value.carType",
            "measurements.fuelLevelStatus.value.carCapturedTimestamp",
            "measurements.temperatureBatteryStatus",
            "measurements.temperatureBatteryStatus.value",
            "measurements.temperatureBatteryStatus.value.carCapturedTimestamp",
            "measurements.temperatureOutsideStatus",
            "measurements.temperatureOutsideStatus.value",
            "measurements.temperatureOutsideStatus.value.temperatureOutside_K",
            "measurements.temperatureOutsideStatus.value.carCapturedTimestamp",
            "readiness", "readiness.readinessStatus",
            "readiness.readinessStatus.value",
            "readiness.readinessStatus.value.connectionState",
            "readiness.readinessStatus.value.connectionWarning",
            "vehicleLights", "vehicleLights.lightsStatus",
            "vehicleLights.lightsStatus.value",
            # v1.9.1 (#90 + #91) — explicit nested fields on lightsStatus.
            "vehicleLights.lightsStatus.value.carCapturedTimestamp",
            "vehicleLights.lightsStatus.value.lights",
            # v1.9.1 (#90 + #91) — top-level diagnostic blocks added
            # in newer firmware. We don't read them yet, but registering
            # them silences the Vehicle Data Scout for these well-known
            # branches. Future feature work can drill into the children.
            "userCapabilities",
            "fuelStatus",
            "vehicleHealthInspection",
            "vehicleHealthWarnings",
            # v1.9.1 (#90, Golf 7 GTE) — automation block (timers, smart
            # charging schedules) and departureProfiles (replacement for
            # the older departureTimers — see ROADMAP "PPE Climate Body").
            "automation",
            "departureProfiles",
            # v1.12.0 (#103 Audi + #104 VW EU, 2026-04-30) — intermediate
            # ``.{xxxStatus}`` / ``.warningLights`` / ``.chargeMode.error``
            # wrappers below the top-level meta blocks. The detector
            # correctly descended past the registered parents and saw
            # these wrappers as unknown — registering silences the Scout
            # for them. We don't need to drill deeper because v1.9.1
            # already registered the leaf paths under each (e.g.
            # ``vehicleHealthInspection.maintenanceStatus.value...``).
            "userCapabilities.capabilitiesStatus",
            "fuelStatus.rangeStatus",
            "vehicleHealthInspection.maintenanceStatus",
            "vehicleHealthWarnings.warningLights",
            "automation.climatisationTimer",
            "automation.chargingProfiles",
            "departureProfiles.departureProfilesStatus",
            # ``charging.chargeMode.error`` — same Bad-Gateway-style
            # error wrapper as ``fuelStatus.rangeStatus.error`` from #96.
            # Older firmwares wrap fields in error objects when the
            # backend can't compute them. Defensive registration.
            "charging.chargeMode.error",
        },
        "parkingposition": {
            "data", "data.lon", "data.lat", "data.carCapturedTimestamp",
        },
    },
    # Audi inherits VW EU's selectivestatus shape (same backend, same endpoint).
    "audi": {},  # populated at module load below
}

# SEAT and CUPRA share the OLA backend — same expected-keys table
EXPECTED_KEYS["seat"] = EXPECTED_KEYS["cupra"]
# Audi inherits VW EU's CARIAD-BFF expected keys (same selectivestatus endpoint)
EXPECTED_KEYS["audi"] = EXPECTED_KEYS["volkswagen"]


def _path_matches(path: str, expected_paths: set[str]) -> bool:
    """Check whether ``path`` is covered by ``expected_paths`` (with wildcards).

    Wildcards: a path component ``"*"`` in expected matches any single
    actual component. So ``"doors.*.locked"`` matches
    ``"doors.frontLeft.locked"``.
    """
    if path in expected_paths:
        return True
    actual_parts = path.split(".")
    for expected in expected_paths:
        if "*" not in expected:
            continue
        expected_parts = expected.split(".")
        if len(expected_parts) != len(actual_parts):
            continue
        if all(e == "*" or e == a for e, a in zip(expected_parts, actual_parts)):
            return True
    return False


def mask_value(value: Any, *, max_len: int = 80) -> str:
    """Anonymise a sample value for logging / external sharing.

    - VINs (17-char alphanumeric blocks) → ``***{last 6 chars}``
    - Email addresses → ``***@***``
    - JWT-shaped tokens → ``[token]``
    - UUIDs → ``[uuid]``
    - Latitude/longitude pairs in numeric values → kept (rounded to 1
      decimal place ≈ 11 km precision) — useful for "is this a EU vehicle"
      kind of context without exposing precise location
    - Strings: redacted then truncated to ``max_len``
    - Numbers / bools / None: stringified (no leak risk)
    - Dicts / lists: shape only (e.g. ``{4 keys}`` or ``[3 items]``)
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int,)):
        return str(value)
    if isinstance(value, float):
        # Round to 1 decimal — kills GPS precision (1.0° ≈ 111km)
        return f"{value:.1f}"
    if isinstance(value, str):
        s = value
        s = _VIN_RE.sub(lambda m: mask_vin(m.group(0)), s)
        s = _EMAIL_RE.sub("***@***", s)
        s = _JWT_RE.sub("[token]", s)
        s = _UUID_RE.sub("[uuid]", s)
        if len(s) > max_len:
            s = s[: max_len - 3] + "..."
        return f'"{s}"'
    if isinstance(value, dict):
        return f"{{{len(value)} keys}}"
    if isinstance(value, list):
        return f"[{len(value)} items]"
    # Fallback: type only
    return f"<{type(value).__name__}>"


def detect_unexpected(
    brand: str,
    endpoint: str,
    response: Any,
    *,
    parent_path: str = "",
    max_depth: int = 6,
) -> Iterable[UnexpectedField]:
    """Walk ``response`` and yield ``UnexpectedField`` for paths NOT in
    ``EXPECTED_KEYS[brand][endpoint]``.

    Behaviour:
    - Returns nothing if the brand or endpoint is not registered (keeps
      old brand clients quiet until they opt in).
    - Walks dicts only — list contents are not recursed (the list
      itself is reported if its parent path is unexpected).
    - Stops at ``max_depth`` to avoid pathological responses tying up
      the event loop.
    - Always yields ``parent_path`` is reported once even if it has many
      unknown children (we don't spam — finer detail comes via individual
      child paths up to ``max_depth``).
    """
    from datetime import datetime, timezone  # local to avoid module-load cost

    expected = EXPECTED_KEYS.get(brand, {}).get(endpoint)
    if expected is None:
        return  # brand/endpoint not registered for detection
    if not isinstance(response, dict):
        return
    now = datetime.now(tz=timezone.utc).isoformat()

    def _walk(node: Any, path: str, depth: int) -> Iterable[UnexpectedField]:
        if depth > max_depth:
            return
        if not isinstance(node, dict):
            return
        for key, val in node.items():
            child_path = f"{path}.{key}" if path else key
            if not _path_matches(child_path, expected):
                yield UnexpectedField(
                    path=child_path,
                    sample_masked=mask_value(val),
                    endpoint=endpoint,
                    first_seen_at=now,
                )
                # Don't recurse into unknown subtree — single report per branch
                continue
            if isinstance(val, dict):
                yield from _walk(val, child_path, depth + 1)

    yield from _walk(response, parent_path, depth=0)
