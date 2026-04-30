# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Sensor platform for VAG Connect.

The VagSensorDescription.condition field gates sensor creation:
  "electric"  — EV and PHEV only (has_battery=True)
  "combustion" — combustion and PHEV only (has_combustion=True)
  None        — all vehicles

charging_rate_kmh uses SensorDeviceClass.SPEED so HA auto-converts km/h ↔ mph
based on the user's unit system preference.
"""
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfLength,
    UnitOfPower,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity


@dataclass(frozen=True)
class VagSensorDescription(SensorEntityDescription):
    """Sensor description with coordinator data key, condition, and optional default-disabled flag."""

    data_key: str = ""
    condition: str | None = None  # "electric" | "combustion" | None
    suggested_display_precision: int | None = None


SENSOR_DESCRIPTIONS: tuple[VagSensorDescription, ...] = (

    VagSensorDescription(
        key="fuel_level",
        translation_key="fuel_level",
        data_key="fuel_level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gas-station",
        condition="combustion",
    ),
    VagSensorDescription(
        key="battery_soc",
        translation_key="battery_soc",
        data_key="battery_soc",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging",
        condition="electric",
    ),
    VagSensorDescription(
        key="range_km",
        translation_key="range_km",
        data_key="range_km",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:map-marker-distance",
        suggested_display_precision=0,
    ),

    # v1.10.0 (#94, #91) — explicit per-energy-source range sensors.
    # Conditional creation in ``async_setup_entry`` is data-present-gated
    # in addition to the ``condition`` flag: even an EV that *has*
    # has_battery=True won't get a phantom ``electric_range_km`` entity
    # if the API didn't actually publish ``electric_range_km`` for it.
    # That solves the "unknown" clutter complaint in #94.
    VagSensorDescription(
        key="electric_range_km",
        translation_key="electric_range_km",
        data_key="electric_range_km",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging-outline",
        condition="electric",
        suggested_display_precision=0,
    ),
    VagSensorDescription(
        key="combustion_range_km",
        translation_key="combustion_range_km",
        data_key="combustion_range_km",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gas-station",
        condition="combustion",
        suggested_display_precision=0,
    ),
    VagSensorDescription(
        key="total_range_km",
        translation_key="total_range_km",
        data_key="total_range_km",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:map-marker-distance",
        suggested_display_precision=0,
        # No ``condition`` — total is meaningful for any drivetrain that
        # publishes the field. Pure EVs typically don't (so the gating
        # below filters it out anyway), but plug-in hybrids and ICE
        # vehicles with a combined trip-meter range get it.
    ),

    VagSensorDescription(
        key="odometer_km",
        translation_key="odometer_km",
        data_key="odometer_km",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
        suggested_display_precision=0,
    ),

    VagSensorDescription(
        key="charging_state",
        translation_key="charging_state",
        data_key="charging_state",
        icon="mdi:ev-plug-type2",
        condition="electric",
    ),
    VagSensorDescription(
        key="plug_state",
        translation_key="plug_state",
        data_key="plug_state",
        icon="mdi:power-plug",
        condition="electric",
    ),
    VagSensorDescription(
        key="target_soc",
        translation_key="target_soc",
        data_key="target_soc",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging-high",
        condition="electric",
    ),
    VagSensorDescription(
        key="charging_power_kw",
        translation_key="charging_power_kw",
        data_key="charging_power_kw",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
        condition="electric",
    ),
    VagSensorDescription(
        key="charging_rate_kmh",
        translation_key="charging_rate_kmh",
        data_key="charging_rate_kmh",
        # km/h = km Reichweite pro Stunde → device_class=SPEED → HA rechnet km/h ↔ mph
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging-outline",
        condition="electric",
        suggested_display_precision=0,
    ),
    VagSensorDescription(
        key="charge_complete_eta",
        translation_key="charge_complete_eta",
        data_key="charge_complete_eta",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-end",
        condition="electric",
    ),
    VagSensorDescription(
        key="charging_type",
        translation_key="charging_type",
        data_key="charging_type",
        icon="mdi:ev-plug-type2",
        entity_category=EntityCategory.DIAGNOSTIC,
        condition="electric",
    ),


    VagSensorDescription(
        key="climatisation_state",
        translation_key="climatisation_state",
        data_key="climatisation_state",
        icon="mdi:thermometer",
    ),
    VagSensorDescription(
        key="target_temperature",
        translation_key="target_temperature",
        data_key="target_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer-auto",
    ),

    VagSensorDescription(
        key="outside_temp",
        translation_key="outside_temp",
        data_key="outside_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),

    VagSensorDescription(
        key="service_km",
        translation_key="service_km",
        data_key="service_km",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:wrench-clock",
        suggested_display_precision=0,
    ),
    VagSensorDescription(
        key="service_due_at",
        translation_key="service_due_at",
        data_key="service_due_at",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:calendar-clock",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # v1.11.0 (#91 closure) — explicit "days remaining" int sensor
    # alongside the DATE sensor above. The DATE conversion loses the
    # exact day count; this one keeps it for users who want "5 Tage"
    # rather than "May 5". Unit "d" makes HA render "5 d" automatically.
    VagSensorDescription(
        key="service_due_in_days",
        translation_key="service_due_in_days",
        data_key="service_due_in_days",
        native_unit_of_measurement="d",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:calendar-clock",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
    ),
    VagSensorDescription(
        key="oil_service_km",
        translation_key="oil_service_km",
        data_key="oil_service_km",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:oil",
        condition="combustion",
        suggested_display_precision=0,
    ),
    VagSensorDescription(
        key="oil_service_at",
        translation_key="oil_service_at",
        data_key="oil_service_at",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:oil",
        entity_category=EntityCategory.DIAGNOSTIC,
        condition="combustion",
    ),
    # v1.11.0 (#91 closure) — explicit oil-service days int sensor.
    VagSensorDescription(
        key="oil_service_due_in_days",
        translation_key="oil_service_due_in_days",
        data_key="oil_service_due_in_days",
        native_unit_of_measurement="d",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:oil",
        entity_category=EntityCategory.DIAGNOSTIC,
        condition="combustion",
        suggested_display_precision=0,
    ),

    VagSensorDescription(
        key="vehicle_state",
        translation_key="vehicle_state",
        data_key="vehicle_state",
        icon="mdi:car-info",
    ),
    # v1.8.11 (Session 3S) — Connection-State Sensor.
    # Closes #54 (GitHobi). Three-state derived from carCapturedTimestamp:
    # online (<30 min), standby (<24 h, wakeable), offline (>=24 h, 12V flat
    # / underground / service mode). Currently only populated for Škoda;
    # other brands keep it None so HA shows "unknown" instead of false data.
    # Pattern verified against `homeassistant-myskoda` issues #751, #731.
    VagSensorDescription(
        key="connection_state",
        translation_key="connection_state",
        data_key="connection_state",
        icon="mdi:car-connected",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),

    VagSensorDescription(
        key="parking_address",
        translation_key="parking_address",
        data_key="parking_address",
        icon="mdi:map-marker",
    ),
    VagSensorDescription(
        key="parking_city",
        translation_key="parking_city",
        data_key="parking_city",
        icon="mdi:city",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),

    VagSensorDescription(
        key="battery_temp",
        translation_key="battery_temp",
        data_key="battery_temp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
        entity_category=EntityCategory.DIAGNOSTIC,
        condition="electric",
    ),

    VagSensorDescription(
        key="last_updated_at",
        translation_key="last_updated_at",
        data_key="last_updated_at",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-check-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),

    VagSensorDescription(
        key="departure_timer_1_time",
        translation_key="departure_timer_1_time",
        data_key="departure_timer_1_time",
        icon="mdi:clock-time-eight-outline",
        condition="electric",
    ),
    VagSensorDescription(
        key="departure_timer_2_time",
        translation_key="departure_timer_2_time",
        data_key="departure_timer_2_time",
        icon="mdi:clock-time-eight-outline",
        condition="electric",
    ),
    VagSensorDescription(
        key="departure_timer_3_time",
        translation_key="departure_timer_3_time",
        data_key="departure_timer_3_time",
        icon="mdi:clock-time-eight-outline",
        condition="electric",
    ),

    # ── AdBlue (Diesel) ──────────────────────────────────────────────────────
    VagSensorDescription(
        key="adblue_range_km",
        translation_key="adblue_range_km",
        data_key="adblue_range_km",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-check",
        condition="combustion",
        suggested_display_precision=0,
    ),

    # v1.11.0 (#91 closure) — vehicle lights count.
    # ``lights_count`` is the on-light count from
    # ``vehicleLights.lightsStatus.value.lights[]``. Created only when
    # the field is non-None (data-present-gated, like the v1.10.0
    # range entities) so vehicles whose API doesn't expose lights
    # don't get a phantom "0" entity.
    VagSensorDescription(
        key="lights_count",
        translation_key="lights_count",
        data_key="lights_count",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightbulb-on-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
    ),

    # v1.11.0 (#91 closure, #90 verified) — max charge current (Ampere)
    # as a read-only Sensor. The v1.9.1 Vehicle Data Scout findings
    # showed this as ``charging.chargingSettings.value.maxChargeCurrentAC_A
    # = 16`` on the Golf 7 GTE — clean integer, suitable for direct
    # display. The Number platform writeable variant is deferred to
    # v1.12.0 (Capability-Filter Phase 3 ships the dispatch + capability
    # check — without those, a writeable Number would 403 on most cars).
    VagSensorDescription(
        key="max_charge_current_a",
        translation_key="max_charge_current_a",
        data_key="max_charge_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-ac",
        condition="electric",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
    ),

    # ── v1.9.0 Vehicle Data Scout + Error Reporter ────────────────────────────
    # Two diagnostic sensors that surface drift / runtime errors detected
    # by the integration so users can 1-click report them via the HA Repair
    # dashboard. data_key="" — value comes from coordinator helpers, not
    # the vehicle dict — see ``ReporterSensor.native_value``.
    VagSensorDescription(
        key="api_observer_findings",
        translation_key="api_observer_findings",
        data_key="",
        icon="mdi:radar",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    VagSensorDescription(
        key="error_reporter_count",
        translation_key="error_reporter_count",
        data_key="",
        icon="mdi:alert-circle-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

# Sensor keys that read from coordinator helpers instead of the per-vehicle
# data dict. Kept in a frozenset so ``async_setup_entry`` can dispatch to
# the right entity class without scattering branch logic.
_REPORTER_KEYS: frozenset[str] = frozenset({
    "api_observer_findings",
    "error_reporter_count",
})

# v1.10.0 (#94) — keys that require the field to be non-None at setup
# time before the entity is created. Prevents phantom "unknown" entities
# on vehicles whose API simply doesn't publish a particular range source.
# Adding to this set is a deliberate per-key opt-in: most existing sensors
# legitimately start as None and populate later, so they should NOT be
# gated this way.
_DATA_PRESENT_REQUIRED: frozenset[str] = frozenset({
    "electric_range_km",
    "combustion_range_km",
    "total_range_km",
    # v1.11.0 (#91) — same phantom-entity-prevention reasoning. Vehicles
    # whose API doesn't expose ``vehicleLights.lightsStatus.value.lights[]``
    # shouldn't get a "0" sensor or default-False binary sensor.
    "lights_count",
})


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Sensor-Entities einrichten."""
    coordinator: VagConnectCoordinator = entry.runtime_data
    entities: list[VagConnectSensor] = []

    for vin, vehicle in coordinator.vehicles.items():
        has_battery    = vehicle.get("has_battery", False)
        has_combustion = vehicle.get("has_combustion", False)

        for desc in SENSOR_DESCRIPTIONS:
            if desc.condition == "electric" and not has_battery:
                continue
            if desc.condition == "combustion" and not has_combustion:
                continue
            # v1.10.0 (#94 acceptance criteria) — additional data-present
            # gating for the new range entities. Avoids "unknown"
            # phantom entities on vehicles that don't publish a
            # particular range source. Only applied to keys that opted
            # in via ``_DATA_PRESENT_REQUIRED`` so existing entities
            # (which may legitimately start as None and populate later)
            # keep their current creation semantics.
            if (
                desc.key in _DATA_PRESENT_REQUIRED
                and vehicle.get(desc.data_key) is None
            ):
                continue
            if desc.key in _REPORTER_KEYS:
                # v1.9.0 — reporter sensors read from coordinator helpers
                # rather than per-vehicle data fields.
                entities.append(ReporterSensor(coordinator, vin, desc))
            else:
                entities.append(VagConnectSensor(coordinator, vin, desc))

    async_add_entities(entities)


