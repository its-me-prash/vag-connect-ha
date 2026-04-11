"""
VagConnectCoordinator — reaktiver Ansatz mit CarConnectivity Observer-Pattern.

Architektur:
  - cc.startup() startet den CC Background-Thread (pollt VAG-API autonom)
  - Wir registrieren Observer auf der Garage: VALUE_CHANGED, on_transaction_end=True
  - Observer-Callback brückt von CC-Thread zu HA asyncio-Loop via run_coroutine_threadsafe
  - HA update_interval = None (kein eigenes Polling)
  - Manuelles Refresh via Button oder Service bleibt möglich
  - Korrekte Shutdown-Sequenz: cc.shutdown() stoppt CC-Background-Thread sauber

Minimum-Intervall Audi-Connector: 180 Sekunden (3 Minuten)
Empfohlen: 300 Sekunden (5 Minuten) → konfigurierbar in HA-Optionen
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_BRAND,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_SPIN,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Minimum interval enforced by Audi connector (seconds)
_CC_MIN_INTERVAL_S = 180


class VagConnectCoordinator(DataUpdateCoordinator):
    """
    Koordiniert alle Fahrzeugdaten.

    Nutzt CarConnectivitys eigenen Background-Thread + Observer-Pattern.
    HA erhält Push-Updates sobald CC neue Daten hat — kein eigenes Polling.
    """

    def __init__(self, hass: HomeAssistant, entry) -> None:
        self.entry = entry
        self._cc = None
        self._started = False
        self._observer_registered = False
        self.vehicles: dict[str, Any] = {}

        # update_interval=None: HA pollt nicht mehr selbst.
        # Updates kommen reaktiv via _on_cc_update().
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=None,
        )

    # ------------------------------------------------------------------
    # HA lifecycle
    # ------------------------------------------------------------------

    async def async_setup(self) -> bool:
        """
        Startet CarConnectivity + registriert Observer.
        Wird einmal beim Setup der Integration aufgerufen.
        """
        try:
            await self.hass.async_add_executor_job(self._start_cc)
            return True
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("VAG Connect setup failed: %s", err)
            return False

    async def async_shutdown(self) -> None:
        """Stoppt CC sauber beim Unload."""
        await self.hass.async_add_executor_job(self._stop_cc)

    # ------------------------------------------------------------------
    # CarConnectivity init + observer registration
    # ------------------------------------------------------------------

    def _start_cc(self) -> None:
        """
        Blocking: Initialisiert CarConnectivity, startet Background-Thread,
        macht einen ersten Fetch und registriert Observer.
        """
        from carconnectivity.carconnectivity import CarConnectivity  # noqa: PLC0415
        from carconnectivity.observable import Observable             # noqa: PLC0415

        brand    = self.entry.data[CONF_BRAND]
        username = self.entry.data[CONF_USERNAME]
        password = self.entry.data[CONF_PASSWORD]
        spin     = self.entry.data.get(CONF_SPIN) or None

        # Intervall: User-Wert in Sekunden, mindestens CC-Minimum
        interval_min = self.entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        interval_s   = max(interval_min * 60, _CC_MIN_INTERVAL_S)

        connector_cfg: dict[str, Any] = {
            "username": username,
            "password": password,
            "interval": interval_s,
        }
        if spin:
            connector_cfg["spin"] = spin

        cc = CarConnectivity(config={
            "carConnectivity": {
                "connectors": [{"type": brand, "config": connector_cfg}]
            }
        })

        # Erster Fetch (blocking, im Executor)
        cc.startup()
        cc.fetch_all()
        self._cc = cc
        self._started = True

        # Observer auf Garage registrieren.
        # on_transaction_end=True: feuert einmal nach einem kompletten Update-Batch,
        # nicht für jede einzelne Attributänderung.
        garage = cc.get_garage()
        if garage is not None:
            garage.add_observer(
                self._on_cc_update,
                Observable.ObserverEvent.VALUE_CHANGED,
                on_transaction_end=True,
            )
            self._observer_registered = True
            _LOGGER.debug("VAG Connect: Observer auf Garage registriert")

        # Initiale Daten extrahieren
        self._sync_vehicles()
        _LOGGER.info(
            "VAG Connect gestartet: Brand=%s, Intervall=%ds, %d Fahrzeug(e)",
            brand, interval_s, len(self.vehicles)
        )

    def _stop_cc(self) -> None:
        """Blocking: Fährt CC Background-Thread sauber herunter."""
        try:
            if self._cc and self._started:
                self._cc.shutdown()
                _LOGGER.debug("VAG Connect: CC sauber heruntergefahren")
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("VAG Connect shutdown warning: %s", err)
        finally:
            self._cc = None
            self._started = False
            self._observer_registered = False

    # ------------------------------------------------------------------
    # Observer Callback — Herz des reaktiven Systems
    # ------------------------------------------------------------------

    def _on_cc_update(self, element, flags) -> None:
        """
        Wird von CCs Background-Thread aufgerufen wenn sich Fahrzeugdaten ändern.
        Brückt vom CC-Thread in HAs asyncio-Event-Loop.

        element: Das Observable das sich geändert hat (Garage oder ein Vehicle-Attribut)
        flags:   ObserverEvent-Flags (VALUE_CHANGED etc.)
        """
        if not self._started or self._cc is None:
            return

        _LOGGER.debug("VAG Connect: Observer-Event empfangen (flags=%s)", flags)

        try:
            # Neue Daten aus CC-Objekten extrahieren (blocking, im CC-Thread)
            self._sync_vehicles()

            # HA asyncio-Loop von außen aufrufen
            loop = self.hass.loop
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._async_push_update(),
                    loop,
                )
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("VAG Connect Observer-Callback Fehler: %s", err)

    async def _async_push_update(self) -> None:
        """
        Pusht die bereits extrahierten Fahrzeugdaten sofort zu HA.
        Läuft im HA asyncio-Loop (nicht im CC-Thread).
        """
        self.async_set_updated_data(self.vehicles)
        _LOGGER.debug(
            "VAG Connect: Push-Update zu HA (%d Fahrzeug(e))",
            len(self.vehicles)
        )

    # ------------------------------------------------------------------
    # Daten-Extraktion
    # ------------------------------------------------------------------

    def _sync_vehicles(self) -> None:
        """
        Liest alle aktuellen Daten aus CC-Objekten und speichert sie in self.vehicles.
        Blocking — muss im Executor oder CC-Thread laufen.
        """
        if self._cc is None:
            return
        garage = self._cc.get_garage()
        if garage is None:
            return

        result: dict[str, Any] = {}
        for vin in garage.list_vehicle_vins():
            vehicle = garage.get_vehicle(vin)
            if vehicle is not None:
                result[vin] = self._extract(vehicle)

        self.vehicles = result

    def _extract(self, vehicle) -> dict[str, Any]:  # noqa: PLR0912, PLR0915
        """Extrahiert alle CarConnectivity-Attribute in ein HA-freundliches Dict."""
        from carconnectivity.drive import GenericDrive          # noqa: PLC0415
        from carconnectivity.doors import Doors                  # noqa: PLC0415
        from carconnectivity.windows import Windows              # noqa: PLC0415
        from carconnectivity.charging import Charging            # noqa: PLC0415
        from carconnectivity.climatization import Climatization  # noqa: PLC0415

        def _val(attr):
            try:
                v = attr.value
                return v.name if hasattr(v, "name") else v
            except Exception:  # noqa: BLE001
                return None

        data: dict[str, Any] = {}

        # Identity
        data["vin"]          = _val(vehicle.vin)
        data["nickname"]     = _val(vehicle.name) or _val(vehicle.vin)
        data["model"]        = _val(vehicle.model) or "VAG Vehicle"
        data["manufacturer"] = _val(vehicle.manufacturer) or self.entry.data[CONF_BRAND].title()
        data["model_year"]   = _val(vehicle.model_year)

        # Odometer
        try:
            data["odometer_km"] = _val(vehicle.odometer)
        except Exception:  # noqa: BLE001
            data["odometer_km"] = None

        # Drives
        data["fuel_level"]  = None
        data["battery_soc"] = None
        data["range_km"]    = None
        data["is_electric"] = False

        try:
            electric_types = {GenericDrive.Type.ELECTRIC}
            fuel_types = {
                GenericDrive.Type.FUEL, GenericDrive.Type.GASOLINE,
                GenericDrive.Type.PETROL, GenericDrive.Type.DIESEL,
                GenericDrive.Type.CNG, GenericDrive.Type.LPG,
            }
            total = _val(vehicle.drives.total_range)
            if total is not None:
                data["range_km"] = total

            for drive in vehicle.drives.drives.values():
                dtype = drive.type.value
                level = _val(drive.level)
                rng   = _val(drive.range)
                if dtype in electric_types:
                    data["is_electric"] = True
                    data["battery_soc"] = level
                    if data["range_km"] is None:
                        data["range_km"] = rng
                elif dtype in fuel_types:
                    data["fuel_level"] = level
                    if data["range_km"] is None:
                        data["range_km"] = rng
                else:
                    data["fuel_level"]  = data["fuel_level"]  or level
                    data["range_km"]    = data["range_km"]    or rng
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("Drive-Daten Fehler: %s", exc)

        # Position
        try:
            data["latitude"]  = _val(vehicle.position.latitude)
            data["longitude"] = _val(vehicle.position.longitude)
        except Exception:  # noqa: BLE001
            data["latitude"] = data["longitude"] = None

        # Doors
        try:
            lock = vehicle.doors.lock_state.value
            data["doors_locked"] = (lock == Doors.LockState.LOCKED) if lock else None
            open_s = vehicle.doors.open_state.value
            data["doors_open"]   = (open_s == Doors.OpenState.OPEN) if open_s else None
        except Exception:  # noqa: BLE001
            data["doors_locked"] = data["doors_open"] = None

        # Windows
        try:
            ws = vehicle.windows.open_state.value
            data["windows_open"] = (ws == Windows.OpenState.OPEN) if ws else None
        except Exception:  # noqa: BLE001
            data["windows_open"] = None

        # Climatisation
        try:
            cs = vehicle.climatization.state.value
            data["climatisation_state"]  = cs.name if cs else None
            data["climatisation_active"] = cs not in (
                Climatization.ClimatizationState.OFF,
                Climatization.ClimatizationState.UNKNOWN,
                None,
            )
            data["target_temperature"] = _val(vehicle.climatization.settings.target_temperature)
        except Exception:  # noqa: BLE001
            data["climatisation_state"]  = None
            data["climatisation_active"] = False
            data["target_temperature"]   = None

        # Charging
        try:
            charge = vehicle.charging.state.value
            data["charging_state"]  = charge.name if charge else None
            data["is_charging"]     = charge in (
                Charging.ChargingState.CHARGING,
                Charging.ChargingState.CONSERVATION,
            )
            plug = vehicle.charging.connector.connection_state.value
            data["plug_connected"]  = plug is not None and plug.name not in ("DISCONNECTED", "UNKNOWN", "INVALID")
            data["plug_state"]      = plug.name if plug else None
            data["target_soc"]      = _val(vehicle.charging.settings.target_level)
        except Exception:  # noqa: BLE001
            data["charging_state"] = None
            data["is_charging"]    = False
            data["plug_connected"] = None
            data["plug_state"]     = None
            data["target_soc"]     = None

        # Maintenance
        try:
            data["service_due_at"] = _val(vehicle.maintenance.inspection_due_at)
            data["service_km"]     = _val(vehicle.maintenance.inspection_due_after)
            data["oil_service_at"] = _val(vehicle.maintenance.oil_service_due_at)
            data["oil_service_km"] = _val(vehicle.maintenance.oil_service_due_after)
        except Exception:  # noqa: BLE001
            data["service_due_at"] = data["service_km"] = None
            data["oil_service_at"] = data["oil_service_km"] = None

        # Outside temperature
        try:
            data["outside_temp"] = _val(vehicle.outside_temperature)
        except Exception:  # noqa: BLE001
            data["outside_temp"] = None

        # Raw object für Actions
        data["_vehicle"] = vehicle
        return data

    # ------------------------------------------------------------------
    # HA DataUpdateCoordinator override
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict[str, Any]:
        """
        Wird nur noch bei manuellem Refresh aufgerufen (Button / Service).
        Normaler Betrieb läuft reaktiv über _on_cc_update().
        """
        if self._cc is None or not self._started:
            return self.vehicles

        def _force_fetch():
            self._cc.fetch_all()
            self._sync_vehicles()
            return self.vehicles

        try:
            result = await self.hass.async_add_executor_job(_force_fetch)
            _LOGGER.debug("VAG Connect: Manueller Refresh abgeschlossen")
            return result
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("VAG Connect: Manueller Refresh fehlgeschlagen: %s", err)
            return self.vehicles

    # ------------------------------------------------------------------
    # Vehicle Actions
    # ------------------------------------------------------------------

    async def async_lock(self, vin: str) -> None:
        await self._run_command(vin, "doors", "lock-unlock", "lock")

    async def async_unlock(self, vin: str) -> None:
        await self._run_command(vin, "doors", "lock-unlock", "unlock")

    async def async_start_climatisation(self, vin: str) -> None:
        await self._run_command(vin, "climatization", "start-stop", "start")

    async def async_stop_climatisation(self, vin: str) -> None:
        await self._run_command(vin, "climatization", "start-stop", "stop")

    async def async_start_charging(self, vin: str) -> None:
        await self._run_command(vin, "charging", "start-stop", "start")

    async def async_stop_charging(self, vin: str) -> None:
        await self._run_command(vin, "charging", "start-stop", "stop")

    async def async_flash_lights(self, vin: str) -> None:
        await self._run_command(vin, "lights", "honk-and-flash", "flash")

    async def async_set_target_soc(self, vin: str, target: int) -> None:
        def _do():
            v = self.vehicles.get(vin, {}).get("_vehicle")
            if v is None:
                raise RuntimeError(f"Fahrzeug {vin} nicht gefunden")
            v.charging.settings.target_level.value = target
        await self.hass.async_add_executor_job(_do)

    async def async_set_climatisation_temperature(self, vin: str, temp_c: float) -> None:
        def _do():
            v = self.vehicles.get(vin, {}).get("_vehicle")
            if v is None:
                raise RuntimeError(f"Fahrzeug {vin} nicht gefunden")
            v.climatization.settings.target_temperature.value = temp_c
        await self.hass.async_add_executor_job(_do)

    async def _run_command(
        self, vin: str, subsystem: str, command_name: str, value: str
    ) -> None:
        """Führt ein CarConnectivity-Command aus und wartet auf Observer-Update."""
        def _do():
            vehicle = self.vehicles.get(vin, {}).get("_vehicle")
            if vehicle is None:
                raise RuntimeError(f"Fahrzeug {vin} nicht gefunden")

            subsystem_map = {
                "doors":         vehicle.doors,
                "charging":      vehicle.charging,
                "climatization": vehicle.climatization,
                "lights":        vehicle.lights,
            }
            sub = subsystem_map.get(subsystem)
            if sub is None:
                raise RuntimeError(f"Unbekanntes Subsystem: {subsystem}")

            cmds = sub.commands
            if not cmds.contains_command(command_name):
                raise RuntimeError(
                    f"Command '{command_name}' nicht verfügbar für {vin} "
                    f"(subsystem={subsystem}). S-PIN gesetzt?"
                )
            cmds.commands[command_name].value = value
            _LOGGER.info("VAG Command: %s / %s / %s -> %s", vin, subsystem, command_name, value)

        await self.hass.async_add_executor_job(_do)
        # Nach einem Command sofort Daten neu holen
        await self._async_update_data()
