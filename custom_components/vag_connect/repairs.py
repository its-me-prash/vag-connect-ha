# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""
VAG Connect Repair-Flows für Auth-Probleme.

Wenn Login fehlschlägt (2FA, T&C, gesperrter Account) erscheint
eine persistente Warnung im HA UI unter Einstellungen → System → Reparaturen.
Der Nutzer kann direkt reagieren ohne in die Logs schauen zu müssen.
"""

import logging

from homeassistant.core import HomeAssistant
import homeassistant.helpers.issue_registry as ir

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def raise_issue_auth_required(hass: HomeAssistant, entry_id: str, reason: str) -> None:
    """
    Erstellt ein HA-Repair-Issue wenn die Authentifizierung fehlschlägt.
    Erscheint unter Einstellungen → System → Reparaturen.
    Surfaces actionable guidance in the HA Repairs dashboard.
    """
    issue_map = {
        "two_factor_required": (
            ir.IssueSeverity.WARNING,
            "two_factor_required",
        ),
        "terms_and_conditions": (
            ir.IssueSeverity.ERROR,
            "terms_and_conditions",
        ),
        "marketing_consent": (
            ir.IssueSeverity.WARNING,
            "marketing_consent",
        ),
        "too_many_requests": (
            ir.IssueSeverity.WARNING,
            "too_many_requests",
        ),
        "invalid_credentials": (
            ir.IssueSeverity.ERROR,
            "invalid_credentials",
        ),
    }

    severity, translation_key = issue_map.get(
        reason, (ir.IssueSeverity.ERROR, "auth_failed")
    )

    ir.async_create_issue(
        hass,
        DOMAIN,
        f"{entry_id}_{reason}",
        is_fixable=False,
        is_persistent=False,
        severity=severity,
        translation_key=translation_key,
        learn_more_url="https://github.com/its-me-prash/vag-connect-ha/blob/main/README.md",
    )
    _LOGGER.warning("VAG Connect Repair-Issue erstellt: %s", reason)


def clear_auth_issues(hass: HomeAssistant, entry_id: str) -> None:
    """Alle Auth-Issues für diesen Entry löschen (nach erfolgreichem Login)."""
    for reason in ["two_factor_required", "terms_and_conditions",
                   "marketing_consent", "too_many_requests",
                   "invalid_credentials", "auth_failed"]:
        ir.async_delete_issue(hass, DOMAIN, f"{entry_id}_{reason}")


def raise_issue_requirements_conflict(hass: HomeAssistant) -> None:
    """Raise a repair issue when CarConnectivity cannot be installed."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        "requirements_conflict",
        is_fixable=False,
        is_persistent=True,
        severity=ir.IssueSeverity.ERROR,
        translation_key="requirements_conflict",
        learn_more_url="https://github.com/its-me-prash/vag-connect-ha/issues",
    )