# Keys that return 0 instead of None when not charging/driving
# This prevents the sensor showing "unavailable" while connected but idle
_ZERO_WHEN_IDLE: frozenset[str] = frozenset({
    "charging_power_kw",
    "charging_rate_kmh",
})


class VagConnectSensor(VagConnectEntity, SensorEntity):
    entity_description: VagSensorDescription

    def __init__(
        self,
        coordinator: VagConnectCoordinator,
        vin: str,
        description: VagSensorDescription,
    ) -> None:
        super().__init__(coordinator, vin, description.key)
        self.entity_description = description
        if description.suggested_display_precision is not None:
            self._attr_suggested_display_precision = description.suggested_display_precision

    @property
    def native_value(self) -> Any:
        val = self._vehicle.get(self.entity_description.data_key)
        # charging_power_kw + charging_rate_kmh: API omits these when not charging.
        # Return 0 so the entity shows "0 kW / 0 km/h" instead of "unavailable".
        if val is None and self.entity_description.key in _ZERO_WHEN_IDLE:
            # Only return 0 if plug is connected (makes sense to show 0 kW)
            if self._vehicle.get("plug_connected"):
                return 0

        # DATE sensors: API may return int (days until event) or a date string.
        # HA SensorDeviceClass.DATE requires datetime.date — convert if needed.
        if (
            self.entity_description.device_class == SensorDeviceClass.DATE
            and val is not None
        ):
            if isinstance(val, int):
                from datetime import date, timedelta  # noqa: PLC0415
                return date.today() + timedelta(days=val)
            if isinstance(val, str):
                try:
                    from datetime import date as _date  # noqa: PLC0415
                    return _date.fromisoformat(val[:10])
                except ValueError:
                    return None

        return val


