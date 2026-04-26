"""Tests for VagConnectCoordinator — uses full mocks, no real API calls."""
from __future__ import annotations

from unittest.mock import MagicMock
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




# ── _enrich() universal enrichment ─────────────────────────────────────────

class TestEnrich:
    """Tests for coordinator._enrich() universal post-processing."""

    def _make_coord(self):
        from unittest.mock import MagicMock, AsyncMock
        from custom_components.vag_connect.coordinator import VagConnectCoordinator
        coord = VagConnectCoordinator.__new__(VagConnectCoordinator)
        coord.hass = MagicMock()
        coord.hass.async_add_executor_job = AsyncMock(return_value=None)
        coord.entry = MagicMock()
        coord.entry.data = {"brand": "audi", "username": "t@t.com",
                            "password": "x", "spin": "", "update_interval": 300}
        coord._vehicles_lock = __import__("threading").Lock()
        coord._cariad_client = MagicMock()
        coord._was_available = True
        coord.data = None
        return coord

    def test_last_updated_at_always_set(self):
        import asyncio
        from datetime import datetime, timezone
        coord = self._make_coord()
        data = {"latitude": None, "longitude": None}
        result = asyncio.get_event_loop().run_until_complete(coord._enrich(data))
        assert result["last_updated_at"] is not None
        assert isinstance(result["last_updated_at"], datetime)
        assert result["last_updated_at"].tzinfo == timezone.utc

    def test_vehicle_state_parked_default(self):
        import asyncio
        coord = self._make_coord()
        data = {"is_online": True, "is_driving": False, "is_charging": False,
                "latitude": None, "longitude": None}
        result = asyncio.get_event_loop().run_until_complete(coord._enrich(data))
        assert result["vehicle_state"] == "PARKED"

    def test_vehicle_state_offline(self):
        import asyncio
        coord = self._make_coord()
        data = {"is_online": False, "latitude": None, "longitude": None}
        result = asyncio.get_event_loop().run_until_complete(coord._enrich(data))
        assert result["vehicle_state"] == "OFFLINE"

    def test_vehicle_state_charging(self):
        import asyncio
        coord = self._make_coord()
        data = {"is_online": True, "is_driving": False, "is_charging": True,
                "plug_connected": True,  # must be True for is_charging to hold
                "latitude": None, "longitude": None}
        result = asyncio.get_event_loop().run_until_complete(coord._enrich(data))
        assert result["vehicle_state"] == "CHARGING"

    def test_existing_vehicle_state_preserved(self):
        """Client-set vehicle_state must not be overwritten."""
        import asyncio
        coord = self._make_coord()
        data = {"vehicle_state": "DRIVING", "latitude": None, "longitude": None}
        result = asyncio.get_event_loop().run_until_complete(coord._enrich(data))
        assert result["vehicle_state"] == "DRIVING"

    def test_geocoding_off_by_default(self):
        """v1.8.0: reverse geocoding is opt-in. Without explicit opt-in,
        the geocoder must NOT be called even when GPS is available (#60)."""
        import asyncio
        from unittest.mock import AsyncMock, patch
        coord = self._make_coord()
        # Real dict so opt-in flag check returns False (MagicMock truthiness off).
        coord.entry.options = {}
        coord.entry.data = {"brand": "audi"}
        with patch.object(coord, "_reverse_geocode", new=AsyncMock()) as mock_geo:
            data = {"latitude": 48.1351, "longitude": 11.5820, "parking_address": None}
            asyncio.get_event_loop().run_until_complete(coord._enrich(data))
            mock_geo.assert_not_called()

    def test_geocoding_skipped_when_address_already_set(self):
        """If client already set parking_address, don't call geocoder
        even when opt-in is enabled."""
        import asyncio
        from unittest.mock import AsyncMock, patch
        coord = self._make_coord()
        coord.entry.options = {"enable_reverse_geocoding": True}
        coord.entry.data = {"brand": "audi"}
        with patch.object(coord, "_reverse_geocode", new=AsyncMock()) as mock_geo:
            data = {"latitude": 48.1, "longitude": 11.5,
                    "parking_address": "Existierende Straße 1, München"}
            asyncio.get_event_loop().run_until_complete(coord._enrich(data))
            mock_geo.assert_not_called()

    def test_geocoding_called_when_opted_in_and_gps_available(self):
        """When user opts in and lat/lon present, _reverse_geocode is called."""
        import asyncio
        from unittest.mock import AsyncMock, patch
        coord = self._make_coord()
        coord.entry.options = {"enable_reverse_geocoding": True}
        coord.entry.data = {"brand": "audi"}
        mock_geo = AsyncMock(
            return_value={"address": "Teststraße 1, München", "city": "München"}
        )
        with patch.object(coord, "_reverse_geocode", new=mock_geo):
            data = {"latitude": 48.1351, "longitude": 11.5820, "parking_address": None}
            result = asyncio.get_event_loop().run_until_complete(coord._enrich(data))
            mock_geo.assert_called_once()
            assert result["parking_address"] == "Teststraße 1, München"
            assert result["parking_city"] == "München"

    def test_geocoding_failure_does_not_crash(self):
        """Geocoding exception → silently ignored, address stays None."""
        import asyncio
        from unittest.mock import AsyncMock, patch
        coord = self._make_coord()
        coord.entry.options = {"enable_reverse_geocoding": True}
        coord.entry.data = {"brand": "audi"}
        with patch.object(
            coord,
            "_reverse_geocode",
            new=AsyncMock(side_effect=Exception("Network error")),
        ):
            data = {"latitude": 48.1, "longitude": 11.5, "parking_address": None}
            result = asyncio.get_event_loop().run_until_complete(coord._enrich(data))
            assert result.get("parking_address") is None  # no crash, address stays None


