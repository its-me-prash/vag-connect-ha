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
    entities: list[SwitchEntity] = []

    for vin, vehicle in coordinator.vehicles.items():
        entities.append(VagLockSwitch(coordinator, vin))
        entities.append(VagClimatisationSwitch(coordinator, vin))
        entities.append(VagWindowHeatingSwitch(coordinator, vin))
        entities.append(VagSeatHeatingSwitch(coordinator, vin))
        if vehicle.get("has_battery"):  # EV + PHEV
            entities.append(VagAutoUnlockSwitch(coordinator, vin))
            entities.append(VagChargingSwitch(coordinator, vin))
            for timer_id in (1, 2, 3):
                entities.append(VagDepartureTimerSwitch(coordinator, vin, timer_id))

    async_add_entities(entities)


class VagLockSwitch(VagConnectEntity, SwitchEntity):
    """Door lock toggle."""

    _attr_name = "Türverriegelung"
    _attr_icon = "mdi:car-door-lock"

    def __init__(self, coordinator, vin):
        super().__init__(coordinator, vin, "lock_switch")

    @property
    def is_on(self) -> bool | None:
        return self._vehicle.get("doors_locked")

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_lock(self._vin)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_unlock(self._vin)


class VagClimatisationSwitch(VagConnectEntity, SwitchEntity):
    """Pre-conditioning toggle."""

    _attr_name = "Klimatisierung"
    _attr_icon = "mdi:thermometer"

    def __init__(self, coordinator, vin):
        super().__init__(coordinator, vin, "climatisation_switch")

    @property
    def is_on(self) -> bool | None:
        state = self._vehicle.get("climatisation_state")
        if state is None:
            return None
        return str(state).lower() not in ("off", "stopped", "")

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_start_climatisation(self._vin)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_stop_climatisation(self._vin)


class VagChargingSwitch(VagConnectEntity, SwitchEntity):
    """Charging toggle."""

    _attr_name = "Laden"
    _attr_icon = "mdi:ev-plug-type2"

    def __init__(self, coordinator, vin):
        super().__init__(coordinator, vin, "charging_switch")

    @property
    def is_on(self) -> bool | None:
        state = self._vehicle.get("charging_state")
        if state is None:
            return None
        return str(state).lower() in ("charging", "conservationcharging")

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_start_charging(self._vin)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_stop_charging(self._vin)


class VagWindowHeatingSwitch(VagConnectEntity, SwitchEntity):
    """Window heating on/off."""

    _attr_name = "Fensterheizung"
    _attr_icon = "mdi:car-windshield"

    def __init__(self, coordinator, vin):
        super().__init__(coordinator, vin, "window_heating_switch")

    @property
    def is_on(self) -> bool | None:
        from carconnectivity.window_heating import WindowHeatings  # noqa: PLC0415
        try:
            v = self._vehicle.get("_vehicle")
            if v is None:
                return None
            state = v.window_heatings.heating_state.value
            if state is None:
                return None
            return state not in (
                WindowHeatings.HeatingState.OFF,
                WindowHeatings.HeatingState.UNKNOWN,
                None,
            )
        except Exception:  # noqa: BLE001
            return None

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_start_window_heating(self._vin)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_stop_window_heating(self._vin)


class VagSeatHeatingSwitch(VagConnectEntity, SwitchEntity):
    """Sitzheizung Ein/Aus — Issue #6."""

    _attr_name = "Sitzheizung"
    _attr_icon = "mdi:car-seat-heater"

    def __init__(self, coordinator, vin):
        super().__init__(coordinator, vin, "seat_heating_switch")

    @property
    def is_on(self) -> bool | None:
        try:
            v = self._vehicle.get("_vehicle")
            if v is None:
                return None
            val = v.climatization.settings.seat_heating.value
            return bool(val) if val is not None else None
        except Exception:  # noqa: BLE001
            return None

    async def async_turn_on(self, **kwargs) -> None:
        async def _set():
            v = self._vehicle.get("_vehicle")
            if v:
                v.climatization.settings.seat_heating.value = True
        await self.coordinator.hass.async_add_executor_job(_set)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        async def _set():
            v = self._vehicle.get("_vehicle")
            if v:
                v.climatization.settings.seat_heating.value = False
        await self.coordinator.hass.async_add_executor_job(_set)
        await self.coordinator.async_request_refresh()


class VagAutoUnlockSwitch(VagConnectEntity, SwitchEntity):
    """Auto-unlock plug after charging completes."""

    _attr_name = "Stecker nach Laden entsperren"
    _attr_icon = "mdi:ev-plug-ccs2"

    def __init__(self, coordinator, vin):
        super().__init__(coordinator, vin, "auto_unlock_switch")

    @property
    def is_on(self) -> bool | None:
        return self._vehicle.get("auto_unlock_charge")

    async def async_turn_on(self, **kwargs) -> None:
        await self._set_auto_unlock(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set_auto_unlock(False)

    async def _set_auto_unlock(self, value: bool) -> None:
        def _do():
            v = self._vehicle.get("_vehicle")
            if v:
                v.charging.settings.auto_unlock.value = value
        await self.coordinator.hass.async_add_executor_job(_do)
        await self.coordinator.async_request_refresh()


class VagDepartureTimerSwitch(VagConnectEntity, SwitchEntity):
    """Enable or disable a departure timer (1–3)."""

    _attr_icon = "mdi:clock-time-eight-outline"

    def __init__(self, coordinator, vin, timer_id: int):
        super().__init__(coordinator, vin, f"departure_timer_{timer_id}_switch")
        self._timer_id = timer_id
        self._attr_name = f"Abfahrtstimer {timer_id}"

    @property
    def is_on(self) -> bool | None:
        return self._vehicle.get(f"departure_timer_{self._timer_id}_enabled")

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_departure_timer(
            self._vin, self._timer_id, enabled=True, departure_time=None
        )

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_departure_timer(
            self._vin, self._timer_id, enabled=False, departure_time=None
        )
