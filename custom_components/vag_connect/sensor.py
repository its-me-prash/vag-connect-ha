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
    UnitOfElectricPotential,
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
    # display. v1.12.0 also exposes a writeable Number entity for the
    # same field (see number.py); the read-only Sensor stays as a
    # quick at-a-glance diagnostic.
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

    # v1.12.0 (#23) — 12V starter battery voltage. Older vehicles see
    # silent API outages when 12V drops below ~10.8 V because the
    # cellular modem can't keep itself awake. This sensor surfaces the
    # voltage so users see "go to garage" warnings before the integration
    # appears to "stop working".
    VagSensorDescription(
        key="voltage_12v",
        translation_key="voltage_12v",
        data_key="voltage_12v",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:car-battery",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
    ),

    # v1.12.0 (#55) — daily wake-up counter. Vehicles cap remote wake-up
    # commands per day (typically 3-5 depending on backend). Once
    # exceeded the car silently ignores wake requests until midnight.
    # This sensor surfaces the count so users + automations can budget.
    VagSensorDescription(
        key="wake_count_today",
        translation_key="wake_count_today",
        data_key="wake_count_today",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:alarm-multiple",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
    ),
    # v1.15.0 — Skoda software-version (mysmob, app v8.10.0+).
    # Population depends on Skoda backend; entity is gated via
    # ``_DATA_PRESENT_REQUIRED`` so non-Skoda vehicles + older Skoda
    # firmwares don't get a phantom "unknown" entity.
    VagSensorDescription(
        key="software_version",
        translation_key="software_version",
        data_key="software_version",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # v1.15.0 (#35) — Skoda Charging History → HA Energy Dashboard.
    # ``total_charged_energy_kwh`` with TOTAL_INCREASING is THE long-
    # term-statistics signal users want for kWh-tracking dashboards.
    # Last-session sensors complement with at-a-glance recent context.
    # ``recent_charging_sessions`` (last 5) lives in the
    # ``total_charged_energy_kwh.extra_state_attributes`` (same audi
    # #113 pattern we used for Trip Stats in v1.14.0).
    VagSensorDescription(
        key="total_charged_energy_kwh",
        translation_key="total_charged_energy_kwh",
        data_key="total_charged_energy_kwh",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt-circle",
        suggested_display_precision=2,
        condition="electric",
    ),
    VagSensorDescription(
        key="last_charging_session_kwh",
        translation_key="last_charging_session_kwh",
        data_key="last_charging_session_kwh",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging",
        suggested_display_precision=2,
        condition="electric",
    ),
    VagSensorDescription(
        key="last_charging_session_duration_min",
        translation_key="last_charging_session_duration_min",
        data_key="last_charging_session_duration_min",
        native_unit_of_measurement="min",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer-outline",
        suggested_display_precision=0,
        condition="electric",
    ),
    # v1.16.0 (#25, #31) — Skoda Charging Profiles read-only sensors.
    # The killer field: ``active_charging_profile_name`` from the
    # backend's ``currentVehiclePositionProfile`` (the backend already
    # decided which profile is active based on the car's current GPS
    # position — solves #25 location-based target SoC without any
    # client-side GPS-zone matching).
    VagSensorDescription(
        key="active_charging_profile_name",
        translation_key="active_charging_profile_name",
        data_key="active_charging_profile_name",
        icon="mdi:map-marker-radius",
        condition="electric",
    ),
    VagSensorDescription(
        key="active_charging_profile_target_soc_pct",
        translation_key="active_charging_profile_target_soc_pct",
        data_key="active_charging_profile_target_soc_pct",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging-90",
        suggested_display_precision=0,
        condition="electric",
    ),
    VagSensorDescription(
        key="next_charging_time",
        translation_key="next_charging_time",
        data_key="next_charging_time",
        icon="mdi:clock-time-eight-outline",
        condition="electric",
    ),
    VagSensorDescription(
        key="charging_profiles_count",
        translation_key="charging_profiles_count",
        data_key="charging_profiles_count",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:format-list-numbered",
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
        condition="electric",
    ),
    # v1.17.1 (Bruno seq 10/11) — SEAT/CUPRA Battery Care read-only.
    # Two thin OLA endpoints surface battery-care mode + target SoC.
    # Skoda has equivalent under different paths (covered v1.15.0 cap-id
    # work). Brand-restricted via _DATA_PRESENT_REQUIRED gating below.
    VagSensorDescription(
        key="battery_care_target_soc_pct",
        translation_key="battery_care_target_soc_pct",
        data_key="battery_care_target_soc_pct",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-heart",
        suggested_display_precision=0,
        condition="electric",
    ),

    # ── v1.9.0 Vehicle Data Scout + Error Reporter ────────────────────────────
    # Two diagnostic sensors that surface drift / runtime errors detected
    # by the integration so users can 1-click report them via the HA Repair
    # dashboard. data_key="" — value comes from coordinator helpers, not
    # the vehicle dict — see ``ReporterSensor.native_value``.
    # ── v1.14.0 (#24) — Trip Statistics (Audi + VW EU) ────────────────
    # Subscription-required (Audi connect Plus / WeConnect Plus).
    # Phase 3 capability gate (#56) hides these entities for accounts
    # without the subscription. Data populated by 1h cache cycle in
    # ``coordinator.refresh_trip_statistics`` from the CARIAD-BFF
    # ``GET /vehicle/v1/vehicles/{vin}/tripstatistics`` endpoint.
    # ``recent_trips`` (list of last 5) lives in
    # ``last_trip_distance_km.extra_state_attributes`` to avoid the
    # 255-char state limit for list-shaped data.
    VagSensorDescription(
        key="last_trip_distance_km",
        translation_key="last_trip_distance_km",
        data_key="last_trip_distance_km",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:road-variant",
        suggested_display_precision=1,
    ),
    VagSensorDescription(
        key="last_trip_avg_speed_kmh",
        translation_key="last_trip_avg_speed_kmh",
        data_key="last_trip_avg_speed_kmh",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
        suggested_display_precision=0,
    ),
    VagSensorDescription(
        key="last_trip_avg_fuel_consumption_l_100km",
        translation_key="last_trip_avg_fuel_consumption_l_100km",
        data_key="last_trip_avg_fuel_consumption_l_100km",
        native_unit_of_measurement="L/100 km",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gas-station",
        suggested_display_precision=1,
        condition="combustion",
    ),
    VagSensorDescription(
        key="last_trip_avg_electric_consumption_kwh_100km",
        translation_key="last_trip_avg_electric_consumption_kwh_100km",
        data_key="last_trip_avg_electric_consumption_kwh_100km",
        native_unit_of_measurement="kWh/100 km",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightning-bolt",
        suggested_display_precision=1,
        condition="electric",
    ),

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
    # v1.12.0 (#23) — older vehicles + non-CARIAD backends don't expose
    # ``lvBattery``; don't create a phantom 0 V sensor for them.
    "voltage_12v",
    # v1.15.0 — Skoda-only software-version (mysmob app v8.10.0+).
    # Cross-brand support deferred — CARIAD-BFF + OLA don't expose an
    # equivalent endpoint yet (Research 2026-05-02).
    "software_version",
    # v1.15.0 (#35) — Skoda-only charging history. Cross-brand deferred
    # (CARIAD-BFF/OLA equivalent endpoints unverified).
    "total_charged_energy_kwh",
    "last_charging_session_kwh",
    "last_charging_session_duration_min",
    # v1.16.0 (#25, #31) — Skoda-only charging profiles. Same cross-
    # brand deferral. Even on Skoda these stay None for accounts
    # without configured profiles → don't create phantom entities.
    "active_charging_profile_name",
    "active_charging_profile_target_soc_pct",
    "next_charging_time",
    "charging_profiles_count",
    # v1.17.1 (Bruno seq 11) — SEAT/CUPRA battery-care target SoC.
    # Field stays None for non-OLA brands and for accounts where
    # battery-care isn't supported / configured.
    "battery_care_target_soc_pct",
})

