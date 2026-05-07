# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Tests for v1.23.0 — Audi/VW Cariad FCM push foundation.

Mirrors v1.18.0 (Skoda MQTT) + v1.19.0 (CUPRA/SEAT FCM) test layout —
AudiVWPushManager shares the abstract PushManager base + identical
lifecycle/state-machine semantics.

User-suggested 2026-05-07: "weil ich auf der app push nachrichten
bekomme, könnte man das doch auch auf der integration als feedback
nehmen?" — myAudi App push notifications surface as HA-side feedback
once Phase 2 wires the receive loop.

Foundation phase: class structure, state machine, lifecycle, opt-in
toggle. Live FCM activation requires a community Audi/VW tester for
Cariad Firebase project + sender_id + notification-subscription
endpoint validation.
"""

from __future__ import annotations

import asyncio
import importlib
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_token_provider():
    return AsyncMock(return_value="fake-oauth-token-789")


@pytest.fixture
def mock_callback():
    return AsyncMock()


# ─────────────────────────────────────────────────────────────────────────────
# A) Brand validation
# ─────────────────────────────────────────────────────────────────────────────


class TestBrandValidation:
    def test_audi_or_volkswagen_only(self, mock_callback, mock_token_provider):
        from custom_components.vag_connect.cariad.push.audi_vw_fcm import (
            AudiVWPushManager,
        )
        for brand in ("audi", "volkswagen"):
            m = AudiVWPushManager(
                mock_callback,
                user_id="u",
                access_token_provider=mock_token_provider,
                vins=["V"],
                brand=brand,
            )
            assert m._brand == brand
        for bad in ("skoda", "cupra", "seat", "porsche", "vw_eu", ""):
            with pytest.raises(ValueError, match="brand must be"):
                AudiVWPushManager(
                    mock_callback,
                    user_id="u",
                    access_token_provider=mock_token_provider,
                    vins=["V"],
                    brand=bad,
                )

    def test_initial_state_is_stopped(self, mock_callback, mock_token_provider):
        from custom_components.vag_connect.cariad.push.audi_vw_fcm import (
            AudiVWPushManager,
        )
        from custom_components.vag_connect.cariad.push.base import PushManagerState
        m = AudiVWPushManager(
            mock_callback,
            user_id="u",
            access_token_provider=mock_token_provider,
            vins=["V"],
            brand="audi",
        )
        assert m.state == PushManagerState.STOPPED


# ─────────────────────────────────────────────────────────────────────────────
# B) Lifecycle
# ─────────────────────────────────────────────────────────────────────────────


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_no_vins_stays_stopped(self, mock_callback, mock_token_provider):
        from custom_components.vag_connect.cariad.push.audi_vw_fcm import (
            AudiVWPushManager,
        )
        from custom_components.vag_connect.cariad.push.base import PushManagerState
        m = AudiVWPushManager(
            mock_callback,
            user_id="u",
            access_token_provider=mock_token_provider,
            vins=[],
            brand="audi",
        )
        await m.start()
        assert m.state == PushManagerState.STOPPED

    @pytest.mark.asyncio
    async def test_missing_firebase_messaging_yields_unavailable(
        self, mock_callback, mock_token_provider, monkeypatch,
    ):
        from custom_components.vag_connect.cariad.push.audi_vw_fcm import (
            AudiVWPushManager,
        )
        from custom_components.vag_connect.cariad.push.base import PushManagerState
        original = importlib.import_module
        def fake(name, *a, **k):
            if name == "firebase_messaging":
                raise ImportError("not installed")
            return original(name, *a, **k)
        monkeypatch.setattr(importlib, "import_module", fake)
        m = AudiVWPushManager(
            mock_callback,
            user_id="u",
            access_token_provider=mock_token_provider,
            vins=["V"],
            brand="volkswagen",
        )
        await m.start()
        assert m.state == PushManagerState.UNAVAILABLE

    @pytest.mark.asyncio
    async def test_start_then_stop_cleanup(
        self, mock_callback, mock_token_provider, monkeypatch,
    ):
        from custom_components.vag_connect.cariad.push.audi_vw_fcm import (
            AudiVWPushManager,
        )
        from custom_components.vag_connect.cariad.push.base import PushManagerState
        m = AudiVWPushManager(
            mock_callback,
            user_id="u",
            access_token_provider=mock_token_provider,
            vins=["V"],
            brand="audi",
        )
        monkeypatch.setattr(m, "_lazy_check_dependencies", lambda: None)
        await m.start()
        await asyncio.sleep(0.05)
        assert m.state == PushManagerState.CONNECTED
        await m.stop()
        assert m.state == PushManagerState.STOPPED
        assert m._loop_task is None


# ─────────────────────────────────────────────────────────────────────────────
# C) Backoff
# ─────────────────────────────────────────────────────────────────────────────


class TestBackoff:
    def _new_manager(self, brand="audi"):
        from custom_components.vag_connect.cariad.push.audi_vw_fcm import (
            AudiVWPushManager,
        )
        return AudiVWPushManager(
            AsyncMock(),
            user_id="u",
            access_token_provider=AsyncMock(return_value="t"),
            vins=["V"],
            brand=brand,
        )

    def test_backoff_constants_match_other_managers(self):
        """Same backoff bounds as v1.18.0 Skoda + v1.19.0 CUPRA/SEAT
        for behavioural consistency across all 3 push managers."""
        from custom_components.vag_connect.cariad.push.audi_vw_fcm import (
            _INITIAL_BACKOFF_S, _MAX_BACKOFF_S,
        )
        assert _INITIAL_BACKOFF_S == 5.0
        assert _MAX_BACKOFF_S == 600.0

    def test_advance_grows_backoff(self):
        m = self._new_manager()
        initial = m._backoff_seconds
        m._advance_backoff()
        assert m._backoff_seconds > initial

    def test_advance_capped(self):
        from custom_components.vag_connect.cariad.push.audi_vw_fcm import _MAX_BACKOFF_S
        m = self._new_manager()
        for _ in range(50):
            m._advance_backoff()
        assert m._backoff_seconds <= _MAX_BACKOFF_S * 1.15

    def test_reset_to_initial(self):
        from custom_components.vag_connect.cariad.push.audi_vw_fcm import _INITIAL_BACKOFF_S
        m = self._new_manager()
        m._advance_backoff()
        m._reset_backoff()
        assert m._backoff_seconds == _INITIAL_BACKOFF_S
        assert m._consecutive_fast_retries == 0


# ─────────────────────────────────────────────────────────────────────────────
# D) Const + Config-Flow option exposure
# ─────────────────────────────────────────────────────────────────────────────


class TestConfigFlowOption:
    def test_const_defines_option_key(self):
        from custom_components.vag_connect.const import CONF_ENABLE_PUSH_AUDI_VW
        assert CONF_ENABLE_PUSH_AUDI_VW == "enable_push_audi_vw"

    def test_three_push_toggles_coexist(self):
        """All 3 brand-tracks have independent toggles — Skoda MQTT
        (v1.18), CUPRA/SEAT FCM (v1.19), Audi/VW FCM (v1.23). User
        with mixed fleet can opt-in to any combination."""
        from custom_components.vag_connect import config_flow
        for attr in (
            "CONF_ENABLE_PUSH_MQTT",
            "CONF_ENABLE_PUSH_FCM",
            "CONF_ENABLE_PUSH_AUDI_VW",
        ):
            assert hasattr(config_flow, attr), f"missing {attr}"

    def test_three_distinct_option_names(self):
        from custom_components.vag_connect import config_flow
        keys = {
            config_flow.CONF_ENABLE_PUSH_MQTT,
            config_flow.CONF_ENABLE_PUSH_FCM,
            config_flow.CONF_ENABLE_PUSH_AUDI_VW,
        }
        assert len(keys) == 3


# ─────────────────────────────────────────────────────────────────────────────
# E) Inheritance + module exports
# ─────────────────────────────────────────────────────────────────────────────


class TestInheritance:
    def test_extends_pushmanager_base(self):
        from custom_components.vag_connect.cariad.push.audi_vw_fcm import (
            AudiVWPushManager,
        )
        from custom_components.vag_connect.cariad.push.base import PushManager
        assert issubclass(AudiVWPushManager, PushManager)

    def test_all_three_managers_share_base(self):
        """All 3 brand-track managers inherit from PushManager —
        coordinator can hold any of them via type hint
        ``self._push_manager: PushManager | None``."""
        from custom_components.vag_connect.cariad.push.audi_vw_fcm import (
            AudiVWPushManager,
        )
        from custom_components.vag_connect.cariad.push.cupra_seat_fcm import (
            CupraSeatPushManager,
        )
        from custom_components.vag_connect.cariad.push.skoda_mqtt import (
            SkodaPushManager,
        )
        from custom_components.vag_connect.cariad.push.base import PushManager
        for cls in (AudiVWPushManager, CupraSeatPushManager, SkodaPushManager):
            assert issubclass(cls, PushManager)
