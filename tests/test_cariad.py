"""Tests for the VAG Connect CARIAD API client package."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# ── helpers ────────────────────────────────────────────────────────────────────

def _mock_session(status: int = 200, json_data: dict | None = None, text: str = "") -> MagicMock:
    """Build an aiohttp.ClientSession mock."""
    resp = AsyncMock()
    resp.status = status
    resp.headers = {"Content-Type": "application/json"}
    resp.json = AsyncMock(return_value=json_data or {})
    resp.text = AsyncMock(return_value=text)
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.get = MagicMock(return_value=resp)
    session.post = MagicMock(return_value=resp)
    session.request = MagicMock(return_value=resp)
    return session


# ── models ─────────────────────────────────────────────────────────────────────

class TestModels:
    def test_brand_configs_all_present(self):
        from custom_components.vag_connect.cariad.models import BRANDS
        assert set(BRANDS.keys()) == {"volkswagen", "audi", "skoda", "seat", "cupra"}

    def test_brand_vw_client_id(self):
        from custom_components.vag_connect.cariad.models import BRAND_VW_EU
        assert "a24fba63" in BRAND_VW_EU.client_id
        assert BRAND_VW_EU.api_base == "https://emea.bff.cariad.digital"

    def test_brand_audi_client_id(self):
        from custom_components.vag_connect.cariad.models import BRAND_AUDI
        assert "f4d0934f" in BRAND_AUDI.client_id
        assert BRAND_AUDI.redirect_uri == "myaudi:///"

    def test_brand_skoda_client_id(self):
        from custom_components.vag_connect.cariad.models import BRAND_SKODA
        assert "7f045eee" in BRAND_SKODA.client_id
        assert "skoda-auto.cz" in BRAND_SKODA.api_base

    def test_brand_seat_client_id(self):
        from custom_components.vag_connect.cariad.models import BRAND_SEAT
        assert "99a5b77d" in BRAND_SEAT.client_id

    def test_brand_cupra_client_id(self):
        from custom_components.vag_connect.cariad.models import BRAND_CUPRA
        assert "3c756d46" in BRAND_CUPRA.client_id
        assert BRAND_CUPRA.redirect_uri == "cupra://oauth-callback"

    def test_brand_app_prefix(self):
        from custom_components.vag_connect.cariad.models import BRAND_AUDI, BRAND_SKODA
        assert BRAND_AUDI.app_prefix == "myaudi"
        assert BRAND_SKODA.app_prefix == "myskoda"

    def test_vehicle_data_defaults(self):
        from custom_components.vag_connect.cariad.models import VehicleData
        d = VehicleData(vin="WVGTEST123456")
        assert d.vin == "WVGTEST123456"
        assert d.battery_soc is None
        assert d.is_electric is False
        assert d.doors_individual == {}

    def test_vehicle_data_to_dict(self):
        from custom_components.vag_connect.cariad.models import VehicleData
        d = VehicleData(vin="VIN1", battery_soc=80, is_electric=True)
        result = d.to_dict()
        assert result["vin"] == "VIN1"
        assert result["battery_soc"] == 80
        assert result["is_electric"] is True

    def test_token_set_valid(self):
        from custom_components.vag_connect.cariad.models import TokenSet
        t = TokenSet("access", "refresh", "id")
        assert t.is_valid() is True

    def test_token_set_invalid_empty(self):
        from custom_components.vag_connect.cariad.models import TokenSet
        t = TokenSet("", "refresh", "id")
        assert t.is_valid() is False


# ── exceptions ─────────────────────────────────────────────────────────────────

class TestExceptions:
    def test_terms_error_message(self):
        from custom_components.vag_connect.cariad.exceptions import TermsAndConditionsError
        e = TermsAndConditionsError()
        assert "app" in str(e).lower()

    def test_rate_limit_error(self):
        from custom_components.vag_connect.cariad.exceptions import RateLimitError
        e = RateLimitError()
        assert "15" in str(e)

    def test_vehicle_not_found_carries_vin(self):
        from custom_components.vag_connect.cariad.exceptions import VehicleNotFoundError
        e = VehicleNotFoundError("VIN123")
        assert e.vin == "VIN123"
        assert "VIN123" in str(e)

    def test_vehicle_command_error(self):
        from custom_components.vag_connect.cariad.exceptions import VehicleCommandError
        e = VehicleCommandError("lock", "403 Forbidden")
        assert e.command == "lock"
        assert "403" in str(e)

    def test_api_error(self):
        from custom_components.vag_connect.cariad.exceptions import APIError
        e = APIError(502, "https://example.com/api", "Bad Gateway")
        assert e.status == 502
        assert "502" in str(e)


# ── auth / PKCE ────────────────────────────────────────────────────────────────

class TestIDKAuth:
    def test_pkce_pair_lengths(self):
        from custom_components.vag_connect.cariad.auth.idk import _pkce_pair
        verifier, challenge = _pkce_pair()
        assert len(verifier) >= 40
        assert len(challenge) >= 40
        assert verifier != challenge

    def test_pkce_pairs_unique(self):
        from custom_components.vag_connect.cariad.auth.idk import _pkce_pair
        pairs = [_pkce_pair() for _ in range(10)]
        verifiers = [p[0] for p in pairs]
        assert len(set(verifiers)) == 10

    def test_extract_auth_code_success(self):
        from custom_components.vag_connect.cariad.auth.idk import _extract_auth_code
        location = "myaudi:///login?code=AUTH_CODE_123&state=xyz"
        code = _extract_auth_code(location, "myaudi:///")
        assert code == "AUTH_CODE_123"

    def test_extract_auth_code_wrong_prefix(self):
        from custom_components.vag_connect.cariad.auth.idk import _extract_auth_code
        code = _extract_auth_code("https://example.com?code=X", "myaudi:///")
        assert code is None

    def test_extract_auth_code_weconnect(self):
        from custom_components.vag_connect.cariad.auth.idk import _extract_auth_code
        location = "weconnect://authenticated?code=VW_CODE&state=abc"
        code = _extract_auth_code(location, "weconnect://authenticated")
        assert code == "VW_CODE"

    def test_absolute_url_relative(self):
        from custom_components.vag_connect.cariad.auth.idk import _absolute_url
        result = _absolute_url("https://identity.vwgroup.io/oidc", "/signin-service/v1/login")
        assert result == "https://identity.vwgroup.io/signin-service/v1/login"

    def test_absolute_url_already_absolute(self):
        from custom_components.vag_connect.cariad.auth.idk import _absolute_url
        url = "https://other.example.com/path"
        assert _absolute_url("https://identity.vwgroup.io", url) == url

    def test_csrf_parser_extracts_fields(self):
        from custom_components.vag_connect.cariad.auth.idk import _CSRFParser
        html = '''<form action="/login/authenticate">
            <input type="hidden" name="_csrf" value="TOKEN123">
            <input type="hidden" name="hmac" value="HMAC456">
            <input type="hidden" name="relayState" value="RS789">
        </form>'''
        p = _CSRFParser()
        p.feed(html)
        assert p.fields["_csrf"] == "TOKEN123"
        assert p.fields["hmac"] == "HMAC456"
        assert p.fields["relayState"] == "RS789"
        assert p.form_action == "/login/authenticate"

    def test_idk_auth_get_token_endpoint_fallback(self):
        """Falls back to known endpoint if openid-config is unreachable."""
        import asyncio
        from custom_components.vag_connect.cariad.auth.idk import IDKAuth
        from custom_components.vag_connect.cariad.models import BRAND_VW_EU

        session = MagicMock()
        resp = AsyncMock()
        resp.__aenter__ = AsyncMock(return_value=resp)
        resp.__aexit__ = AsyncMock(return_value=False)
        resp.json = AsyncMock(side_effect=Exception("network error"))
        session.get = MagicMock(return_value=resp)

        auth = IDKAuth(session, BRAND_VW_EU)
        result = asyncio.get_event_loop().run_until_complete(auth._get_token_endpoint())
        assert "identity.vwgroup.io" in result
        assert "token" in result

    def test_idk_auth_raises_on_bad_auth_page(self):
        """Raises AuthenticationError if login page has no CSRF fields."""
        import asyncio
        from custom_components.vag_connect.cariad.auth.idk import IDKAuth
        from custom_components.vag_connect.cariad.exceptions import AuthenticationError
        from custom_components.vag_connect.cariad.models import BRAND_VW_EU

        session = MagicMock()
        resp = AsyncMock()
        resp.__aenter__ = AsyncMock(return_value=resp)
        resp.__aexit__ = AsyncMock(return_value=False)
        resp.status = 200
        resp.text = AsyncMock(return_value="<html>No form here</html>")
        session.get = MagicMock(return_value=resp)

        auth = IDKAuth(session, BRAND_VW_EU)
        with pytest.raises(AuthenticationError):
            asyncio.get_event_loop().run_until_complete(
                auth.authenticate("user@test.de", "pass")
            )

    def test_idk_auth_raises_on_non_200(self):
        import asyncio
        from custom_components.vag_connect.cariad.auth.idk import IDKAuth
        from custom_components.vag_connect.cariad.exceptions import AuthenticationError
        from custom_components.vag_connect.cariad.models import BRAND_AUDI

        session = MagicMock()
        resp = AsyncMock()
        resp.__aenter__ = AsyncMock(return_value=resp)
        resp.__aexit__ = AsyncMock(return_value=False)
        resp.status = 503
        resp.text = AsyncMock(return_value="Service Unavailable")
        session.get = MagicMock(return_value=resp)

        auth = IDKAuth(session, BRAND_AUDI)
        with pytest.raises(AuthenticationError, match="503"):
            asyncio.get_event_loop().run_until_complete(
                auth.authenticate("user@test.de", "pass")
            )


# ── factory ────────────────────────────────────────────────────────────────────

class TestFactory:
    def test_creates_vw_client(self):
        from custom_components.vag_connect.cariad.api.factory import CariadClientFactory
        from custom_components.vag_connect.cariad.api.vw_eu import VWEUClient
        client = CariadClientFactory.create("volkswagen", MagicMock(), "u@t.de", "pw")
        assert isinstance(client, VWEUClient)
        assert client.brand.name == "volkswagen"

    def test_creates_audi_client(self):
        from custom_components.vag_connect.cariad.api.factory import CariadClientFactory
        from custom_components.vag_connect.cariad.api.audi import AudiClient
        client = CariadClientFactory.create("audi", MagicMock(), "u@t.de", "pw")
        assert isinstance(client, AudiClient)
        assert client.brand.name == "audi"

    def test_creates_skoda_client(self):
        from custom_components.vag_connect.cariad.api.factory import CariadClientFactory
        from custom_components.vag_connect.cariad.api.skoda import SkodaClient
        client = CariadClientFactory.create("skoda", MagicMock(), "u@t.de", "pw")
        assert isinstance(client, SkodaClient)

    def test_creates_seat_client(self):
        from custom_components.vag_connect.cariad.api.factory import CariadClientFactory
        from custom_components.vag_connect.cariad.api.seat_cupra import SeatCupraClient
        client = CariadClientFactory.create("seat", MagicMock(), "u@t.de", "pw")
        assert isinstance(client, SeatCupraClient)
        assert client.brand.name == "seat"

    def test_creates_cupra_client(self):
        from custom_components.vag_connect.cariad.api.factory import CariadClientFactory
        from custom_components.vag_connect.cariad.api.seat_cupra import SeatCupraClient
        client = CariadClientFactory.create("cupra", MagicMock(), "u@t.de", "pw")
        assert isinstance(client, SeatCupraClient)
        assert client.brand.name == "cupra"

    def test_unknown_brand_raises(self):
        from custom_components.vag_connect.cariad.api.factory import CariadClientFactory
        with pytest.raises(ValueError, match="Unknown brand"):
            CariadClientFactory.create("bmw", MagicMock(), "u@t.de", "pw")


# ── base client ────────────────────────────────────────────────────────────────

class TestBaseClient:
    def _make_client(self, json_data=None, status=200):
        from custom_components.vag_connect.cariad.api.vw_eu import VWEUClient
        from custom_components.vag_connect.cariad.models import TokenSet
        session = _mock_session(status=status, json_data=json_data or {})
        client = VWEUClient(session, "u@t.de", "pw")
        client._tokens = TokenSet("access123", "refresh123", "id123")
        return client

    def test_val_nested_path(self):
        from custom_components.vag_connect.cariad.api.base import CariadBaseClient
        client = CariadBaseClient.__new__(CariadBaseClient)
        data = {"a": {"b": {"c": 42}}}
        assert client._val(data, "a", "b", "c") == 42

    def test_val_missing_key_returns_default(self):
        from custom_components.vag_connect.cariad.api.base import CariadBaseClient
        client = CariadBaseClient.__new__(CariadBaseClient)
        assert client._val({"a": {}}, "a", "x", default="missing") == "missing"

    def test_val_none_stops_traversal(self):
        from custom_components.vag_connect.cariad.api.base import CariadBaseClient
        client = CariadBaseClient.__new__(CariadBaseClient)
        assert client._val({"a": None}, "a", "b") is None

    def test_access_token_raises_without_auth(self):
        from custom_components.vag_connect.cariad.api.vw_eu import VWEUClient
        from custom_components.vag_connect.cariad.exceptions import AuthenticationError
        client = VWEUClient(MagicMock(), "u@t.de", "pw")
        with pytest.raises(AuthenticationError, match="authenticate"):
            _ = client._access_token

    def test_get_vehicles(self):
        import asyncio
        client = self._make_client(json_data={
            "data": [{"vin": "WVWZZZAUZLW012345"}, {"vin": "WAUZZZ4G5KN012345"}]
        })
        vins = asyncio.get_event_loop().run_until_complete(client.get_vehicles())
        assert vins == ["WVWZZZAUZLW012345", "WAUZZZ4G5KN012345"]

    def test_get_vehicles_empty(self):
        import asyncio
        client = self._make_client(json_data={"data": []})
        vins = asyncio.get_event_loop().run_until_complete(client.get_vehicles())
        assert vins == []

    def test_request_raises_api_error_on_500(self):
        import asyncio
        from custom_components.vag_connect.cariad.exceptions import APIError
        from custom_components.vag_connect.cariad.api.vw_eu import VWEUClient
        from custom_components.vag_connect.cariad.models import TokenSet

        session = _mock_session(status=500, text="Internal Error")
        # Make 401 retry not infinite by returning 500 on all calls
        client = VWEUClient(session, "u@t.de", "pw")
        client._tokens = TokenSet("acc", "ref", "id")

        with pytest.raises(APIError) as exc:
            asyncio.get_event_loop().run_until_complete(
                client._request("GET", "https://example.com/api")
            )
        assert exc.value.status == 500

    def test_request_204_returns_none(self):
        import asyncio
        from custom_components.vag_connect.cariad.api.vw_eu import VWEUClient
        from custom_components.vag_connect.cariad.models import TokenSet

        session = _mock_session(status=204)
        client = VWEUClient(session, "u@t.de", "pw")
        client._tokens = TokenSet("acc", "ref", "id")

        result = asyncio.get_event_loop().run_until_complete(
            client._request("POST", "https://example.com/api")
        )
        assert result is None


# ── VW EU status parsing ───────────────────────────────────────────────────────

class TestVWEUStatusParsing:
    """Test _parse_status with synthetic selectivestatus payloads."""

    def _client(self) -> object:
        from custom_components.vag_connect.cariad.api.vw_eu import VWEUClient
        from custom_components.vag_connect.cariad.models import TokenSet
        client = VWEUClient(MagicMock(), "u@t.de", "pw")
        client._tokens = TokenSet("acc", "ref", "id")
        return client

    def _ev_payload(self) -> dict:
        return {
            "charging": {
                "chargingStatus": {"value": {
                    "chargingState": "READY_FOR_CHARGING",
                    "chargePower_kW": None,
                    "chargeRate_kmph": None,
                }},
                "batteryStatus": {"value": {
                    "currentSOC_pct": 80,
                    "cruisingRangeElectric_km": 350,
                }},
                "plugStatus": {"value": {
                    "plugConnectionState": "CONNECTED",
                    "plugLockState": "LOCKED",
                }},
                "chargingSettings": {"value": {
                    "targetSOC_pct": 80,
                    "maxChargeCurrentAC_A": 16,
                    "autoUnlockPlugWhenChargedAC": "OFF",
                }},
            },
            "measurements": {
                "odometerStatus": {"value": {"odometer": 15000}},
                "fuelLevelStatus": {"value": {"carType": "electric"}},
            },
            "fuelStatus": {
                "rangeStatus": {"value": {
                    "primaryEngine": {"type": "electric", "remainingRange_km": 350},
                    "totalRange_km": 350,
                }},
            },
            "access": {
                "accessStatus": {"value": {
                    "doorLockStatus": "LOCKED",
                    "overallStatus": "SAFE",
                }},
            },
            "climatisation": {
                "climatisationStatus": {"value": {"climatisationState": "OFF"}},
                "climatisationSettings": {"value": {"targetTemperature_C": 21.0}},
                "windowHeatingStatus": {"value": {"windowHeatingStatus": []}},
            },
            "readiness": {
                "readinessStatus": {"value": {
                    "connectionState": {"isOnline": True},
                }},
            },
            "vehicleHealthInspection": {
                "maintenanceStatus": {"value": {
                    "inspectionDue_km": 8000,
                    "oilServiceDue_km": None,
                }},
            },
            "departureTimers": {
                "departureTimersStatus": {"value": {"timers": [
                    {"enabled": True, "departureTime": {"time": "07:30"}},
                    {"enabled": False, "departureTime": None},
                    {"enabled": False, "departureTime": None},
                ]}},
            },
        }

    def test_ev_battery_soc(self):
        client = self._client()
        result = client._parse_status("VIN1", self._ev_payload(), {})
        assert result.battery_soc == 80

    def test_ev_is_electric(self):
        client = self._client()
        result = client._parse_status("VIN1", self._ev_payload(), {})
        assert result.is_electric is True
        assert result.has_battery is True
        assert result.has_combustion is False

    def test_ev_not_charging(self):
        client = self._client()
        result = client._parse_status("VIN1", self._ev_payload(), {})
        assert result.is_charging is False
        assert result.charging_state == "READY_FOR_CHARGING"

    def test_ev_plug_connected(self):
        client = self._client()
        result = client._parse_status("VIN1", self._ev_payload(), {})
        assert result.plug_connected is True
        assert result.plug_state == "CONNECTED"
        assert result.connector_locked is True

    def test_ev_doors_locked(self):
        client = self._client()
        result = client._parse_status("VIN1", self._ev_payload(), {})
        assert result.doors_locked is True
        assert result.doors_open is False

    def test_ev_target_soc(self):
        client = self._client()
        result = client._parse_status("VIN1", self._ev_payload(), {})
        assert result.target_soc == 80
        assert result.max_charge_current == 16.0

    def test_ev_online(self):
        client = self._client()
        result = client._parse_status("VIN1", self._ev_payload(), {})
        assert result.is_online is True

    def test_ev_odometer(self):
        client = self._client()
        result = client._parse_status("VIN1", self._ev_payload(), {})
        assert result.odometer_km == 15000

    def test_ev_range(self):
        client = self._client()
        result = client._parse_status("VIN1", self._ev_payload(), {})
        assert result.range_km == 350

    def test_ev_target_temperature(self):
        client = self._client()
        result = client._parse_status("VIN1", self._ev_payload(), {})
        assert result.target_temperature == 21.0

    def test_ev_departure_timer_1_enabled(self):
        client = self._client()
        result = client._parse_status("VIN1", self._ev_payload(), {})
        assert result.departure_timer_1_enabled is True
        assert result.departure_timer_1_time == "07:30"
        assert result.departure_timer_2_enabled is False

    def test_service_km(self):
        client = self._client()
        result = client._parse_status("VIN1", self._ev_payload(), {})
        assert result.service_km == 8000

    def test_parking_position_from_dict(self):
        client = self._client()
        result = client._parse_status("VIN1", self._ev_payload(), {"lat": 48.137, "lon": 11.576})
        assert result.latitude == 48.137
        assert result.longitude == 11.576

    def test_phev_detection(self):
        client = self._client()
        payload = self._ev_payload()
        payload["fuelStatus"]["rangeStatus"]["value"]["primaryEngine"]["type"] = "electric"
        payload["fuelStatus"]["rangeStatus"]["value"]["secondaryEngine"] = {"type": "gasoline", "remainingRange_km": 400}
        result = client._parse_status("VIN1", payload, {})
        assert result.has_battery is True
        assert result.has_combustion is True
        assert result.is_hybrid is True
        assert result.is_electric is False

    def test_kelvin_to_celsius_conversion(self):
        client = self._client()
        payload = self._ev_payload()
        payload["measurements"]["outsideTemperatureStatus"] = {
            "value": {"outsideTemperature_K": 296.15}  # 23°C
        }
        result = client._parse_status("VIN1", payload, {})
        assert result.outside_temp == pytest.approx(23.0, abs=0.2)

    def test_charging_active_state(self):
        client = self._client()
        payload = self._ev_payload()
        payload["charging"]["chargingStatus"]["value"]["chargingState"] = "CHARGING"
        payload["charging"]["chargingStatus"]["value"]["chargePower_kW"] = 11.0
        result = client._parse_status("VIN1", payload, {})
        assert result.is_charging is True
        assert result.charging_power_kw == 11.0

    def test_doors_open_unsafe(self):
        client = self._client()
        payload = self._ev_payload()
        payload["access"]["accessStatus"]["value"]["overallStatus"] = "UNSAFE"
        payload["access"]["accessStatus"]["value"]["doors"] = [
            {"name": "frontLeft", "status": [{"value": "open"}]},
            {"name": "frontRight", "status": [{"value": "closed"}]},
        ]
        result = client._parse_status("VIN1", payload, {})
        assert result.doors_open is True
        assert result.doors_individual["frontLeft"] is True
        assert result.doors_individual["frontRight"] is False

    def test_empty_payload_no_crash(self):
        client = self._client()
        result = client._parse_status("VIN1", {}, {})
        assert result.vin == "VIN1"
        assert result.battery_soc is None
        assert result.is_online is False


# ── AudiClient ─────────────────────────────────────────────────────────────────

class TestAudiClient:
    def test_brand_is_audi(self):
        from custom_components.vag_connect.cariad.api.audi import AudiClient
        client = AudiClient(MagicMock(), "u@t.de", "pw")
        assert client.brand.name == "audi"

    def test_redirect_uri_is_myaudi(self):
        from custom_components.vag_connect.cariad.api.audi import AudiClient
        client = AudiClient(MagicMock(), "u@t.de", "pw")
        assert client.brand.redirect_uri == "myaudi:///"

    def test_azs_exchange_updates_tokens(self):
        import asyncio
        from custom_components.vag_connect.cariad.api.audi import AudiClient
        from custom_components.vag_connect.cariad.models import TokenSet

        session = _mock_session(status=200, json_data={
            "access_token": "new_access",
            "refresh_token": "new_refresh",
            "id_token": "new_id",
        })
        client = AudiClient(session, "u@t.de", "pw")
        client._tokens = TokenSet("old_access", "old_refresh", "old_id")

        asyncio.get_event_loop().run_until_complete(client._exchange_azs())
        assert client._tokens.access_token == "new_access"

    def test_azs_exchange_raises_on_failure(self):
        import asyncio
        from custom_components.vag_connect.cariad.api.audi import AudiClient
        from custom_components.vag_connect.cariad.exceptions import AuthenticationError
        from custom_components.vag_connect.cariad.models import TokenSet

        session = _mock_session(status=401, text="Unauthorized")
        client = AudiClient(session, "u@t.de", "pw")
        client._tokens = TokenSet("acc", "ref", "id")

        with pytest.raises(AuthenticationError, match="401"):
            asyncio.get_event_loop().run_until_complete(client._exchange_azs())

    def test_mbb_register_stores_xclient_id(self):
        import asyncio
        from custom_components.vag_connect.cariad.api.audi import AudiClient
        from custom_components.vag_connect.cariad.models import TokenSet

        session = _mock_session(status=200, json_data={"client_id": "MBB_CLIENT_XYZ"})
        client = AudiClient(session, "u@t.de", "pw")
        client._tokens = TokenSet("acc", "ref", "id")

        asyncio.get_event_loop().run_until_complete(client._mbb_register_and_auth())
        assert client._xclient_id == "MBB_CLIENT_XYZ"


# ── Škoda client ───────────────────────────────────────────────────────────────

class TestSkodaClient:
    def test_brand_is_skoda(self):
        from custom_components.vag_connect.cariad.api.skoda import SkodaClient
        client = SkodaClient(MagicMock(), "u@t.de", "pw")
        assert client.brand.name == "skoda"

    def test_get_vehicles_parses_garage(self):
        import asyncio
        from custom_components.vag_connect.cariad.api.skoda import SkodaClient
        from custom_components.vag_connect.cariad.models import TokenSet

        session = _mock_session(json_data={"vehicles": [
            {"vin": "TMBJB7NE5M3001234"},
            {"vin": "TMBJB7NE5M3005678"},
        ]})
        client = SkodaClient(session, "u@t.de", "pw")
        client._tokens = TokenSet("acc", "ref", "id")

        vins = asyncio.get_event_loop().run_until_complete(client.get_vehicles())
        assert "TMBJB7NE5M3001234" in vins

    def test_api_base_is_skoda(self):
        from custom_components.vag_connect.cariad.api.skoda import _BASE
        assert "skoda-auto.cz" in _BASE


# ── SEAT/CUPRA client ──────────────────────────────────────────────────────────

class TestSeatCupraClient:
    def test_seat_brand_config(self):
        from custom_components.vag_connect.cariad.api.seat_cupra import SeatCupraClient
        client = SeatCupraClient(MagicMock(), "seat", "u@t.de", "pw")
        assert client.brand.name == "seat"
        assert "99a5b77d" in client.brand.client_id

    def test_cupra_brand_config(self):
        from custom_components.vag_connect.cariad.api.seat_cupra import SeatCupraClient
        client = SeatCupraClient(MagicMock(), "cupra", "u@t.de", "pw")
        assert client.brand.name == "cupra"
        assert "3c756d46" in client.brand.client_id

    def test_api_base_is_ola(self):
        from custom_components.vag_connect.cariad.api.seat_cupra import _BASE
        assert "ola.prod.code.seat" in _BASE