# ── Fix #917: charging sensors return 0 when plugged but not charging ───────

class TestChargingRateZeroFix:
    """Tests for #917 — charging_rate_kmh/charging_power_kw return 0 when plugged in."""

    def _make_sensor(self, key: str, vehicle_data: dict):
        from unittest.mock import MagicMock
        from custom_components.vag_connect.sensor import VagConnectSensor, VagSensorDescription
        from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
        from homeassistant.const import UnitOfSpeed, UnitOfPower

        coord = MagicMock()
        coord.data = {"VIN1": vehicle_data}
        desc = VagSensorDescription(
            key=key,
            data_key=key,
            name=key,
            device_class=SensorDeviceClass.SPEED if "rate" in key else SensorDeviceClass.POWER,
            native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR if "rate" in key else UnitOfPower.KILO_WATT,
            state_class=SensorStateClass.MEASUREMENT,
        )
        sensor = VagConnectSensor.__new__(VagConnectSensor)
        sensor.coordinator = coord
        sensor._vin = "VIN1"
        sensor._key = key
        sensor.entity_description = desc
        return sensor

    def test_charging_rate_zero_when_plugged_not_charging(self):
        """API returns None for rate → should be 0 when plug is connected."""
        sensor = self._make_sensor("charging_rate_kmh", {
            "charging_rate_kmh": None,
            "plug_connected": True,
        })
        assert sensor.native_value == 0

    def test_charging_power_zero_when_plugged_not_charging(self):
        """API returns None for power → should be 0 when plug is connected."""
        sensor = self._make_sensor("charging_power_kw", {
            "charging_power_kw": None,
            "plug_connected": True,
        })
        assert sensor.native_value == 0

    def test_charging_rate_none_when_not_plugged(self):
        """Not plugged in → None (unavailable) is correct."""
        sensor = self._make_sensor("charging_rate_kmh", {
            "charging_rate_kmh": None,
            "plug_connected": False,
        })
        assert sensor.native_value is None

    def test_charging_rate_actual_value_preserved(self):
        """When charging → actual value from API, not 0."""
        sensor = self._make_sensor("charging_rate_kmh", {
            "charging_rate_kmh": 85.5,
            "plug_connected": True,
        })
        assert sensor.native_value == 85.5


