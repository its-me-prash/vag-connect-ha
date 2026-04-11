"""Base entity class for VAG Connect."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VagConnectCoordinator


def _device_name(vehicle: dict, brand: str) -> str:
    """
    Baut den Gerätenamen aus Marke + Modell.

    Ergebnis:  'Audi Q4 e-tron'  ->  entity_id wird sensor.audi_q4_e_tron_*
               'Skoda Enyaq iV'  ->  sensor.skoda_enyaq_iv_*

    Wenn kein Modell bekannt: Fallback auf '<Marke> <VIN-Ende>'
    damit mehrere unbekannte Fahrzeuge trotzdem unterschiedliche Namen haben.
    """
    model = vehicle.get("model") or ""
    # Modell-Namen saeubern: Leerzeichen/Sonderzeichen die HA slug unlesbar machen
    model = model.strip()

    if model and model.lower() not in ("vag vehicle", "unknown", ""):
        return f"{brand.title()} {model}"

    # Fallback: letzte 6 Zeichen der VIN
    vin = vehicle.get("vin", "")
    return f"{brand.title()} {vin[-6:]}" if vin else brand.title()


class VagConnectEntity(CoordinatorEntity[VagConnectCoordinator]):
    """
    Basis-Entity fuer alle VAG Connect Entities.

    Entity-ID Schema (mit has_entity_name=True):
        sensor.{brand}_{model}_{key}
    Beispiele:
        sensor.audi_q4_e_tron_tankfullstand
        sensor.skoda_enyaq_iv_ladestand
        sensor.volkswagen_id_4_kilometerstand

    Mehrere Fahrzeuge desselben Modells:
        sensor.audi_q4_e_tron_tankfullstand   (erstes)
        sensor.audi_q4_e_tron_2_tankfullstand (zweites - HA setzt _2 automatisch)

    Jedes Fahrzeug bekommt ein eigenes Geraet im Geraete-Register (pro VIN).
    Mehrere Konten (z.B. Audi + Skoda) = mehrere Config Entries = getrennte Koordinatoren.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VagConnectCoordinator,
        vin: str,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._vin = vin
        self._key = key
        # unique_id: VIN-basiert -> bleibt stabil bei Modellumbenennung
        self._attr_unique_id = f"{vin}_{key}"

    @property
    def _vehicle(self) -> dict:
        """Aktuelles Fahrzeug-Dict. Sicher gegen None beim Start."""
        return (self.coordinator.data or {}).get(self._vin, {})

    @property
    def device_info(self) -> DeviceInfo:
        """
        Alle Entities desselben Fahrzeugs teilen ein HA-Geraet.
        Name = '{Marke} {Modell}' -> bestimmt die entity_id-Prefix.
        """
        vehicle = self._vehicle
        brand = self.coordinator.entry.data.get("brand", "vag")
        name = _device_name(vehicle, brand)

        return DeviceInfo(
            identifiers={(DOMAIN, self._vin)},
            name=name,
            model=vehicle.get("model") or "VAG Vehicle",
            manufacturer=brand.title(),
            serial_number=self._vin,
            # model_year falls verfuegbar
            hw_version=str(vehicle.get("model_year")) if vehicle.get("model_year") else None,
        )
