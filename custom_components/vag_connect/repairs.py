# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""
VAG Connect Repair-Flows für Auth-Probleme + Quota-Warnings.

Wenn Login fehlschlägt (2FA, T&C, gesperrter Account) ODER die API-Quota
zur Neige geht, erscheint eine persistente Warnung im HA UI unter
Einstellungen → System → Reparaturen. Der Nutzer kann direkt reagieren
ohne in die Logs schauen zu müssen.

v1.19.4 (Bundle 1):
- Brand-aware deeplinks für T&C-Repair (Skoda → skodaid.vwgroup.io,
  VW EU → vwid.vwgroup.io, Audi → my.audi.com, SEAT/CUPRA → seat-cupra.cloud)
- Quota-Warning Repair-Issue (extension von v1.19.1 quota sensor)
"""

import logging

from homeassistant.core import HomeAssistant
import homeassistant.helpers.issue_registry as ir

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# v1.19.4 Bundle 1 — Brand-aware deeplinks für T&C-Repair-Issue.
# Wenn IDK-Backend "terms-and-conditions" / "terms_of_use" body sendet,
# zeigt das Repair-Issue einen "Learn more" Link direkt zum Account-
# Portal des passenden Brands (statt generisch zum README). Pattern aus
# skodaconnect/myskoda issues.py — saubere brand-spezifische URLs.
_BRAND_TNC_URLS: dict[str, str] = {
    "skoda":          "https://skodaid.vwgroup.io/landing-page",
    "volkswagen":     "https://vwid.vwgroup.io/account",
    "audi":           "https://my.audi.com",
    "seat":           "https://seat-cupra.cloud.vwgroup.com",
    "cupra":          "https://seat-cupra.cloud.vwgroup.com",
    "porsche":        "https://my.porsche.com",
    "volkswagen_na":  "https://www.vw.com/myvw",
}

# Default fallback URL when brand is unknown (e.g. legacy entries).
_DEFAULT_LEARN_URL = "https://github.com/its-me-prash/vag-connect-ha/blob/main/README.md"


def _learn_url_for_reason(brand: str | None, reason: str) -> str:
    """Return the most actionable learn-more URL for a repair reason.

    For T&C / marketing-consent reasons: brand-specific account-portal
    deeplink so user can accept the new terms in one click. For other
    reasons: integration README.
    """
    if reason in ("terms_and_conditions", "marketing_consent") and brand:
        return _BRAND_TNC_URLS.get(brand.lower(), _DEFAULT_LEARN_URL)
    return _DEFAULT_LEARN_URL


def raise_issue_auth_required(
    hass: HomeAssistant, entry_id: str, reason: str, *, brand: str | None = None,
) -> None:
    """
    Erstellt ein HA-Repair-Issue wenn die Authentifizierung fehlschlägt.
    Erscheint unter Einstellungen → System → Reparaturen.
    Surfaces actionable guidance in the HA Repairs dashboard.

    v1.19.4 — accepts optional ``brand`` for brand-aware learn-more
    deeplinks. Backwards-compatible: callers without brand still work.
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
        learn_more_url=_learn_url_for_reason(brand, reason),
    )
    _LOGGER.warning("VAG Connect Repair-Issue erstellt: %s (brand=%s)", reason, brand)


def clear_auth_issues(hass: HomeAssistant, entry_id: str) -> None:
    """Alle Auth-Issues für diesen Entry löschen (nach erfolgreichem Login)."""
    for reason in ["two_factor_required", "terms_and_conditions",
                   "marketing_consent", "too_many_requests",
                   "invalid_credentials", "auth_failed"]:
        ir.async_delete_issue(hass, DOMAIN, f"{entry_id}_{reason}")


def raise_issue_requirements_conflict(hass: HomeAssistant) -> None:
    """Raise a repair issue for configuration problems."""
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


# v1.19.4 Bundle 1 — Quota Warning Repair-Issue.
# Extension von v1.19.1 (X-RateLimit-Remaining sensor): jetzt auch
# proactive UI-Warning wenn der user kurz vor dem täglichen Quota-Cap
# steht. Pycupra-Pattern als persistent_notification (older HA), wir
# nutzen Repair-Issue (more discoverable + auto-clears wenn quota
# sich wieder erholt).

# Threshold-Konstanten — community research (pycupra README) zeigt
# MyCupra/MySeat ~1500/day quota; warning bei 100 ist ~6.7%, critical
# bei 25 ist ~1.7%. User hat dann genug Zeit Polling-Interval zu
# erhöhen via OptionsFlow bevor der Cap erreicht wird.
QUOTA_WARN_THRESHOLD = 100
QUOTA_CRITICAL_THRESHOLD = 25


def raise_issue_quota_low(
    hass: HomeAssistant,
    entry_id: str,
    *,
    remaining: int,
    limit: int | None = None,
    critical: bool = False,
) -> None:
    """v1.19.4 Bundle 1 — Repair-Issue wenn API-Quota zur Neige geht.

    Wird vom Coordinator gerufen wenn ``requests_remaining_today``
    unter ``QUOTA_WARN_THRESHOLD`` (oder ``QUOTA_CRITICAL_THRESHOLD``)
    fällt. Idempotent — wiederholtes Rufen mit gleicher issue_id
    überschreibt nur den state, kein neuer notification spam.

    Args:
        hass: HomeAssistant instance
        entry_id: Config entry ID for per-entry isolation
        remaining: Current X-RateLimit-Remaining value
        limit: Total X-RateLimit-Limit (for percentage display)
        critical: True if remaining < CRITICAL_THRESHOLD (more
            urgent, ERROR severity); False = WARNING.
    """
    severity = ir.IssueSeverity.ERROR if critical else ir.IssueSeverity.WARNING
    translation_key = "quota_critical" if critical else "quota_low"
    placeholders = {"remaining": str(remaining)}
    if limit is not None:
        placeholders["limit"] = str(limit)
        placeholders["pct"] = f"{(remaining / limit * 100):.1f}" if limit else "?"
    ir.async_create_issue(
        hass,
        DOMAIN,
        f"{entry_id}_quota_low",
        is_fixable=False,
        is_persistent=False,
        severity=severity,
        translation_key=translation_key,
        translation_placeholders=placeholders,
        learn_more_url="https://github.com/its-me-prash/vag-connect-ha/blob/main/docs/FAQ.md#api-quota",
    )
    _LOGGER.info(
        "VAG Connect Quota-Warning Repair-Issue erstellt: %d remaining "
        "(critical=%s)",
        remaining, critical,
    )


def clear_quota_issue(hass: HomeAssistant, entry_id: str) -> None:
    """v1.19.4 — Quota-Warning Repair-Issue auflösen wenn remaining
    sich erholt hat (z.B. midnight reset).
    """
    ir.async_delete_issue(hass, DOMAIN, f"{entry_id}_quota_low")
