"""
VagConnectCoordinator — reaktiv via CarConnectivity Observer-Pattern.

Datenfluss:
  1. cc.startup()  → CC Background-Thread startet (pollt VAG-API)
  2. Observer      → VALUE_CHANGED auf Garage, on_transaction_end=True
  3. CC-Thread     → aktualisiert Objekte, feuert Observer-Callback
  4. Callback      → _sync_vehicles() + asyncio.run_coroutine_threadsafe
  5. HA-Loop       → async_set_updated_data() → async_update_listeners()
  6. Entities      → async_write_ha_state()

Thread-Safety:
  - self._vehicles_lock  (threading.Lock) schützt self.vehicles
  - self.vehicles wird nur in _sync_vehicles() (CC-Thread) geschrieben
  - self.vehicles wird in _async_push_update() (HA-Loop) gelesen
  - Lock + dict-copy verhindert Race Conditions

Confirmed HA behavior:
  - async_set_updated_data() ruft async_update_listeners() → Entities update sofort
  - update_interval=None → kein eigenes HA-Polling, rein reaktiv
"""
from __future__ import annotations

import asyncio
import logging
import threading
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

# Minimum interval enforced by Audi/VW connector (Sekunden)
_CC_MIN_INTERVAL_S = 180


class VagConnectCoordinator(DataUpdateCoordinator):
    """Koordiniert Fahrzeugdaten via CarConnectivity Observer-Push."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        self.entry = entry
        self._cc = None
        self._started = False
        self._observer_registered = False

        # Thread-safe dict für Fahrzeugdaten
        self.vehicles: dict[str, Any] = {}
        self._vehicles_lock = threading.Lock()

        # update_interval=None: kein eigenes HA-Polling
        # Updates kommen reaktiv via _on_cc_update → async_set_updated_data
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=None,
        )

    # ──────────────────────────────────────────────────────────────────
    # Lifecycle
    # ──────────────────────────────────────────────────────────────────

    async def async_setup(self) -> bool:
        """
        Startet CarConnectivity + erster Fetch + Observer.
        Wird einmal in async_setup_entry aufgerufen.
        Gibt True zurück wenn mindestens ein Fahrzeug gefunden wurde.
        """
        try:
            await self.hass.async_add_executor_job(self._start_cc)
            with self._vehicles_lock:
                found = len(self.vehicles)
            _LOGGER.info("VAG Connect: Setup OK — %d Fahrzeug(e)", found)
            return found > 0
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("VAG Connect Setup fehlgeschlagen: %s", err)
            return False

    async def async_shutdown(self) -> None:
        """Stoppt CC Background-Thread sauber beim Unload."""
        await self.hass.async_add_executor_job(self._stop_cc)

    # ──────────────────────────────────────────────────────────────────
    # CarConnectivity Start/Stop (blocking, im Executor)
    # ──────────────────────────────────────────────────────────────────

    def _start_cc(self) -> None:
        """Blocking: CC initialisieren, Background-Thread starten, Observer registrieren."""
        from carconnectivity.carconnectivity import CarConnectivity  # noqa: PLC0415
        from carconnectivity.observable import Observable             # noqa: PLC0415

        brand    = self.entry.data[CONF_BRAND]
        username = self.entry.data[CONF_USERNAME]
        password = self.entry.data[CONF_PASSWORD]
        spin     = self.entry.data.get(CONF_SPIN) or None

        # Intervall: User-Minuten → Sekunden, mindestens CC-Minimum
        interval_s = max(
            self.entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL) * 60,
            _CC_MIN_INTERVAL_S,
        )

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

        # startup() startet CC Background-Thread (pollt autonom)
        cc.startup()
        # fetch_all() holt sofort erste Daten (blocking)
        cc.fetch_all()
        self._cc = cc
        self._started = True

        # Observer auf Garage registrieren
        # on_transaction_end=True: feuert einmal nach vollständigem Update-Batch,
        # nicht für jede einzelne Attributänderung (effizienter)
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
        self._sync_vehicles_unlocked(cc)
        _LOGGER.info(
            "VAG Connect: Brand=%s, Intervall=%ds, Fahrzeuge=%d",
            brand, interval_s, len(self.vehicles),
        )

    def _stop_cc(self) -> None:
        """Blocking: CC sauber herunterfahren."""
        try:
            if self._cc and self._started:
                self._cc.shutdown()
                _LOGGER.debug("VAG Connect: CC heruntergefahren")
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("VAG Connect shutdown warning: %s", err)
        finally:
            self._cc = None
            self._started = False
            self._observer_registered = False

    # ──────────────────────────────────────────────────────────────────
    # Observer Callback
    # ──────────────────────────────────────────────────────────────────

    def _on_cc_update(self, element, flags) -> None:
        """
        Wird von CCs Background-Thread aufgerufen wenn Daten geändert wurden.
        Brückt vom CC-Thread in HAs asyncio-Event-Loop.
        """
        if not self._started or self._cc is None:
            return

        _LOGGER.debug("VAG Connect: Observer-Event (flags=%s)", flags)

        try:
            # Daten im CC-Thread extrahieren (Lock halten)
            with self._vehicles_lock:
                self._sync_vehicles_unlocked(self._cc)
                fresh_data = dict(self.vehicles)

            # HA asyncio-Loop benachrichtigen
            loop = self.hass.loop
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._async_push_update(fresh_data),
                    loop,
                )
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("VAG Connect Observer-Fehler: %s", err)

    async def _async_push_update(self, data: dict[str, Any]) -> None:
        """
        Pusht frische Fahrzeugdaten zu HA.
        Läuft im HA asyncio-Loop.

        async_set_updated_data() setzt coordinator.data UND ruft
        async_update_listeners() auf → alle Entities schreiben sofort ihren State.
        Funktioniert auch mit update_interval=None (bestätigt in HA-Source).
        """
        self.async_set_updated_data(data)
        _LOGGER.debug("VAG Connect: Push zu HA — %d Fahrzeug(e)", len(data))

    # ──────────────────────────────────────────────────────────────────
    # Daten-Extraktion
    # ──────────────────────────────────────────────────────────────────

    def _sync_vehicles_unlocked(self, cc) -> None:
        """
        Liest CC-Objekte → self.vehicles.
        MUSS unter _vehicles_lock laufen (oder beim Start vor dem Observer).
        """
        garage = cc.get_garage()
        if garage is None:
            return

        result: dict[str, Any] = {}
        for vin in garage.list_vehicle_vins():
            vehicle = garage.get_vehicle(vin)
            if vehicle is not None:
                result[vin] = self._extract(vehicle)

        self.vehicles = result

    def _extract(self, vehicle) -> dict[str, Any]:  # noqa: PLR0912, PLR0915
        """Extrahiert alle CarConnectivity-Attribute in ein HA-Dict."""
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

        # Drives (Verbrenner / Elektro / Hybrid)
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
                    data["range_km"]    = data["range_km"] or rng
                elif dtype in fuel_types:
                    data["fuel_level"] = level
                    data["range_km"]   = data["range_km"] or rng
                else:
                    data["fuel_level"] = data["fuel_level"] or level
                    data["range_km"]   = data["range_km"]   or rng
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("Drive-Daten Fehler (VIN=%s): %s", data.get("vin"), exc)

        # Position
        try:
            data["latitude"]  = _val(vehicle.position.latitude)
            data["longitude"] = _val(vehicle.position.longitude)
        except Exception:  # noqa: BLE001
            data["latitude"] = data["longitude"] = None

        # Türen
        try:
            lock  = vehicle.doors.lock_state.value
            opens = vehicle.doors.open_state.value
            data["doors_locked"] = (lock  == Doors.LockState.LOCKED)  if lock  else None
            data["doors_open"]   = (opens == Doors.OpenState.OPEN)    if opens else None
        except Exception:  # noqa: BLE001
            data["doors_locked"] = data["doors_open"] = None

        # Fenster
        try:
            ws = vehicle.windows.open_state.value
            data["windows_open"] = (ws == Windows.OpenState.OPEN) if ws else None
        except Exception:  # noqa: BLE001
            data["windows_open"] = None

        # Klimatisierung
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

        # Laden
        try:
            charge = vehicle.charging.state.value
            plug   = vehicle.charging.connector.connection_state.value
            data["charging_state"]  = charge.name if charge else None
            data["is_charging"]     = charge in (
                Charging.ChargingState.CHARGING,
                Charging.ChargingState.CONSERVATION,
            )
            data["plug_connected"]  = plug is not None and plug.name not in (
                "DISCONNECTED", "UNKNOWN", "INVALID"
            )
            data["plug_state"]      = plug.name if plug else None
            data["target_soc"]      = _val(vehicle.charging.settings.target_level)
        except Exception:  # noqa: BLE001
            data["charging_state"] = None
            data["is_charging"]    = False
            data["plug_connected"] = None
            data["plug_state"]     = None
            data["target_soc"]     = None

        # Wartung
        try:
            data["service_due_at"] = _val(vehicle.maintenance.inspection_due_at)
            data["service_km"]     = _val(vehicle.maintenance.inspection_due_after)
            data["oil_service_at"] = _val(vehicle.maintenance.oil_service_due_at)
            data["oil_service_km"] = _val(vehicle.maintenance.oil_service_due_after)
        except Exception:  # noqa: BLE001
            data["service_due_at"] = data["service_km"] = None
            data["oil_service_at"] = data["oil_service_km"] = None

        # Außentemperatur
        try:
            data["outside_temp"] = _val(vehicle.outside_temperature)
        except Exception:  # noqa: BLE001
            data["outside_temp"] = None

        # Raw CC-Objekt für Actions (nicht serialisiert, nicht geloggt)
        data["_vehicle"] = vehicle
        return data

    # ──────────────────────────────────────────────────────────────────
    # HA DataUpdateCoordinator
    # ──────────────────────────────────────────────────────────────────

    async def _async_update_data(self) -> dict[str, Any]:
        """
        Wird nur bei manuellem Refresh aufgerufen (Refresh-Button, Service).
        Normale Updates kommen reaktiv via Observer → async_set_updated_data().

        Macht einen echten CC-Fetch und gibt die frischen Daten zurück.
        """
        if self._cc is None or not self._started:
            with self._vehicles_lock:
                return dict(self.vehicles)

        def _force_fetch():
            self._cc.fetch_all()
            with self._vehicles_lock:
                self._sync_vehicles_unlocked(self._cc)
                return dict(self.vehicles)

        try:
            result = await self.hass.async_add_executor_job(_force_fetch)
            _LOGGER.debug("VAG Connect: Manueller Refresh OK")
            return result
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("VAG Connect: Manueller Refresh fehlgeschlagen: %s", err)
            with self._vehicles_lock:
                return dict(self.vehicles)

    # ──────────────────────────────────────────────────────────────────
    # Actions
    # ──────────────────────────────────────────────────────────────────

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
            with self._vehicles_lock:
                v = self.vehicles.get(vin, {}).get("_vehicle")
            if v is None:
                raise RuntimeError(f"Fahrzeug {vin} nicht gefunden")
            v.charging.settings.target_level.value = target
        await self.hass.async_add_executor_job(_do)

    async def async_set_climatisation_temperature(self, vin: str, temp_c: float) -> None:
        def _do():
            with self._vehicles_lock:
                v = self.vehicles.get(vin, {}).get("_vehicle")
            if v is None:
                raise RuntimeError(f"Fahrzeug {vin} nicht gefunden")
            v.climatization.settings.target_temperature.value = temp_c
        await self.hass.async_add_executor_job(_do)

    async def _run_command(
        self, vin: str, subsystem: str, command_name: str, value: str
    ) -> None:
        """Führt ein CarConnectivity-Command aus."""
        def _do():
            with self._vehicles_lock:
                vehicle = self.vehicles.get(vin, {}).get("_vehicle")
            if vehicle is None:
                raise RuntimeError(f"Fahrzeug {vin} nicht gefunden")

            sub_map = {
                "doors":         vehicle.doors,
                "charging":      vehicle.charging,
                "climatization": vehicle.climatization,
                "lights":        vehicle.lights,
            }
            sub = sub_map.get(subsystem)
            if sub is None:
                raise RuntimeError(f"Unbekanntes Subsystem: {subsystem}")

            cmds = sub.commands
            if not cmds.contains_command(command_name):
                raise RuntimeError(
                    f"Command '{command_name}' nicht verfügbar für {vin} "
                    f"(subsystem={subsystem}). S-PIN gesetzt? Fahrzeug-Capabilities prüfen."
                )
            cmds.commands[command_name].value = value
            _LOGGER.info(
                "VAG Command ausgeführt: VIN=%s | %s/%s → %s",
                vin, subsystem, command_name, value,
            )

        await self.hass.async_add_executor_job(_do)
        # Nach Command sofort manuellen Refresh anstossen
        await self.async_request_refresh()