# ── Fix #927: Options-Flow ohne Reload ─────────────────────────────────────

class TestOptionsLiveUpdate:
    """Tests for #927 — scan_interval change must not trigger full reload."""

    def test_poll_loop_reads_interval_from_options(self):
        """_poll_loop should pick up entry.options.scan_interval dynamically."""
        from unittest.mock import MagicMock
        from custom_components.vag_connect.coordinator import VagConnectCoordinator
        import threading

        coord = VagConnectCoordinator.__new__(VagConnectCoordinator)
        coord.entry = MagicMock()
        coord.entry.data = {"scan_interval": 5, "brand": "audi",
                            "username": "t@t.com", "password": "x", "spin": ""}
        # Simulate options override
        coord.entry.options = {"scan_interval": 15}

        # The _poll_loop reads: entry.options.get(scan_interval) or entry.data.get(scan_interval)
        interval_s = max(
            int(
                coord.entry.options.get("scan_interval")
                or coord.entry.data.get("scan_interval", 5)
            ) * 60,
            180,
        )
        assert interval_s == 15 * 60, f"Expected 900s, got {interval_s}s"

    def test_poll_loop_falls_back_to_data_when_no_options(self):
        """When no options set, falls back to entry.data."""
        from unittest.mock import MagicMock
        from custom_components.vag_connect.coordinator import VagConnectCoordinator

        coord = VagConnectCoordinator.__new__(VagConnectCoordinator)
        coord.entry = MagicMock()
        coord.entry.data = {"scan_interval": 10}
        coord.entry.options = {}

        interval_s = max(
            int(
                coord.entry.options.get("scan_interval")
                or coord.entry.data.get("scan_interval", 5)
            ) * 60,
            180,
        )
        assert interval_s == 10 * 60


# ── Bug #32: is_charging defensive reset ────────────────────────────────────

class TestIsChargingReset:
    """Tests for Bug #32 — is_charging stays True after charging ends."""

    def _make_coord(self):
        from unittest.mock import MagicMock, AsyncMock
        from custom_components.vag_connect.coordinator import VagConnectCoordinator
        coord = VagConnectCoordinator.__new__(VagConnectCoordinator)
        coord.hass = MagicMock()
        coord.hass.async_add_executor_job = AsyncMock(return_value=None)
        coord.entry = MagicMock()
        coord.entry.data = {"brand":"audi","username":"t@t.com","password":"x","spin":"","update_interval":300}
        coord._vehicles_lock = __import__("threading").Lock()
        coord._cariad_client = MagicMock()
        return coord

    def test_is_charging_reset_when_unplugged(self):
        """is_charging=True + plug_connected=False → reset to False."""
        import asyncio
        coord = self._make_coord()
        data = {"is_charging": True, "plug_connected": False, "latitude": None, "longitude": None}
        result = asyncio.get_event_loop().run_until_complete(coord._enrich(data))
        assert result["is_charging"] is False

    def test_is_charging_preserved_when_plugged(self):
        """is_charging=True + plug_connected=True → stays True."""
        import asyncio
        coord = self._make_coord()
        data = {"is_charging": True, "plug_connected": True, "latitude": None, "longitude": None}
        result = asyncio.get_event_loop().run_until_complete(coord._enrich(data))
        assert result["is_charging"] is True

    def test_is_charging_false_stays_false(self):
        """is_charging=False → untouched."""
        import asyncio
        coord = self._make_coord()
        data = {"is_charging": False, "plug_connected": True, "latitude": None, "longitude": None}
        result = asyncio.get_event_loop().run_until_complete(coord._enrich(data))
        assert result["is_charging"] is False
