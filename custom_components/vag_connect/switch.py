"""Switches for VAG Connect (lock/unlock, charging)."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VagConnectCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SwitchEntity] = []

    for vin, vehicle in coordinator.vehicles.items():
        entities.append(VagLockSwitch(coordinator, vin))
        entities.append(VagClimatisationSwitch(coordinator, vin))
        entities.append(VagWindowHeatingSwitch(coordinator, vin))
        entities.append(VagSeatHeatingSwitch(coordinator, vin))
        if vehicle.get("has_battery"):  # EV + PHEV
            entities.append(VagChargingSwitch(coordinator, vin))

    async_add_entities(entities)


class VagLockSwitch(VagConnectEntity, SwitchEntity):
    """Toggle door lock."""

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
    """Toggle climatisation."""

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
    """Toggle charging (EVs only)."""

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
    """Fensterheizung Ein/Aus."""

    _attr_name = "Fensterheizung"
    _attr_icon = "mdi:car-windshield"

    def __init__(self, coordinator, vin):
        super().__init__(coordinator, vin, "window_heating_switch")

    @property
    def is_on(self) -> bool | None:
        from carconnectivity.window_heating import WindowHeatings  # noqa: PLC0415
        try:
            state = self._vehicle.get("_vehicle").window_heatings.heating_state.value
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
