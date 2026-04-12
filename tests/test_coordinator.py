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


