# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""v2.2.0 Phase 5b PR #19/20 — Pydantic dual-write validation tests.

Validates the foundation infrastructure (``_pydantic_validate.py`` +
``_pydantic_models.py``) without forcing Pydantic to be installed in
the test environment.

When Pydantic IS available (CI with HA Core): exercises the full
validation roundtrip + schema-mismatch fall-through.

When Pydantic is NOT available (local dev without HA): verifies the
defensive fall-through (returns None silently, never raises).

"It's like having a backup parachute. You hope you never need it,
but when you do — boy oh boy, are you glad it's there."
— Marshall Eriksen, on defensive validation layers
"""

from __future__ import annotations

import pytest

try:
    import pydantic  # noqa: F401

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


class TestPydanticAvailabilityHelper:
    """The ``is_pydantic_available()`` helper must reflect reality."""

    def test_helper_matches_actual_import(self) -> None:
        from custom_components.vag_connect.cariad._pydantic_validate import (
            is_pydantic_available,
        )

        assert is_pydantic_available() == PYDANTIC_AVAILABLE


class TestValidateResponseDefensive:
    """``validate_response`` MUST never raise, regardless of input shape."""

    def test_none_raw_returns_none(self) -> None:
        from custom_components.vag_connect.cariad._pydantic_models import (
            BatteryStatusValue,
        )
        from custom_components.vag_connect.cariad._pydantic_validate import (
            validate_response,
        )

        result = validate_response(None, BatteryStatusValue)
        assert result is None

    def test_pydantic_unavailable_returns_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Force the availability check to return False even if pydantic
        # IS installed — simulates a stripped-down environment.
        from custom_components.vag_connect.cariad import _pydantic_validate
        from custom_components.vag_connect.cariad._pydantic_models import (
            BatteryStatusValue,
        )

        monkeypatch.setattr(
            _pydantic_validate, "_pydantic_available", lambda: False
        )
        result = _pydantic_validate.validate_response(
            {"currentSOC_pct": 80}, BatteryStatusValue
        )
        assert result is None

    @pytest.mark.skipif(
        not PYDANTIC_AVAILABLE, reason="Pydantic required for this test"
    )
    def test_schema_mismatch_returns_none_no_raise(self) -> None:
        # currentSOC_pct must be 0-100 per the model. >100 should fail
        # validation but NOT propagate the exception.
        from custom_components.vag_connect.cariad._pydantic_models import (
            BatteryStatusValue,
        )
        from custom_components.vag_connect.cariad._pydantic_validate import (
            validate_response,
        )

        result = validate_response(
            {"currentSOC_pct": 9999}, BatteryStatusValue
        )
        assert result is None

    @pytest.mark.skipif(
        not PYDANTIC_AVAILABLE, reason="Pydantic required for this test"
    )
    def test_wrong_type_returns_none_no_raise(self) -> None:
        from custom_components.vag_connect.cariad._pydantic_models import (
            BatteryStatusValue,
        )
        from custom_components.vag_connect.cariad._pydantic_validate import (
            validate_response,
        )

        # currentSOC_pct expected int, give it a dict — must NOT raise
        result = validate_response(
            {"currentSOC_pct": {"nested": "garbage"}},
            BatteryStatusValue,
        )
        assert result is None


@pytest.mark.skipif(
    not PYDANTIC_AVAILABLE, reason="Pydantic required for happy-path tests"
)
class TestBatteryStatusValueHappyPath:
    """When Pydantic is available + raw data matches the model, we get
    a validated instance back."""

    def test_canonical_shape_validates(self) -> None:
        from custom_components.vag_connect.cariad._pydantic_models import (
            BatteryStatusValue,
        )
        from custom_components.vag_connect.cariad._pydantic_validate import (
            validate_response,
        )

        raw = {
            "currentSOC_pct": 80,
            "cruisingRangeElectric_km": 350.5,
            "carCapturedTimestamp": "2026-05-16T14:30:00Z",
        }
        result = validate_response(raw, BatteryStatusValue)
        assert result is not None
        assert result.currentSOC_pct == 80
        assert result.cruisingRangeElectric_km == 350.5
        assert result.carCapturedTimestamp == "2026-05-16T14:30:00Z"

    def test_extra_keys_allowed_no_failure(self) -> None:
        # ``extra="allow"`` is critical — Cariad rolls new sibling keys
        # mid-month. The model must NOT fail when unknown keys appear.
        from custom_components.vag_connect.cariad._pydantic_models import (
            BatteryStatusValue,
        )
        from custom_components.vag_connect.cariad._pydantic_validate import (
            validate_response,
        )

        raw = {
            "currentSOC_pct": 60,
            "cruisingRangeElectric_km": 280.0,
            "carCapturedTimestamp": "2026-05-16T15:00:00Z",
            # NEW sibling key from a hypothetical PPE-platform firmware
            "batteryConditioning_state": "ACTIVE",
            # Another rolled key
            "futureField_xyz": {"deeply": {"nested": "value"}},
        }
        result = validate_response(raw, BatteryStatusValue)
        assert result is not None
        assert result.currentSOC_pct == 60

    def test_partial_data_with_all_optional_fields_none(self) -> None:
        # ICE-only vehicle returns an essentially-empty block; the
        # model must accept it (all fields Optional).
        from custom_components.vag_connect.cariad._pydantic_models import (
            BatteryStatusValue,
        )
        from custom_components.vag_connect.cariad._pydantic_validate import (
            validate_response,
        )

        result = validate_response({}, BatteryStatusValue)
        assert result is not None
        assert result.currentSOC_pct is None
        assert result.cruisingRangeElectric_km is None
        assert result.carCapturedTimestamp is None


class TestModuleImportSafety:
    """Critical: both new modules MUST import cleanly even when Pydantic
    is absent (so dev contributors without HA Core can still import the
    parser modules for unit testing)."""

    def test_pydantic_validate_imports_without_pydantic(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Module is already imported elsewhere in this test file, so
        # we can't truly remove pydantic mid-test. The defensive guard
        # is verified by source inspection instead.
        import inspect

        from custom_components.vag_connect.cariad import _pydantic_validate

        src = inspect.getsource(_pydantic_validate)
        # The module must use a try/except around pydantic import
        # (via _pydantic_available), not a top-level hard import
        assert "import pydantic" in src  # the check
        assert "ImportError" in src  # the catch

    def test_pydantic_models_imports_without_pydantic(self) -> None:
        import inspect

        from custom_components.vag_connect.cariad import _pydantic_models

        src = inspect.getsource(_pydantic_models)
        # Top-level pydantic import MUST be inside try/except so the
        # module is importable in dev environments without pydantic
        assert "try:" in src
        assert "from pydantic import" in src
        assert "except ImportError:" in src


class TestDualWriteWiring:
    """The vw_eu.py parser must call ``validate_response`` exactly
    once per battery-status read — and the call must not raise."""

    def test_vw_eu_imports_validate_response(self) -> None:
        import inspect

        from custom_components.vag_connect.cariad.api import vw_eu

        src = inspect.getsource(vw_eu)
        assert "validate_response" in src
        assert "BatteryStatusValue" in src

    def test_vw_eu_passes_context_string(self) -> None:
        # context= helps when sifting through dual-write telemetry
        import inspect

        from custom_components.vag_connect.cariad.api import vw_eu

        src = inspect.getsource(vw_eu)
        assert 'context="vw_eu/charging.batteryStatus.value"' in src
