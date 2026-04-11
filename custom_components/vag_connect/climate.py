"""Climate entity for VAG Connect — remote pre-conditioning."""

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity

DEFAULT_TEMP = 21.0
MIN_TEMP = 16.0
MAX_TEMP = 30.0
TEMP_STEP = 0.5

# CarConnectivity ClimatizationState values that mean "active"
_ACTIVE_STATES = {"HEATING", "COOLING", "VENTILATION"}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VagConnectCoordinator = entry.runtime_data
    async_add_entities(
        [VagClimate(coordinator, vin) for vin in coordinator.vehicles]
    )


class VagClimate(VagConnectEntity, ClimateEntity):
    """Climate entity — maps to vehicle pre-conditioning."""

    _attr_name = "Vorklimatisierung"
    _attr_icon = "mdi:thermometer"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT_COOL]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_target_temperature_step = TEMP_STEP

    def __init__(self, coordinator: VagConnectCoordinator, vin: str) -> None:
        super().__init__(coordinator, vin, "climate")

    @property
    def hvac_mode(self) -> HVACMode:
        state = self._vehicle.get("climatisation_state")
        if state and state in _ACTIVE_STATES:
            return HVACMode.HEAT_COOL
        return HVACMode.OFF

    @property
    def current_temperature(self) -> float | None:
        return self._vehicle.get("outside_temp")

    @property
    def target_temperature(self) -> float | None:
        t = self._vehicle.get("target_temperature")
        return float(t) if t is not None else DEFAULT_TEMP

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.HEAT_COOL:
            await self.coordinator.async_start_climatisation(self._vin)
        else:
            await self.coordinator.async_stop_climatisation(self._vin)

    async def async_set_temperature(self, **kwargs) -> None:
        temp = kwargs.get("temperature", DEFAULT_TEMP)
        await self.coordinator.async_set_climatisation_temperature(
            self._vin, float(temp)
        )
