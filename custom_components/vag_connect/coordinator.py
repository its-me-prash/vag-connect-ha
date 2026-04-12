"""Coordinator for VAG Connect — cloud_push via CarConnectivity observer pattern.

Data flow:
  CC background thread polls VAG API → observer fires on VALUE_CHANGED
  → asyncio.run_coroutine_threadsafe → async_set_updated_data → entities update.

Thread safety:
  _vehicles_lock (threading.Lock) guards self.vehicles.
  CC thread writes; HA event loop reads via a dict copy.
"""

import asyncio
import logging
import threading
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_BRAND,
    CONF_FORCE_ACCESS,
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
    """Coordinates vehicle data via CarConnectivity observer push (cloud_push).

    No HA polling — CC background thread owns all API calls.
    Updates flow: CC thread → Observer → asyncio bridge → async_set_updated_data → Entities.
    """

    def __init__(self, hass: HomeAssistant, entry) -> None:
        """Initialise coordinator."""
        self.entry = entry
        self._cc = None
        self._started = False
        self._observer_registered = False
        self._was_available: bool = True  # tracks availability for log_when_unavailable

        # Thread-safe dict for vehicle data
        self.vehicles: dict[str, Any] = {}
        self._vehicles_lock = threading.Lock()

        # update_interval=None: no HA-level polling
        # Updates arrive reactively via _on_cc_update → async_set_updated_data
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=None,
        )


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
            _LOGGER.info("VAG Connect: setup complete — %d vehicle(s)", found)
            return found > 0
        except Exception as err:  # noqa: BLE001
            err_str = str(err).lower()
            if "terms and conditions" in err_str or "accept" in err_str and "condition" in err_str:
                raise ValueError("terms_and_conditions") from err
            if "too many requests" in err_str or "429" in err_str:
                raise ValueError("too_many_requests") from err
            if "marketing" in err_str or "consent" in err_str:
                raise ValueError("marketing_consent") from err
            if "password" in err_str or "credential" in err_str or "authentication" in err_str:
                raise ValueError("invalid_credentials") from err
            if "two_factor" in err_str or "2fa" in err_str or "otp" in err_str:
                raise ValueError("two_factor_required") from err
            _LOGGER.error("VAG Connect Setup fehlgeschlagen: %s", err)
            return False

    async def async_shutdown(self) -> None:
        """Stop CarConnectivity and release resources."""
        await self.hass.async_add_executor_job(self._stop_cc)

    def _tokenstore_path(self) -> str:
        """Pfad zur Token-Datei im HA-Config-Verzeichnis.
        Tokens persist across HA restarts — no re-authentication needed.
        """
        import os  # noqa: PLC0415
        storage_dir = os.path.join(self.hass.config.config_dir, ".storage")
        os.makedirs(storage_dir, exist_ok=True)
        return os.path.join(
            storage_dir,
            f"vag_connect_tokens_{self.entry.entry_id}.json"
        )


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
        # force_enable_access: workaround for older VW/Audi models missing 'access' capability.
        if self.entry.data.get(CONF_FORCE_ACCESS, False):
            connector_cfg["force_enable_access"] = True
            _LOGGER.info("VAG Connect: force_enable_access aktiviert")

        cc = CarConnectivity(
            config={
                "carConnectivity": {
                    "connectors": [{"type": brand, "config": connector_cfg}]
                }
            },
            # Token-Persistenz: verhindert Re-Auth bei jedem HA-Neustart
            tokenstore_file=self._tokenstore_path(),
        )

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
        """Blocking: shut down CC cleanly."""
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


    def _on_cc_update(self, element, flags) -> None:
        """
        Wird von CCs Background-Thread aufgerufen wenn Daten geändert wurden.
        Brückt vom CC-Thread in HAs asyncio-Event-Loop.
        """
        if not self._started or self._cc is None:
            return

        _LOGGER.debug("VAG Connect: Observer-Event (flags=%s)", flags)

        try:
            with self._vehicles_lock:
                self._sync_vehicles_unlocked(self._cc)
                fresh_data = dict(self.vehicles)

            loop = self.hass.loop
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._async_push_update(fresh_data, success=True),
                    loop,
                )
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("VAG Connect Observer-Fehler: %s", err)
            # Mark all entities unavailable.
            loop = self.hass.loop
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._async_push_update({}, success=False),
                    loop,
                )

    async def _async_push_update(self, data: dict, success: bool = True) -> None:
        """Push vehicle data to HA.

        Implements log_when_unavailable: logs once when going offline,
        once when coming back online — never fills logs with repeated errors.
        Also removes stale devices when vehicles disappear from the account.
        """
        if success:
            if not self._was_available:
                _LOGGER.info(
                    "VAG Connect: Fahrzeug wieder erreichbar (%s)",
                    self.entry.data.get("username", ""),
                )
                self._was_available = True

            # Remove devices for VINs no longer present in the account
            await self._async_remove_stale_devices(set(data.keys()))

            self.async_set_updated_data(data)
            _LOGGER.debug("VAG Connect: Push zu HA — %d Fahrzeug(e)", len(data))
        else:
            if self._was_available:
                _LOGGER.warning(
                    "VAG Connect: Fahrzeug nicht erreichbar — Entities auf unavailable gesetzt (%s)",
                    self.entry.data.get("username", ""),
                )
                self._was_available = False
            self.last_update_success = False
            self.async_update_listeners()

    async def _async_remove_stale_devices(self, current_vins: set) -> None:
        """Remove device registry entries for VINs no longer in the account.

        Implements the stale-devices Gold quality scale rule.
        Only removes devices that were previously seen (in coordinator.data)
        but are no longer returned by the API.
        """
        if not self.data:
            return  # First run — nothing to clean up

        from homeassistant.helpers import device_registry as dr  # noqa: PLC0415
        from .const import DOMAIN as _DOMAIN  # noqa: PLC0415

        device_reg = dr.async_get(self.hass)
        previous_vins = set(self.data.keys()) - {"_meta"}

        for stale_vin in previous_vins - current_vins:
            device_entry = device_reg.async_get_device(
                identifiers={(_DOMAIN, stale_vin)}
            )
            if device_entry is not None:
                _LOGGER.info(
                    "VAG Connect: Fahrzeug %s nicht mehr im Account — Gerät entfernt",
                    stale_vin,
                )
                device_reg.async_remove_device(device_entry.id)


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
        data["model"]        = _val(vehicle.model) or "VAG Vehicle"
        data["manufacturer"] = _val(vehicle.manufacturer) or self.entry.data[CONF_BRAND].title()
        data["model_year"]   = _val(vehicle.model_year)

        # Odometer
        try:
            data["odometer_km"] = _val(vehicle.odometer)
        except Exception:  # noqa: BLE001
            data["odometer_km"] = None

        # Drivetrain type detection (EV / PHEV / combustion).────
        # vehicle.type: ELECTRIC / HYBRID / FUEL / GASOLINE / DIESEL
        # Pure EV:   drives=[ELECTRIC]
        # PHEV:      drives=[ELECTRIC, GASOLINE]  vehicle.type=HYBRID
        # Verbrenner:drives=[GASOLINE/DIESEL]
        data["fuel_level"]    = None
        data["battery_soc"]   = None
        data["range_km"]      = None
        data["is_electric"]   = False  # True nur für reine EVs
        data["has_battery"]   = False  # True für EV + PHEV (hat Akku+Lader)
        data["is_hybrid"]     = False  # True für PHEV
        data["has_combustion"] = False  # True für Verbrenner + PHEV
        try:
            # Fahrzeugtyp direkt aus vehicle.type (zuverlässiger als Drives)
            vtype = vehicle.type.value
            if vtype is not None:
                type_name = vtype.name if hasattr(vtype, 'name') else str(vtype)
                data["is_electric"]   = type_name == "ELECTRIC"
                data["is_hybrid"]     = type_name == "HYBRID"
                data["has_battery"]   = type_name in ("ELECTRIC", "HYBRID")
                data["has_combustion"] = type_name in (
                    "HYBRID", "FUEL", "GASOLINE", "PETROL", "DIESEL", "CNG", "LPG"
                )

            electric_types = {GenericDrive.Type.ELECTRIC}
            fuel_types = {
                GenericDrive.Type.FUEL, GenericDrive.Type.GASOLINE,
                GenericDrive.Type.PETROL, GenericDrive.Type.DIESEL,
                GenericDrive.Type.CNG, GenericDrive.Type.LPG,
            }
            total = _val(vehicle.drives.total_range)
            if total is not None:
                data["range_km"] = total

            data["range_estimated_full_km"] = None
            data["range_wltp_km"]           = None
            data["battery_available_kwh"]   = None

            for drive in vehicle.drives.drives.values():
                dtype = drive.type.value
                level = _val(drive.level)
                rng   = _val(drive.range)
                if dtype in electric_types:
                    data["has_battery"] = True
                    data["battery_soc"] = level
                    data["range_km"]    = data["range_km"] or rng
                    # Extrafelder aus ElectricDrive
                    if data["range_estimated_full_km"] is None:
                        data["range_estimated_full_km"] = _val(drive.range_estimated_full)
                    if data["range_wltp_km"] is None:
                        data["range_wltp_km"] = _val(drive.range_wltp)
                    # Verfügbare Akku-Energie (kWh)
                    try:
                        avail = _val(drive.battery.available_capacity)
                        if avail is not None:
                            data["battery_available_kwh"] = round(avail, 1)
                    except Exception:  # noqa: BLE001
                        pass
                elif dtype in fuel_types:
                    data["has_combustion"] = True
                    data["fuel_level"] = level
                    data["range_km"]   = data["range_km"] or rng
                else:
                    data["fuel_level"] = data["fuel_level"] or level
                    data["range_km"]   = data["range_km"]   or rng

            # Fallback: wenn vehicle.type None — aus Drives ableiten
            if vtype is None:
                data["is_electric"]    = data["has_battery"] and not data["has_combustion"]
                data["is_hybrid"]      = data["has_battery"] and data["has_combustion"]

        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("Drive-Daten Fehler (VIN=%s): %s", data.get("vin"), exc)

        # Position
        try:
            data["latitude"]  = _val(vehicle.position.latitude)
            data["longitude"] = _val(vehicle.position.longitude)
        except Exception:  # noqa: BLE001
            data["latitude"] = data["longitude"] = None

        # Doors — aggregate state and per-door state.
        try:
            lock  = vehicle.doors.lock_state.value
            opens = vehicle.doors.open_state.value
            data["doors_locked"] = (lock  == Doors.LockState.LOCKED) if lock  else None
            data["doors_open"]   = (opens == Doors.OpenState.OPEN)   if opens else None
            # Individuelle Türen: dict keyed by door_id
            individual: dict = {}
            for door_id, door in vehicle.doors.doors.items():
                try:
                    ds = door.open_state.value
                    individual[door_id] = (ds == Doors.OpenState.OPEN) if ds else None
                except Exception:  # noqa: BLE001
                    individual[door_id] = None
            data["doors_individual"] = individual  # z.B. {"frontLeft": False, "trunk": True}
        except Exception:  # noqa: BLE001
            data["doors_locked"] = data["doors_open"] = None
            data["doors_individual"] = {}

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
            data["target_soc"]        = _val(vehicle.charging.settings.target_level)
            data["charging_power_kw"] = _val(vehicle.charging.power)
            data["charging_rate_kmh"] = _val(vehicle.charging.rate)
        except Exception:  # noqa: BLE001
            data["charging_state"]    = None
            data["is_charging"]       = False
            data["charging_power_kw"] = None
            data["charging_rate_kmh"] = None
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

        # Fahrzeugstatus + Verbindung
        try:
            vs = vehicle.state.value
            data["vehicle_state"]     = vs.name if vs and hasattr(vs,"name") else None
            data["is_driving"]        = vs.name in ("DRIVING","IGNITION_ON") if vs and hasattr(vs,"name") else None
            cs = vehicle.connection_state.value
            data["connection_state"]  = cs.name if cs and hasattr(cs,"name") else None
            data["is_online"]         = cs.name in ("ONLINE","REACHABLE") if cs and hasattr(cs,"name") else None
        except Exception:  # noqa: BLE001
            data["vehicle_state"] = data["connection_state"] = None
            data["is_driving"] = data["is_online"] = None

        # Parking address — provided directly by the API, no geocoding required.
        try:
            loc  = vehicle.position.location
            name = _val(loc.display_name)
            city = _val(loc.city)
            road = _val(loc.road)
            data["parking_address"] = name or (f"{road}, {city}" if road and city else city)
            data["parking_city"]    = city
        except Exception:  # noqa: BLE001
            data["parking_address"] = data["parking_city"] = None

        # Fahrtrichtung (0–360°)
        try:
            data["heading"] = _val(vehicle.position.heading)
        except Exception:  # noqa: BLE001
            data["heading"] = None

        # Akkutemperatur (nur bei EVs / PHEVs)
        try:
            bat = None
            for drive in vehicle.drives.drives.values():
                if hasattr(drive, "battery"):
                    bat = drive.battery
                    break
            if bat is not None:
                data["battery_temp"]     = _val(bat.temperature)
                data["battery_temp_min"] = _val(bat.temperature_min)
                data["battery_temp_max"] = _val(bat.temperature_max)
                data["battery_cap_kwh"]  = _val(bat.total_capacity)
            else:
                data["battery_temp"] = data["battery_temp_min"] = None
                data["battery_temp_max"] = data["battery_cap_kwh"] = None
        except Exception:  # noqa: BLE001
            data["battery_temp"] = data["battery_temp_min"] = None
            data["battery_temp_max"] = data["battery_cap_kwh"] = None

        # Ladeende-ETA + Ladetyp AC/DC
        try:
            data["charge_complete_eta"] = _val(vehicle.charging.estimated_date_reached)
            ct = vehicle.charging.type.value
            data["charging_type"]       = ct.name if ct and hasattr(ct,"name") else None
        except Exception:  # noqa: BLE001
            data["charge_complete_eta"] = data["charging_type"] = None

        # Ladesäule (Name, Adresse, Max-kW, Betreiber)
        try:
            cs_obj = vehicle.charging.charging_station
            data["charging_station_name"]    = _val(cs_obj.name)
            data["charging_station_address"] = _val(cs_obj.address)
            data["charging_station_kw"]      = _val(cs_obj.max_power)
            data["charging_station_operator"]= _val(cs_obj.operator_name)
        except Exception:  # noqa: BLE001
            data["charging_station_name"] = data["charging_station_address"] = None
            data["charging_station_kw"]   = data["charging_station_operator"] = None

        # Erweiterte Lade-Einstellungen
        try:
            data["auto_unlock_charge"]   = _val(vehicle.charging.settings.auto_unlock)
            data["max_charge_current"]   = _val(vehicle.charging.settings.maximum_current)
            data["connector_locked"]     = None  # ChargingConnectorLockState
            lock = vehicle.charging.connector.lock_state.value
            if lock is not None:
                data["connector_locked"] = lock.name not in ("UNLOCKED","UNKNOWN","INVALID")
        except Exception:  # noqa: BLE001
            data["auto_unlock_charge"] = data["max_charge_current"] = None
            data["connector_locked"]   = None

        # Kennzeichen + Firmware-Version (nützlich für Gerätekarte)
        try:
            data["license_plate"]    = _val(vehicle.license_plate)
            data["firmware_version"] = _val(vehicle.software.version)
        except Exception:  # noqa: BLE001
            data["license_plate"] = data["firmware_version"] = None

        # Abfahrtstimer (Departure Timers) — Audi: climatization.timers.timer_1/2/3
        for idx in (1, 2, 3):
            key_enabled  = f"departure_timer_{idx}_enabled"
            key_time     = f"departure_timer_{idx}_time"
            try:
                timers_obj = vehicle.climatization.timers
                timer_obj  = getattr(timers_obj, f"timer_{idx}", None)
                if timer_obj is not None:
                    data[key_enabled] = _val(timer_obj.enabled)
                    # target_datetime bevorzugen, Fallback start_datetime
                    dt = _val(getattr(timer_obj, "target_datetime", None))
                    if dt is None:
                        dt = _val(getattr(timer_obj, "start_datetime", None))
                    data[key_time] = dt
                else:
                    data[key_enabled] = data[key_time] = None
            except Exception:  # noqa: BLE001
                data[key_enabled] = data[key_time] = None

        # Zeitstempel: wann hat das Fahrzeug zuletzt Daten gesendet
        from datetime import datetime, timezone  # noqa: PLC0415
        data["last_updated_at"] = datetime.now(tz=timezone.utc)

        # Raw CC-Objekt für Actions (nicht serialisiert, nicht geloggt)
        data["_vehicle"] = vehicle
        return data


    async def _async_update_data(self) -> dict[str, Any]:
        """
        Wird nur bei manuellem Refresh aufgerufen (Refresh-Button, Service).
        Normale Updates kommen reaktiv via Observer → async_set_updated_data().

        Forces a CC fetch and returns fresh vehicle data.
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

    async def async_set_departure_timer(
        self,
        vin: str,
        timer_id: int,
        enabled: bool,
        departure_time: str | None,
    ) -> None:
        """Abfahrtstimer setzen (Audi CARIAD).

        timer_id:       1, 2 oder 3
        enabled:        True/False
        departure_time: "HH:MM" oder ISO-Datetime-String, None = nur enabled toggeln
        """
        def _do():
            with self._vehicles_lock:
                v = self.vehicles.get(vin, {}).get("_vehicle")
            if v is None:
                raise RuntimeError(f"Fahrzeug {vin} nicht gefunden")

            timers_obj = getattr(getattr(v, "climatization", None), "timers", None)
            if timers_obj is None:
                raise RuntimeError(
                    f"Fahrzeug {vin} unterstützt keine Abfahrtstimer "
                    "(climatization.timers nicht verfügbar)"
                )

            timer_attr = f"timer_{timer_id}"
            timer_obj = getattr(timers_obj, timer_attr, None)
            if timer_obj is None:
                raise RuntimeError(
                    f"Timer {timer_id} für {vin} nicht verfügbar "
                    "(noch kein Timer in API-Antwort)"
                )

            # Enable / disable
            if hasattr(timer_obj, "enabled") and timer_obj.enabled is not None:
                timer_obj.enabled.value = enabled

            # Zeit setzen wenn angegeben
            if departure_time is not None:
                from datetime import datetime  # noqa: PLC0415
                # "HH:MM" → datetime mit heutigem Datum; ISO-String direkt parsen
                if len(departure_time) <= 5:
                    now = datetime.now()
                    h, m = map(int, departure_time.split(":"))
                    dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
                else:
                    dt = datetime.fromisoformat(departure_time)

                if hasattr(timer_obj, "target_datetime") and timer_obj.target_datetime is not None:
                    timer_obj.target_datetime._set_value(value=dt, measured=datetime.now())
                elif hasattr(timer_obj, "start_datetime") and timer_obj.start_datetime is not None:
                    timer_obj.start_datetime._set_value(value=dt, measured=datetime.now())

            _LOGGER.info(
                "VAG Abfahrtstimer: VIN=%s | timer=%d | enabled=%s | time=%s",
                vin, timer_id, enabled, departure_time,
            )

        await self.hass.async_add_executor_job(_do)
        await self.async_request_refresh()

    async def _run_command(
        self, vin: str, subsystem: str, command_name: str, value: str
    ) -> None:
        """Führt ein CarConnectivity-Command auf einem beliebigen Subsystem aus."""
        def _do():
            with self._vehicles_lock:
                vehicle = self.vehicles.get(vin, {}).get("_vehicle")
            if vehicle is None:
                raise RuntimeError(f"Fahrzeug {vin} nicht gefunden")

            sub_map = {
                "doors":           vehicle.doors,
                "charging":        vehicle.charging,
                "climatization":   vehicle.climatization,
                "lights":          vehicle.lights,
                "window_heatings": vehicle.window_heatings,
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
                "VAG Command: VIN=%s | %s/%s → %s", vin, subsystem, command_name, value,
            )

        await self.hass.async_add_executor_job(_do)
        await self.async_request_refresh()

    async def async_set_max_charge_current(self, vin: str, ampere: int) -> None:
        """Max Ladestrom setzen."""
        def _do():
            with self._vehicles_lock:
                v = self.vehicles.get(vin, {}).get("_vehicle")
            if v is None:
                raise RuntimeError(f"Fahrzeug {vin} nicht gefunden")
            v.charging.settings.maximum_current.value = ampere
        await self.hass.async_add_executor_job(_do)
        await self.async_request_refresh()

    async def async_start_window_heating(self, vin: str) -> None:
        """Fensterheizung starten."""
        await self._run_command(vin, "window_heatings", "start-stop", "start")

    async def async_stop_window_heating(self, vin: str) -> None:
        """Fensterheizung stoppen."""
        await self._run_command(vin, "window_heatings", "start-stop", "stop")

    async def async_wake_vehicle(self, vin: str) -> None:
        """Fahrzeug aufwecken (wake-sleep Kommando auf Vehicle-Ebene)."""
        def _do():
            with self._vehicles_lock:
                vehicle = self.vehicles.get(vin, {}).get("_vehicle")
            if vehicle is None:
                raise RuntimeError(f"Fahrzeug {vin} nicht gefunden")
            cmds = vehicle.commands
            if not cmds.contains_command("wake-sleep"):
                raise RuntimeError(
                    f"wake-sleep nicht verfügbar für {vin}. "
                    "Vom Connector nicht unterstützt."
                )
            cmds.commands["wake-sleep"].value = "wake"
            _LOGGER.info("VAG Command: %s / wake-sleep → wake", vin)

        await self.hass.async_add_executor_job(_do)
        await self.async_request_refresh()


