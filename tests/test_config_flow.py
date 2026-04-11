"""Tests for VagConnect config flow — setup, reauth, reconfigure."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.vag_connect.const import (
    CONF_BRAND, CONF_SCAN_INTERVAL, CONF_SPIN, DEFAULT_SCAN_INTERVAL, DOMAIN,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_coordinator():
    """Return a coordinator mock that succeeds setup with one EV."""
    coord = MagicMock()
    coord.async_setup = AsyncMock(return_value=True)
    coord.async_set_updated_data = MagicMock()
    coord.async_shutdown = AsyncMock()
    coord.vehicles = {"WAUZZZ4G7EN123456": {"model": "Q4 e-tron", "vin": "WAUZZZ4G7EN123456"}}
    return coord


# ── Config Flow: async_step_user ──────────────────────────────────────────────

class TestConfigFlowUser:
    """Tests for the initial user setup step."""

    def _get_flow_class(self):
        from custom_components.vag_connect.config_flow import VagConnectConfigFlow
        return VagConnectConfigFlow

    def test_flow_shows_form_when_no_input(self):
        """Step user without input returns a form."""
        import asyncio
        from homeassistant.data_entry_flow import FlowResultType

        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock()
        flow = self._get_flow_class()()
        flow.hass = hass
        flow.context = {}
        flow.handler = DOMAIN
        flow.flow_id = "test"
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        result = asyncio.get_event_loop().run_until_complete(
            flow.async_step_user(None)
        )
        assert result["type"] == "form"
        assert result["step_id"] == "user"

    def test_duplicate_entry_aborts(self):
        """Entering same brand+username twice aborts with already_configured."""
        import asyncio
        from homeassistant.data_entry_flow import FlowResultType

        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock()
        flow = self._get_flow_class()()
        flow.hass = hass
        flow.context = {}
        flow.handler = DOMAIN
        flow.flow_id = "test"
        flow.async_set_unique_id = AsyncMock()
        # Simulate abort
        from homeassistant.exceptions import HomeAssistantError
        flow._abort_if_unique_id_configured = MagicMock(
            side_effect=Exception("already_configured")
        )

        with pytest.raises(Exception, match="already_configured"):
            asyncio.get_event_loop().run_until_complete(
                flow.async_step_user({
                    CONF_BRAND: "audi",
                    "username": "test@test.de",
                    "password": "pw",
                })
            )

    def test_invalid_credentials_shows_error(self):
        """Wrong credentials → form with error base:invalid_credentials."""
        import asyncio

        hass = MagicMock()
        hass.async_add_executor_job = AsyncMock(side_effect=ValueError("invalid_credentials"))
        flow = self._get_flow_class()()
        flow.hass = hass
        flow.context = {}
        flow.handler = DOMAIN
        flow.flow_id = "test"
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        with patch(
            "custom_components.vag_connect.config_flow._validate_credentials",
            side_effect=ValueError("invalid_credentials"),
        ):
            result = asyncio.get_event_loop().run_until_complete(
                flow.async_step_user({
                    CONF_BRAND: "audi",
                    "username": "test@test.de",
                    "password": "wrong",
                    CONF_SPIN: "",
                    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                    "force_enable_access": False,
                })
            )
        assert result["type"] == "form"
        assert result["errors"]["base"] == "invalid_credentials"

    def test_cannot_connect_shows_error(self):
        """Connection failure → cannot_connect error."""
        import asyncio

        hass = MagicMock()
        flow = self._get_flow_class()()
        flow.hass = hass
        flow.context = {}
        flow.handler = DOMAIN
        flow.flow_id = "test"
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        with patch(
            "custom_components.vag_connect.config_flow._validate_credentials",
            side_effect=ValueError("cannot_connect"),
        ):
            result = asyncio.get_event_loop().run_until_complete(
                flow.async_step_user({
                    CONF_BRAND: "volkswagen",
                    "username": "t@t.de",
                    "password": "pw",
                    CONF_SPIN: "",
                    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                    "force_enable_access": False,
                })
            )
        assert result["type"] == "form"
        assert result["errors"]["base"] == "cannot_connect"

    def test_successful_setup_creates_entry(self):
        """Valid credentials → creates config entry with correct data."""
        import asyncio

        hass = MagicMock()
        flow = self._get_flow_class()()
        flow.hass = hass
        flow.context = {}
        flow.handler = DOMAIN
        flow.flow_id = "test"
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        with patch(
            "custom_components.vag_connect.config_flow._validate_credentials",
            return_value=None,
        ):
            with patch.object(flow, "async_create_entry", return_value={"type": "create_entry", "data": {}}) as mock_create:
                asyncio.get_event_loop().run_until_complete(
                    flow.async_step_user({
                        CONF_BRAND: "audi",
                        "username": "user@audi.de",
                        "password": "secret",
                        CONF_SPIN: "1234",
                        CONF_SCAN_INTERVAL: 10,
                        "force_enable_access": False,
                    })
                )
        mock_create.assert_called_once()
        call_data = mock_create.call_args[1]["data"]
        assert call_data[CONF_BRAND] == "audi"
        assert call_data["username"] == "user@audi.de"
        assert call_data[CONF_SCAN_INTERVAL] == 10


# ── Config Flow: error key mapping ────────────────────────────────────────────

class TestErrorMapping:
    """Test _map_error covers all known error codes."""

    def test_known_errors_pass_through(self):
        from custom_components.vag_connect.config_flow import _map_error
        for code in [
            "terms_and_conditions", "marketing_consent", "two_factor_required",
            "too_many_requests", "invalid_credentials", "missing_library",
        ]:
            assert _map_error(code) == code

    def test_unknown_error_maps_to_cannot_connect(self):
        from custom_components.vag_connect.config_flow import _map_error
        assert _map_error("some_random_error") == "cannot_connect"
        assert _map_error("") == "cannot_connect"


# ── Options flow ──────────────────────────────────────────────────────────────

class TestOptionsFlow:
    """Test options flow shows form and saves correctly."""

    def test_options_flow_shows_form(self):
        import asyncio
        from custom_components.vag_connect.config_flow import VagConnectOptionsFlow

        entry = MagicMock()
        entry.data = {CONF_SCAN_INTERVAL: 5, CONF_SPIN: ""}
        flow = VagConnectOptionsFlow(entry)
        result = asyncio.get_event_loop().run_until_complete(
            flow.async_step_init(None)
        )
        assert result["type"] == "form"
        assert result["step_id"] == "init"

    def test_options_flow_saves_on_submit(self):
        import asyncio
        from custom_components.vag_connect.config_flow import VagConnectOptionsFlow

        entry = MagicMock()
        entry.data = {CONF_SCAN_INTERVAL: 5, CONF_SPIN: ""}
        flow = VagConnectOptionsFlow(entry)
        with patch.object(flow, "async_create_entry", return_value={"type": "create_entry"}) as mock_save:
            asyncio.get_event_loop().run_until_complete(
                flow.async_step_init({CONF_SCAN_INTERVAL: 15, CONF_SPIN: "9999"})
            )
        mock_save.assert_called_once_with(title="", data={CONF_SCAN_INTERVAL: 15, CONF_SPIN: "9999"})


# ── Validate credentials ──────────────────────────────────────────────────────

class TestValidateCredentials:
    """Test _validate_credentials error handling."""

    def test_missing_library_raises(self):
        import asyncio
        from custom_components.vag_connect.config_flow import _validate_credentials

        hass = MagicMock()

        def _raise_import(*_):
            raise ImportError("no module")

        with patch("builtins.__import__", side_effect=_raise_import):
            with pytest.raises(ValueError, match="missing_library|cannot_connect"):
                asyncio.get_event_loop().run_until_complete(
                    _validate_credentials(hass, "audi", "u", "p")
                )
