# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Switches for VAG Connect (lock/unlock, charging)."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VagConnectCoordinator = entry.runtime_data
    # v1.12.0 (#63) — Read-only Mode: switches send commands, skip all.
    if coordinator.is_read_only():
        return
    entities: list[SwitchEntity] = []

    for vin, vehicle in coordinator.vehicles.items():
        entities.append(VagLockSwitch(coordinator, vin))
        entities.append(VagClimatisationSwitch(coordinator, vin))
        entities.append(VagWindowHeatingSwitch(coordinator, vin))
        # VagSeatHeatingSwitch + VagAutoUnlockSwitch removed in v1.8.0:
        # they relied on internal CarConnectivity object mutation that no
        # longer exists in our own CARIAD client. They will return once a
        # real API command is implemented. See issue #60.
        if vehicle.get("has_battery"):  # EV + PHEV
            entities.append(VagChargingSwitch(coordinator, vin))
            for timer_id in (1, 2, 3):
                entities.append(VagDepartureTimerSwitch(coordinator, vin, timer_id))

    async_add_entities(entities)


class VagLockSwitch(VagConnectEntity, SwitchEntity):
    """Door lock toggle."""

    _attr_translation_key = "lock_switch"
    _attr_icon = "mdi:car-door-lock"
    # v1.9.1 — Phase 2 gating mirrors VagDoorLock (same backend command).
    _command_id = "command_lock"

    def __init__(self, coordinator: VagConnectCoordinator, vin: str) -> None:
        super().__init__(coordinator, vin, "lock_switch")

    @property
    def is_on(self) -> bool | None:
        return self._vehicle.get("doors_locked")

    async def async_turn_on(self, **kwargs: object) -> None:
        await self.coordinator.async_lock(self._vin)

    async def async_turn_off(self, **kwargs: object) -> None:
        await self.coordinator.async_unlock(self._vin)


class VagClimatisationSwitch(VagConnectEntity, SwitchEntity):
    """Pre-conditioning toggle."""

    _attr_translation_key = "climatisation_switch"
    _attr_icon = "mdi:thermometer"
    # v1.9.1 — Phase 2 gating.
    _command_id = "command_start_climate"

    def __init__(self, coordinator: VagConnectCoordinator, vin: str) -> None:
        super().__init__(coordinator, vin, "climatisation_switch")

    @property
    def is_on(self) -> bool | None:
        state = self._vehicle.get("climatisation_state")
        if state is None:
            return None
        return str(state).lower() not in ("off", "stopped", "")

    async def async_turn_on(self, **kwargs: object) -> None:
        await self.coordinator.async_start_climatisation(self._vin)

    async def async_turn_off(self, **kwargs: object) -> None:
        await self.coordinator.async_stop_climatisation(self._vin)


class VagChargingSwitch(VagConnectEntity, SwitchEntity):
    """Charging toggle."""

    _attr_translation_key = "charging_switch"
    _attr_icon = "mdi:ev-plug-type2"
    # v1.9.1 — Phase 2 gating.
    _command_id = "command_start_charging"

    def __init__(self, coordinator: VagConnectCoordinator, vin: str) -> None:
        super().__init__(coordinator, vin, "charging_switch")

    @property
    def is_on(self) -> bool | None:
        state = self._vehicle.get("charging_state")
        if state is None:
            return None
        return str(state).lower() in ("charging", "conservationcharging")

    async def async_turn_on(self, **kwargs: object) -> None:
        await self.coordinator.async_start_charging(self._vin)

    async def async_turn_off(self, **kwargs: object) -> None:
        await self.coordinator.async_stop_charging(self._vin)


class VagWindowHeatingSwitch(VagConnectEntity, SwitchEntity):
    """Window heating on/off."""

    _attr_translation_key = "window_heating_switch"
    _attr_icon = "mdi:car-windshield"
    # v1.9.1 — Phase 2 gating.
    _command_id = "command_start_window_heating"

    def __init__(self, coordinator: VagConnectCoordinator, vin: str) -> None:
        super().__init__(coordinator, vin, "window_heating_switch")

    @property
    def is_on(self) -> bool | None:
        val = self._vehicle.get("window_heating_front")
        return bool(val) if val is not None else None

    async def async_turn_on(self, **kwargs: object) -> None:
        await self.coordinator.async_start_window_heating(self._vin)

    async def async_turn_off(self, **kwargs: object) -> None:
        await self.coordinator.async_stop_window_heating(self._vin)


class VagDepartureTimerSwitch(VagConnectEntity, SwitchEntity):
    """Enable or disable a departure timer (1–3)."""

    _attr_icon = "mdi:clock-time-eight-outline"

    def __init__(self, coordinator: VagConnectCoordinator, vin: str, timer_id: int) -> None:
        super().__init__(coordinator, vin, f"departure_timer_{timer_id}_switch")
        self._timer_id = timer_id
        self._attr_translation_key = f"departure_timer_{timer_id}_switch"

    @property
    def is_on(self) -> bool | None:
        return self._vehicle.get(f"departure_timer_{self._timer_id}_enabled")

    async def async_turn_on(self, **kwargs: object) -> None:
        await self.coordinator.async_set_departure_timer(
            self._vin, self._timer_id, enabled=True, departure_time=None
        )

    async def async_turn_off(self, **kwargs: object) -> None:
        await self.coordinator.async_set_departure_timer(
            self._vin, self._timer_id, enabled=False, departure_time=None
        )