# v1.14.0 (#24) — Trip Statistics is brand-restricted at the API level
# (CARIAD-BFF only — Audi + VW EU). Other brands' clients don't expose
# ``get_trip_statistics``. Gate at setup so SEAT/CUPRA/Skoda/Porsche/VW NA
# users don't get four "unknown" sensors per VIN. Capability gating
# (Phase 3, #56) further hides them when the subscription is absent.
_TRIP_STATS_KEYS: frozenset[str] = frozenset({
    "last_trip_distance_km",
    "last_trip_avg_speed_kmh",
    "last_trip_avg_fuel_consumption_l_100km",
    "last_trip_avg_electric_consumption_kwh_100km",
})
_TRIP_STATS_BRANDS: frozenset[str] = frozenset({"audi", "volkswagen"})


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Sensor-Entities einrichten."""
    coordinator: VagConnectCoordinator = entry.runtime_data
    # v1.14.0 (#24) — read brand once for trip-stats brand-restriction.
    brand = str(entry.data.get("brand", "")).lower()
    trip_stats_supported = brand in _TRIP_STATS_BRANDS
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
            # v1.14.0 (#24) — Trip Stats brand-gate. Skip the four
            # tripstatistics sensors entirely for non-CARIAD brands so
            # SEAT/CUPRA/Skoda/Porsche/VW NA users don't see "unknown"
            # entities forever. Phase 3 capability filter additionally
            # hides them when the audi/vw subscription is missing.
            if desc.key in _TRIP_STATS_KEYS:
                if not trip_stats_supported:
                    continue
                if (
                    coordinator.command_capability_supported(vin, "command_trip_stats")
                    is False
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
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """v1.14.0 (#24) — Surface ``recent_trips`` (last 5 short-term
        trips) on the ``last_trip_distance_km`` sensor.

        Pattern from audi #113 — list-shaped data goes into attributes
        because HA caps state strings at 255 chars and per-trip metadata
        easily exceeds that. Other sensors return ``None`` so we don't
        accidentally inflate recorder rows.
        """
        if self.entity_description.key == "last_trip_distance_km":
            recent = self._vehicle.get("recent_trips")
            if isinstance(recent, list) and recent:
                return {"recent_trips": recent[: 5]}
        # v1.15.0 (#35) — Skoda charging-history recent sessions go on
        # the cumulative total sensor. Same audi #113 pattern: list-
        # shaped data lives in attributes to dodge the 255-char state
        # limit + recorder bloat.
        if self.entity_description.key == "total_charged_energy_kwh":
            recent = self._vehicle.get("recent_charging_sessions")
            ct = self._vehicle.get("last_charging_session_current_type")
            attrs: dict[str, Any] = {}
            if isinstance(recent, list) and recent:
                attrs["recent_sessions"] = recent[:5]
            if isinstance(ct, str) and ct:
                attrs["last_session_current_type"] = ct
            return attrs or None
        # v1.16.0 (#25, #31) — Full registered profiles list lives in
        # attributes on the active-profile sensor so users can see all
        # configured locations + their per-location target SoCs at a
        # glance without needing 4× sensors per profile.
        if self.entity_description.key == "active_charging_profile_name":
            profiles = self._vehicle.get("charging_profiles")
            if isinstance(profiles, list) and profiles:
                return {"profiles": profiles}
        # v1.17.7 (#130 Chr1sDub + #133 christianmhz, 2026-05-04) —
        # Skoda preferred-workshop block surfaced on the
        # ``service_due_in_days`` sensor. Same audi #113 pattern:
        # composite metadata lives in attributes (workshop name,
        # contact, address, location, partner-id) so the sensor's
        # native_value (the int day-count) stays clean for templates.
        # Other brands keep returning None until they grow analogous
        # parsing.
        if self.entity_description.key == "service_due_in_days":
            workshop = self._vehicle.get("preferred_workshop")
            if isinstance(workshop, dict) and workshop:
                return {"preferred_workshop": workshop}
        return None

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