class ReporterSensor(VagConnectSensor):
    """v1.9.0 — Vehicle Data Scout / Error Reporter sensor.

    Reads from coordinator-level state (``unexpected_findings`` /
    ``error_buffer``) rather than the per-vehicle data dict. Surfaces
    counts so users can see drift / failures at a glance, and points at
    the HA Repair issue (raised by the reporter pipeline) for the 1-click
    GitHub-or-Copy workflow.

    Per-VIN even though Error Reporter is account-wide — keeps the entity
    layout consistent with every other diagnostic sensor and means the
    sensor still appears even when a single vehicle in a multi-VIN setup
    becomes unavailable.
    """

    @property
    def native_value(self) -> Any:
        key = self.entity_description.key
        coord = self.coordinator
        if key == "api_observer_findings":
            # Per-VIN count (not aggregate) so each vehicle's sensor reflects
            # only its own drift. Aggregate goes into the repair issue.
            findings: dict[str, dict[str, Any]] = (
                getattr(coord, "unexpected_findings", {}) or {}
            )
            return len(findings.get(self._vin, {}))
        if key == "error_reporter_count":
            # Account-wide count — auth/rate-limit errors aren't per-VIN
            # and the buffer is shared across all vehicles in the account.
            return coord.reporter_error_count() if hasattr(
                coord, "reporter_error_count"
            ) else 0
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Surface a tiny preview so the entity card is informative.

        Privacy: every value here has already passed through
        ``mask_value`` / ``_redact`` upstream. Don't add raw fields.
        """
        key = self.entity_description.key
        coord = self.coordinator
        if key == "api_observer_findings":
            findings = (getattr(coord, "unexpected_findings", {}) or {}).get(
                self._vin, {}
            )
            # Up to 5 most recent paths — keeps the attributes panel tidy
            # and avoids hammering the recorder with huge state dicts.
            preview = list(findings.keys())[-5:]
            return {
                "paths": preview,
                "report_url": "https://github.com/its-me-prash/vag-connect-ha/issues/new",
            }
        if key == "error_reporter_count":
            buffer = getattr(coord, "error_buffer", None)
            records = (buffer.records if buffer is not None else [])[-3:]
            return {
                "recent_types": [r.exception_type for r in records],
                "report_url": "https://github.com/its-me-prash/vag-connect-ha/issues/new",
            }
        return None
