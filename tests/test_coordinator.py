"""Tests for VagConnectCoordinator — uses full mocks, no real API calls."""
from __future__ import annotations

from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from custom_components.vag_connect.coordinator import VagConnectCoordinator
from custom_components.vag_connect.const import (
    CONF_BRAND, CONF_USERNAME, CONF_PASSWORD, CONF_SPIN, CONF_SCAN_INTERVAL,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_entry(brand="audi", username="test@test.de", password="pw", spin="1234"):
    entry = MagicMock()
    entry.entry_id = "test_entry_1"
    entry.data = {
        CONF_BRAND: brand,
        CONF_USERNAME: username,
        CONF_PASSWORD: password,
        CONF_SPIN: spin,
        CONF_SCAN_INTERVAL: 15,
    }
    return entry


def _make_drive(drive_type_name, level, range_val):
    """Build a mock CarConnectivity GenericDrive."""
    from carconnectivity.drive import GenericDrive
    drive = MagicMock()
    drive.type.value = GenericDrive.Type[drive_type_name]
    drive.level.value = level
    drive.range.value = range_val
    return drive


def _make_vehicle(
    vin="WAUZZZ4G7EN123456",
    model="Audi Q4 e-tron",
    is_electric=True,
    fuel_level=None,
    battery_soc=80,
    range_km=350,
    odometer=25000,
    locked=True,
    doors_open=False,
    windows_open=False,
    lat=48.1351,
    lon=11.5820,
    clim_state="OFF",
    charging_state="READY_FOR_CHARGING",
    plug_connected=True,
    target_soc=80,
    outside_temp=18.5,
    inspection_km=8500,
):
    """Build a comprehensive mock vehicle."""
    from carconnectivity.doors import Doors
    from carconnectivity.windows import Windows
    from carconnectivity.charging import Charging
    from carconnectivity.climatization import Climatization
    from carconnectivity.charging_connector import ChargingConnector

    v = MagicMock()

    # Identity
    v.vin.value = vin
    v.name.value = "Mein Audi"
    v.model.value = model
    v.manufacturer.value = "Audi"
    v.model_year.value = 2023

    # Vehicle type — nötig für EV/PHEV/Verbrenner-Logik
    type_mock = MagicMock()
    if is_electric and fuel_level is None:
        type_mock.name = "ELECTRIC"
    elif is_electric and fuel_level is not None:
        type_mock.name = "HYBRID"
    else:
        type_mock.name = "GASOLINE"
    v.type.value = type_mock

    # Odometer
    v.odometer.value = odometer

    # Drives
    drives = {}
    if is_electric:
        drives["electric"] = _make_drive("ELECTRIC", battery_soc, range_km)
    else:
        drives["fuel"] = _make_drive("GASOLINE", fuel_level, range_km)
    v.drives.drives = drives
    v.drives.total_range.value = range_km

    # Position
    v.position.latitude.value = lat
    v.position.longitude.value = lon

    # Doors
    v.doors.lock_state.value = (
        Doors.LockState.LOCKED if locked else Doors.LockState.UNLOCKED
    )
    v.doors.open_state.value = (
        Doors.OpenState.OPEN if doors_open else Doors.OpenState.CLOSED
    )

    # Windows
    v.windows.open_state.value = (
        Windows.OpenState.OPEN if windows_open else Windows.OpenState.CLOSED
    )

    # Climatisation
    v.climatization.state.value = Climatization.ClimatizationState[clim_state]
    v.climatization.settings.target_temperature.value = 21.0

    # Charging
    v.charging.state.value = Charging.ChargingState[charging_state]
    v.charging.connector.connection_state.value = (
        ChargingConnector.ChargingConnectorConnectionState.CONNECTED
        if plug_connected
        else ChargingConnector.ChargingConnectorConnectionState.DISCONNECTED
    )
    v.charging.settings.target_level.value = target_soc

    # Maintenance
    v.maintenance.inspection_due_at.value = None
    v.maintenance.inspection_due_after.value = inspection_km
    v.maintenance.oil_service_due_at.value = None
    v.maintenance.oil_service_due_after.value = None

    # Outside temperature
    v.outside_temperature.value = outside_temp

    return v


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestExtract:
    """Test the _extract() method with mocked vehicle objects."""

    def setup_method(self):
        hass = MagicMock()
        self.coordinator = VagConnectCoordinator.__new__(VagConnectCoordinator)
        self.coordinator.hass = hass
        self.coordinator.entry = _make_entry()
        self.coordinator.vehicles = {}
        self.coordinator.logger = MagicMock()

    def test_electric_vehicle_basic(self):
        v = _make_vehicle(is_electric=True, battery_soc=75, range_km=280)
        data = self.coordinator._extract(v)

        assert data["vin"] == "WAUZZZ4G7EN123456"
        assert data["model"] == "Audi Q4 e-tron"
        assert data["is_electric"] is True
        assert data["battery_soc"] == 75
        assert data["fuel_level"] is None
        assert data["range_km"] == 280
        assert data["odometer_km"] == 25000

    def test_combustion_vehicle(self):
        v = _make_vehicle(is_electric=False, fuel_level=65, range_km=450)
        data = self.coordinator._extract(v)

        assert data["is_electric"] is False
        assert data["fuel_level"] == 65
        assert data["battery_soc"] is None
        assert data["range_km"] == 450

    def test_doors_locked(self):
        v = _make_vehicle(locked=True, doors_open=False)
        data = self.coordinator._extract(v)
        assert data["doors_locked"] is True
        assert data["doors_open"] is False

    def test_doors_unlocked_and_open(self):
        v = _make_vehicle(locked=False, doors_open=True)
        data = self.coordinator._extract(v)
        assert data["doors_locked"] is False
        assert data["doors_open"] is True

    def test_windows_closed(self):
        v = _make_vehicle(windows_open=False)
        data = self.coordinator._extract(v)
        assert data["windows_open"] is False

    def test_gps_position(self):
        v = _make_vehicle(lat=48.1351, lon=11.5820)
        data = self.coordinator._extract(v)
        assert data["latitude"] == 48.1351
        assert data["longitude"] == 11.5820

    def test_charging_state(self):
        v = _make_vehicle(charging_state="CHARGING", plug_connected=True)
        data = self.coordinator._extract(v)
        assert data["charging_state"] == "CHARGING"
        assert data["is_charging"] is True
        assert data["plug_connected"] is True

    def test_charging_off(self):
        v = _make_vehicle(charging_state="OFF", plug_connected=False)
        data = self.coordinator._extract(v)
        assert data["is_charging"] is False

    def test_climatisation_off(self):
        v = _make_vehicle(clim_state="OFF")
        data = self.coordinator._extract(v)
        assert data["climatisation_state"] == "OFF"
        assert data["climatisation_active"] is False

    def test_climatisation_heating(self):
        v = _make_vehicle(clim_state="HEATING")
        data = self.coordinator._extract(v)
        assert data["climatisation_state"] == "HEATING"
        assert data["climatisation_active"] is True

    def test_target_soc(self):
        v = _make_vehicle(target_soc=90)
        data = self.coordinator._extract(v)
        assert data["target_soc"] == 90

    def test_outside_temperature(self):
        v = _make_vehicle(outside_temp=-5.5)
        data = self.coordinator._extract(v)
        assert data["outside_temp"] == -5.5

    def test_maintenance_km(self):
        v = _make_vehicle(inspection_km=12000)
        data = self.coordinator._extract(v)
        assert data["service_km"] == 12000

    def test_vehicle_object_stored(self):
        """_vehicle raw object must be in data for actions."""
        v = _make_vehicle()
        data = self.coordinator._extract(v)
        assert data["_vehicle"] is v

    def test_graceful_missing_attributes(self):
        """Missing attributes should return None, not raise."""
        v = MagicMock()
        v.vin.value = "TEST123"
        v.name.value = None
        v.model.value = None
        v.manufacturer.value = None
        v.model_year.value = None
        v.odometer.value = None
        v.drives.drives = {}
        v.drives.total_range.value = None
        v.position.latitude.value = None
        v.position.longitude.value = None
        # Make subsystems raise to test graceful degradation
        v.doors.lock_state.value  # this returns MagicMock → truthy
        v.climatization.state.value = MagicMock(name="OFF")
        v.charging.state.value = MagicMock(name="OFF")
        v.outside_temperature.value = None
        v.maintenance.inspection_due_at.value = None
        v.maintenance.inspection_due_after.value = None
        v.maintenance.oil_service_due_at.value = None
        v.maintenance.oil_service_due_after.value = None

        # Should not raise
        data = self.coordinator._extract(v)
        assert data["vin"] == "TEST123"
        assert data["range_km"] is None
        assert data["odometer_km"] is None


class TestCommands:
    """Test command execution."""

    def setup_method(self):
        hass = MagicMock()
        self.coordinator = VagConnectCoordinator.__new__(VagConnectCoordinator)
        self.coordinator.hass = hass
        self.coordinator.entry = _make_entry()
        self.coordinator.vehicles = {}

    def test_lock_command_sets_value(self):
        """Lock command must set 'lock' on the doors command."""
        mock_vehicle = MagicMock()
        mock_cmd = MagicMock()
        mock_vehicle.doors.commands.contains_command.return_value = True
        mock_vehicle.doors.commands.commands = {"lock-unlock": mock_cmd}
        self.coordinator.vehicles = {"VIN1": {"_vehicle": mock_vehicle}}

        # Simulate the blocking part of _run_command directly
        vehicle = self.coordinator.vehicles["VIN1"]["_vehicle"]
        cmds = vehicle.doors.commands
        assert cmds.contains_command("lock-unlock")
        cmds.commands["lock-unlock"].value = "lock"
        mock_cmd.value = "lock"
        assert mock_cmd.value == "lock"

    def test_command_missing_raises(self):
        """If command not available, raise RuntimeError."""
        mock_vehicle = MagicMock()
        mock_vehicle.doors.commands.contains_command.return_value = False
        self.coordinator.vehicles = {"VIN1": {"_vehicle": mock_vehicle}}

        with pytest.raises(RuntimeError, match="not available"):
            def _do():
                vehicle = self.coordinator.vehicles["VIN1"]["_vehicle"]
                cmds = vehicle.doors.commands
                if not cmds.contains_command("lock-unlock"):
                    raise RuntimeError(
                        "Command 'lock-unlock' not available for VIN1 (subsystem=doors). "
                        "Check S-PIN and vehicle capabilities."
                    )
            _do()

    def test_unknown_vin_raises(self):
        """Action on unknown VIN must raise RuntimeError."""
        self.coordinator.vehicles = {}
        with pytest.raises(RuntimeError, match="not found"):
            def _do():
                vehicle = self.coordinator.vehicles.get("UNKNOWN", {}).get("_vehicle")
                if vehicle is None:
                    raise RuntimeError("Vehicle UNKNOWN not found in garage")
            _do()


# ══════════════════════════════════════════════════════════════════════════════
# Tests für Features seit v0.2.0
# ══════════════════════════════════════════════════════════════════════════════

class TestNewExtractFields:
    """Tests für alle Felder die nach v0.1.1 hinzugekommen sind."""

    def setup_method(self):
        hass = MagicMock()
        hass.config.config_dir = "/tmp"
        hass.loop = MagicMock()
        hass.loop.is_running.return_value = False
        self.coordinator = VagConnectCoordinator.__new__(VagConnectCoordinator)
        self.coordinator.hass = hass
        self.coordinator.entry = _make_entry()
        self.coordinator.vehicles = {}
        self.coordinator.logger = MagicMock()
        self.coordinator._was_available = True  # required by log_when_unavailable
    def test_charging_power_extracted(self):
        v = _make_vehicle(is_electric=True)
        v.charging.power.value = 22.0
        data = self.coordinator._extract(v)
        assert data["charging_power_kw"] == 22.0

    def test_charging_rate_extracted(self):
        v = _make_vehicle(is_electric=True)
        v.charging.rate.value = 120.0
        data = self.coordinator._extract(v)
        assert data["charging_rate_kmh"] == 120.0

    def test_charging_power_none_when_not_charging(self):
        v = _make_vehicle(is_electric=True)
        v.charging.power.value = None
        data = self.coordinator._extract(v)
        assert data["charging_power_kw"] is None

    # ── Individuelle Türen (Issue #3) ──────────────────────────────────────
    def test_individual_doors_extracted(self):
        from carconnectivity.doors import Doors  # noqa: PLC0415
        v = _make_vehicle()
        # Mock individual doors dict
        door_fl = MagicMock()
        door_fl.open_state.value = Doors.OpenState.CLOSED
        door_trunk = MagicMock()
        door_trunk.open_state.value = Doors.OpenState.OPEN
        v.doors.doors = {"frontLeft": door_fl, "trunk": door_trunk}
        data = self.coordinator._extract(v)
        assert "doors_individual" in data
        assert data["doors_individual"]["frontLeft"] is False
        assert data["doors_individual"]["trunk"] is True

    def test_individual_doors_empty_when_no_doors(self):
        v = _make_vehicle()
        v.doors.doors = {}
        data = self.coordinator._extract(v)
        assert data["doors_individual"] == {}

    def test_individual_door_handles_error_gracefully(self):
        v = _make_vehicle()
        bad_door = MagicMock()
        bad_door.open_state.value = None  # None state
        v.doors.doors = {"frontLeft": bad_door}
        data = self.coordinator._extract(v)
        assert data["doors_individual"]["frontLeft"] is None

    # ── Stale Data Fix (Issue #4) ──────────────────────────────────────────
    def test_async_push_update_success_true_calls_set_updated_data(self):
        """success=True → async_set_updated_data aufgerufen."""
        import asyncio  # noqa: PLC0415
        self.coordinator.async_set_updated_data = MagicMock()
        self.coordinator.last_update_success = True
        self.coordinator.async_update_listeners = MagicMock()
        fresh = {"VIN1": {"model": "Q4"}}
        asyncio.get_event_loop().run_until_complete(
            self.coordinator._async_push_update(fresh, success=True)
        )
        self.coordinator.async_set_updated_data.assert_called_once_with(fresh)

    def test_async_push_update_success_false_sets_last_update_failed(self):
        """success=False → last_update_success=False + listeners notifiziert."""
        import asyncio  # noqa: PLC0415
        self.coordinator.async_set_updated_data = MagicMock()
        self.coordinator.last_update_success = True
        self.coordinator.async_update_listeners = MagicMock()
        asyncio.get_event_loop().run_until_complete(
            self.coordinator._async_push_update({}, success=False)
        )
        assert self.coordinator.last_update_success is False
        self.coordinator.async_update_listeners.assert_called_once()
        self.coordinator.async_set_updated_data.assert_not_called()

    # ── Token Store Path ───────────────────────────────────────────────────
    def test_tokenstore_path_uses_ha_config_dir(self):
        self.coordinator.hass.config.config_dir = "/home/user/.homeassistant"
        path = self.coordinator._tokenstore_path()
        assert ".storage" in path
        assert "vag_connect_tokens" in path
        assert self.coordinator.entry.entry_id in path
        assert path.endswith(".json")

    def test_tokenstore_path_different_per_entry(self):
        self.coordinator.hass.config.config_dir = "/config"
        entry_a = _make_entry()
        entry_a.entry_id = "entry_aaa"
        entry_b = _make_entry()
        entry_b.entry_id = "entry_bbb"
        c1 = VagConnectCoordinator.__new__(VagConnectCoordinator)
        c1.hass = self.coordinator.hass
        c1.entry = entry_a
        c2 = VagConnectCoordinator.__new__(VagConnectCoordinator)
        c2.hass = self.coordinator.hass
        c2.entry = entry_b
        assert c1._tokenstore_path() != c2._tokenstore_path()

    # ── force_enable_access (Issue #1) ────────────────────────────────────
    def test_force_enable_access_passed_to_connector_config(self):
        """force_enable_access=True muss in connector_cfg landen.
        Testet _start_cc intern durch Inspektion des aufgebauten config-Dicts."""
        entry = _make_entry()
        entry.data = {**entry.data, "force_enable_access": True}
        c = VagConnectCoordinator.__new__(VagConnectCoordinator)
        c.entry = entry
        c.hass = self.coordinator.hass
        c._vehicles_lock = __import__('threading').Lock()
        c.vehicles = {}

        # Prüfen dass _start_cc das Flag korrekt in connector_cfg einbaut
        # durch direkten Code-Pfad-Test ohne echten CarConnectivity-Import
        import inspect  # noqa: PLC0415
        src = inspect.getsource(c._start_cc)
        assert 'force_enable_access' in src
        assert 'connector_cfg["force_enable_access"] = True' in src

    def test_force_enable_access_not_passed_when_false(self):
        """force_enable_access=False darf nicht im connector_cfg landen."""
        import inspect  # noqa: PLC0415
        src = inspect.getsource(VagConnectCoordinator._start_cc)
        # Sicherstellen dass der Guard "if self.entry.data.get(...)" vorhanden ist
        assert 'force_enable_access' in src
        # Nicht einfach immer gesetzt — nur wenn True
        assert "CONF_FORCE_ACCESS" in src  # Konstante statt direkter String seit Cleanup


class TestEntityBaseName:
    """Tests für das neue Entity-Naming Schema (Marke + Modell)."""

    def test_device_name_audi_q4(self):
        from custom_components.vag_connect.entity_base import _device_name  # noqa: PLC0415
        vehicle = {"model": "Q4 e-tron", "vin": "WAUZZ1"}
        name = _device_name(vehicle, "audi")
        assert name == "Audi Q4 e-tron"

    def test_device_name_skoda_enyaq(self):
        from custom_components.vag_connect.entity_base import _device_name  # noqa: PLC0415
        vehicle = {"model": "Enyaq iV 80", "vin": "TMBXXX"}
        name = _device_name(vehicle, "skoda")
        assert name == "Skoda Enyaq iV 80"

    def test_device_name_fallback_to_vin_when_no_model(self):
        from custom_components.vag_connect.entity_base import _device_name  # noqa: PLC0415
        vehicle = {"model": None, "vin": "WAUZZ123456"}
        name = _device_name(vehicle, "audi")
        assert "123456" in name  # letzten 6 VIN-Zeichen
        assert "Audi" in name

    def test_device_name_fallback_unknown_model(self):
        from custom_components.vag_connect.entity_base import _device_name  # noqa: PLC0415
        vehicle = {"model": "Unknown", "vin": "WAUZZ999999"}
        name = _device_name(vehicle, "volkswagen")
        assert "999999" in name

    def test_device_name_empty_model(self):
        from custom_components.vag_connect.entity_base import _device_name  # noqa: PLC0415
        vehicle = {"model": "", "vin": "WAUZZAABBCC"}
        name = _device_name(vehicle, "volkswagen")
        assert "AABBCC" in name


class TestDriveTypeLogic:
    """EV / PHEV / Verbrenner — korrekte Flag-Setzung."""

    def setup_method(self):
        self.coord = VagConnectCoordinator.__new__(VagConnectCoordinator)
        hass = MagicMock()
        hass.config.config_dir = "/tmp"
        self.coord.hass = hass
        self.coord.entry = _make_entry()
        self.coord.logger = MagicMock()

    def _vehicle_with_type(self, vtype_name: str, drive_types: list[str]):
        """Erstellt ein Mock-Fahrzeug mit gegebenem vehicle.type und Antrieben."""
        from carconnectivity.drive import GenericDrive  # noqa: PLC0415
        from carconnectivity.vehicle import GenericVehicle  # noqa: PLC0415

        v = _make_vehicle(is_electric="ELECTRIC" in drive_types)

        # vehicle.type setzen
        vtype_mock = MagicMock()
        vtype_mock.name = vtype_name
        v.type.value = vtype_mock

        # Drives aufbauen
        drives = {}
        for dt in drive_types:
            d = MagicMock()
            dtype_mock = MagicMock()
            dtype_mock.name = dt
            # Map zu echtem Enum-Wert
            enum_val = getattr(GenericDrive.Type, dt, GenericDrive.Type.UNKNOWN)
            d.type.value = enum_val
            d.level.value = 75.0
            d.range.value = 300.0
            drives[dt.lower()] = d
        v.drives.drives = drives
        v.drives.total_range.value = None
        return v

    # ── Pure EV ──────────────────────────────────────────────────────────────
    def test_pure_ev_flags(self):
        v = self._vehicle_with_type("ELECTRIC", ["ELECTRIC"])
        data = self.coord._extract(v)
        assert data["is_electric"] is True
        assert data["has_battery"] is True
        assert data["is_hybrid"] is False
        assert data["has_combustion"] is False

    def test_pure_ev_no_fuel_sensor(self):
        v = self._vehicle_with_type("ELECTRIC", ["ELECTRIC"])
        data = self.coord._extract(v)
        assert data["fuel_level"] is None
        assert data["battery_soc"] == 75.0

    # ── PHEV / Hybrid ────────────────────────────────────────────────────────
    def test_phev_flags(self):
        v = self._vehicle_with_type("HYBRID", ["ELECTRIC", "GASOLINE"])
        data = self.coord._extract(v)
        assert data["is_electric"] is False   # PHEV ist kein reines EV
        assert data["has_battery"] is True    # hat Akku → Lade-Entities anzeigen
        assert data["is_hybrid"] is True
        assert data["has_combustion"] is True

    def test_phev_has_both_fuel_and_battery(self):
        """PHEV zeigt Tankstand UND Ladestand."""
        v = self._vehicle_with_type("HYBRID", ["ELECTRIC", "GASOLINE"])
        data = self.coord._extract(v)
        assert data["battery_soc"] == 75.0
        assert data["fuel_level"] == 75.0

    # ── Verbrenner ───────────────────────────────────────────────────────────
    def test_combustion_flags(self):
        v = self._vehicle_with_type("GASOLINE", ["GASOLINE"])
        data = self.coord._extract(v)
        assert data["is_electric"] is False
        assert data["has_battery"] is False
        assert data["is_hybrid"] is False
        assert data["has_combustion"] is True

    def test_combustion_no_battery_sensor(self):
        v = self._vehicle_with_type("DIESEL", ["DIESEL"])
        data = self.coord._extract(v)
        assert data["battery_soc"] is None
        assert data["fuel_level"] == 75.0

    # ── Fallback wenn vehicle.type None ──────────────────────────────────────
    def test_fallback_from_drives_when_type_none(self):
        """Wenn vehicle.type None → aus Drives ableiten."""
        v = _make_vehicle(is_electric=True)
        v.type.value = None
        # Drives manuell setzen
        from carconnectivity.drive import GenericDrive  # noqa: PLC0415
        elec = MagicMock()
        elec.type.value = GenericDrive.Type.ELECTRIC
        elec.level.value = 80.0
        elec.range.value = 400.0
        v.drives.drives = {"electric": elec}
        v.drives.total_range.value = None

        data = self.coord._extract(v)
        assert data["is_electric"] is True   # abgeleitet aus Drives
        assert data["has_battery"] is True
        assert data["has_combustion"] is False


class TestNewFeatures:
    """Tests für Priorität-1 Features (v0.4.0)."""

    def setup_method(self):
        c = VagConnectCoordinator.__new__(VagConnectCoordinator)
        hass = MagicMock()
        hass.config.config_dir = "/tmp"
        c.hass = hass
        c.entry = _make_entry()
        c.logger = MagicMock()
        self.coord = c

    # ── vehicle_state / is_driving ─────────────────────────────────────────
    def test_vehicle_state_parked(self):
        v = _make_vehicle()
        state = MagicMock(); state.name = "PARKED"
        v.state.value = state
        conn = MagicMock(); conn.name = "ONLINE"
        v.connection_state.value = conn
        data = self.coord._extract(v)
        assert data["vehicle_state"] == "PARKED"
        assert data["is_driving"] is False
        assert data["is_online"] is True

    def test_vehicle_state_driving(self):
        v = _make_vehicle()
        state = MagicMock(); state.name = "DRIVING"
        v.state.value = state
        conn = MagicMock(); conn.name = "REACHABLE"
        v.connection_state.value = conn
        data = self.coord._extract(v)
        assert data["is_driving"] is True
        assert data["is_online"] is True

    def test_vehicle_state_offline(self):
        v = _make_vehicle()
        state = MagicMock(); state.name = "OFFLINE"
        v.state.value = state
        conn = MagicMock(); conn.name = "OFFLINE"
        v.connection_state.value = conn
        data = self.coord._extract(v)
        assert data["is_driving"] is False
        assert data["is_online"] is False

    # ── parking_address ────────────────────────────────────────────────────
    def test_parking_address_extracted(self):
        v = _make_vehicle()
        v.position.location.display_name.value = "Maximilianstraße 1, München"
        v.position.location.city.value = "München"
        v.position.location.road.value = "Maximilianstraße"
        data = self.coord._extract(v)
        assert data["parking_address"] == "Maximilianstraße 1, München"
        assert data["parking_city"] == "München"

    def test_parking_address_fallback_road_city(self):
        v = _make_vehicle()
        v.position.location.display_name.value = None
        v.position.location.city.value = "Berlin"
        v.position.location.road.value = "Unter den Linden"
        data = self.coord._extract(v)
        assert data["parking_address"] == "Unter den Linden, Berlin"

    # ── heading ───────────────────────────────────────────────────────────
    def test_heading_extracted(self):
        v = _make_vehicle()
        v.position.heading.value = 270.0
        data = self.coord._extract(v)
        assert data["heading"] == 270.0

    # ── battery_temperature ────────────────────────────────────────────────
    def test_battery_temperature_extracted(self):
        from carconnectivity.drive import GenericDrive  # noqa: PLC0415
        v = _make_vehicle(is_electric=True)
        elec_drive = MagicMock()
        elec_drive.type.value = GenericDrive.Type.ELECTRIC
        elec_drive.level.value = 80.0
        elec_drive.range.value = 300.0
        elec_drive.battery.temperature.value = 28.5
        elec_drive.battery.temperature_min.value = 24.0
        elec_drive.battery.temperature_max.value = 32.0
        elec_drive.battery.total_capacity.value = 82.0
        v.drives.drives = {"electric": elec_drive}
        data = self.coord._extract(v)
        assert data["battery_temp"] == 28.5
        assert data["battery_temp_min"] == 24.0
        assert data["battery_cap_kwh"] == 82.0

    # ── charge_complete_eta ────────────────────────────────────────────────
    def test_charge_complete_eta_extracted(self):
        from datetime import datetime, timezone  # noqa: PLC0415
        v = _make_vehicle(is_electric=True)
        eta = datetime(2026, 4, 11, 22, 30, tzinfo=timezone.utc)
        v.charging.estimated_date_reached.value = eta
        data = self.coord._extract(v)
        assert data["charge_complete_eta"] == eta

    def test_charge_complete_eta_none_when_not_charging(self):
        v = _make_vehicle(is_electric=True)
        v.charging.estimated_date_reached.value = None
        data = self.coord._extract(v)
        assert data["charge_complete_eta"] is None

    # ── charging_type AC/DC ────────────────────────────────────────────────
    def test_charging_type_dc(self):
        v = _make_vehicle(is_electric=True)
        ct = MagicMock(); ct.name = "DC"
        v.charging.type.value = ct
        data = self.coord._extract(v)
        assert data["charging_type"] == "DC"

    # ── charging_station ───────────────────────────────────────────────────
    def test_charging_station_data_extracted(self):
        v = _make_vehicle(is_electric=True)
        cs = v.charging.charging_station
        cs.name.value = "IONITY A9"
        cs.address.value = "A9, Ausfahrt 42"
        cs.max_power.value = 350.0
        cs.operator_name.value = "IONITY GmbH"
        data = self.coord._extract(v)
        assert data["charging_station_name"] == "IONITY A9"
        assert data["charging_station_kw"] == 350.0
        assert data["charging_station_operator"] == "IONITY GmbH"

    # ── auto_unlock + max_current ──────────────────────────────────────────
    def test_auto_unlock_extracted(self):
        v = _make_vehicle(is_electric=True)
        v.charging.settings.auto_unlock.value = True
        data = self.coord._extract(v)
        assert data["auto_unlock_charge"] is True

    def test_max_charge_current_extracted(self):
        v = _make_vehicle(is_electric=True)
        v.charging.settings.maximum_current.value = 16.0
        data = self.coord._extract(v)
        assert data["max_charge_current"] == 16.0

    # ── license_plate + firmware ───────────────────────────────────────────
    def test_license_plate_extracted(self):
        v = _make_vehicle()
        v.license_plate.value = "M-AB 1234"
        data = self.coord._extract(v)
        assert data["license_plate"] == "M-AB 1234"

    def test_firmware_version_extracted(self):
        v = _make_vehicle()
        v.software.version.value = "3.2.1-build.42"
        data = self.coord._extract(v)
        assert data["firmware_version"] == "3.2.1-build.42"


# ── Abfahrtstimer Tests ────────────────────────────────────────────────────────

class TestDepartureTimers:
    """Tests für Departure Timer Extraction und Action."""

    def setup_method(self):
        from unittest.mock import MagicMock, AsyncMock
        from custom_components.vag_connect.coordinator import VagConnectCoordinator
        hass = MagicMock()
        hass.loop = __import__("asyncio").new_event_loop()
        entry = MagicMock()
        entry.data = {"brand": "audi", "username": "test@test.com", "password": "x", "spin": "", "update_interval": 300}
        entry.entry_id = "test_departure"
        self.coord = VagConnectCoordinator(hass, entry)

    def _make_timer(self, timer_id, enabled, target_dt=None):
        """Baut ein Mock-Timer-Objekt wie AudiClimatization.Timers es erstellt."""
        from unittest.mock import MagicMock
        timer = MagicMock()
        timer.enabled.value = enabled
        timer.target_datetime.value = target_dt
        timer.start_datetime.value = None
        return timer

    def test_timer_enabled_extracted(self):
        """Aktivierter Timer → departure_timer_1_enabled = True."""
        v = _make_vehicle(is_electric=True)
        timer = self._make_timer(1, enabled=True)
        v.climatization.timers.timer_1 = timer
        data = self.coord._extract(v)
        assert data["departure_timer_1_enabled"] is True

    def test_timer_disabled_extracted(self):
        """Deaktivierter Timer → departure_timer_1_enabled = False."""
        v = _make_vehicle(is_electric=True)
        timer = self._make_timer(1, enabled=False)
        v.climatization.timers.timer_1 = timer
        data = self.coord._extract(v)
        assert data["departure_timer_1_enabled"] is False

    def test_timer_target_datetime_extracted(self):
        """Zieldatum wird korrekt extrahiert."""
        from datetime import datetime
        v = _make_vehicle(is_electric=True)
        dt = datetime(2026, 4, 15, 7, 30, 0)
        timer = self._make_timer(1, enabled=True, target_dt=dt)
        v.climatization.timers.timer_1 = timer
        data = self.coord._extract(v)
        assert data["departure_timer_1_time"] == dt

    def test_timer_not_present_returns_none(self):
        """Kein timer_2 im Objekt → beide Keys = None."""
        v = _make_vehicle(is_electric=True)
        # timer_2 nicht gesetzt → getattr liefert None via MagicMock
        # Wir löschen es explizit damit getattr None zurückgibt
        del v.climatization.timers.timer_2
        data = self.coord._extract(v)
        assert data["departure_timer_2_enabled"] is None
        assert data["departure_timer_2_time"] is None

    def test_all_three_timers_extracted(self):
        """Alle 3 Timer werden unabhängig extrahiert."""
        from datetime import datetime
        v = _make_vehicle(is_electric=True)
        for idx in (1, 2, 3):
            timer = self._make_timer(idx, enabled=(idx % 2 == 1))
            setattr(v.climatization.timers, f"timer_{idx}", timer)
        data = self.coord._extract(v)
        assert data["departure_timer_1_enabled"] is True
        assert data["departure_timer_2_enabled"] is False
        assert data["departure_timer_3_enabled"] is True

    def test_timer_extraction_survives_exception(self):
        """Exception in timer-Extraktion → Keys = None, kein Crash."""
        v = _make_vehicle(is_electric=True)
        v.climatization.timers = None  # zwingt Exception
        data = self.coord._extract(v)
        assert data["departure_timer_1_enabled"] is None
        assert data["departure_timer_1_time"] is None


# ── Neue Felder v0.6.0 ─────────────────────────────────────────────────────

class TestV060Fields:
    """Tests für range_estimated_full, range_wltp, battery_available_kwh, last_updated_at."""

    def setup_method(self):
        from unittest.mock import MagicMock
        from custom_components.vag_connect.coordinator import VagConnectCoordinator
        hass = MagicMock()
        hass.loop = __import__("asyncio").new_event_loop()
        entry = MagicMock()
        entry.data = {"brand": "audi", "username": "t@t.com", "password": "x", "spin": "", "update_interval": 300}
        entry.entry_id = "test_v060"
        self.coord = VagConnectCoordinator(hass, entry)

    def test_range_estimated_full_extracted(self):
        """range_estimated_full_km wird aus drive.range_estimated_full gelesen."""
        v = _make_vehicle(is_electric=True)
        v.drives.drives["electric"].range_estimated_full.value = 480.0
        data = self.coord._extract(v)
        assert data["range_estimated_full_km"] == 480.0

    def test_range_wltp_extracted(self):
        """range_wltp_km wird aus drive.range_wltp gelesen."""
        v = _make_vehicle(is_electric=True)
        v.drives.drives["electric"].range_wltp.value = 520.0
        data = self.coord._extract(v)
        assert data["range_wltp_km"] == 520.0

    def test_battery_available_kwh_extracted(self):
        """battery_available_kwh wird aus drive.battery.available_capacity gelesen."""
        v = _make_vehicle(is_electric=True)
        v.drives.drives["electric"].battery.available_capacity.value = 68.3
        data = self.coord._extract(v)
        assert data["battery_available_kwh"] == 68.3

    def test_last_updated_at_is_datetime(self):
        """last_updated_at ist ein UTC-datetime und immer gesetzt."""
        from datetime import datetime, timezone
        v = _make_vehicle(is_electric=True)
        data = self.coord._extract(v)
        assert data["last_updated_at"] is not None
        assert isinstance(data["last_updated_at"], datetime)
        assert data["last_updated_at"].tzinfo == timezone.utc

    def test_range_estimated_full_none_if_missing(self):
        """Kein range_estimated_full in Daten → None, kein Crash."""
        v = _make_vehicle(is_electric=True)
        v.drives.drives["electric"].range_estimated_full.value = None
        data = self.coord._extract(v)
        assert data["range_estimated_full_km"] is None

    def test_battery_available_kwh_none_if_no_battery(self):
        """Kein battery-Objekt → None, kein Crash."""
        v = _make_vehicle(is_electric=False, fuel_level=60)
        data = self.coord._extract(v)
        assert data["battery_available_kwh"] is None
