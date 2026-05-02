# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Constants for VAG Connect."""

DOMAIN = "vag_connect"

# Config entry keys
CONF_BRAND                    = "brand"
CONF_USERNAME                 = "username"
CONF_PASSWORD                 = "password"
CONF_SPIN                     = "spin"
CONF_SCAN_INTERVAL            = "scan_interval"
CONF_FORCE_ACCESS             = "force_enable_access"
CONF_ENABLE_REVERSE_GEOCODING = "enable_reverse_geocoding"
# v1.12.0 (#63) — Read-only mode. When True, the integration creates
# only status sensors + binary sensors (read-only), no switches/buttons/
# locks/numbers/climate that would send commands. Useful for users who
# want vehicle telemetry but no risk of accidental actuation or
# subscription-counting commands.
CONF_READ_ONLY                = "read_only_mode"
# v1.14.0 (#29 + #51 Facelift) — PPE/PPC Climate body conditional.
# Audi-only option (default False). When True, ``command_start_climate``
# uses the PPE body shape — ``climatisationMode: "comfort"`` mandatory,
# ``targetTemperature*`` MUST BE OMITTED (audi_connect_ha PR #644 + #677).
# Auto-detection from VIN/model/year is unreliable (no public PPE list);
# user-overridable until we have a proper detection mechanism.
CONF_FORCE_PPE_CLIMATE        = "force_ppe_climate"

# Supported brands — must match CariadClientFactory.create() keys
BRANDS = {
    "audi":           "Audi (myAudi)",
    "volkswagen":     "Volkswagen EU (WeConnect ID)",
    "skoda":          "Škoda (MyŠkoda)",
    "seat":           "SEAT",
    "cupra":          "CUPRA",
    "volkswagen_na":  "Volkswagen US/CA",
    "porsche":        "Porsche (My Porsche)",
}

# Polling interval limits
# v1.17.0 — defaults raised after community research (pycupra
# README + WulfgarW/homeassistant-pycupra release notes): the
# MyCupra/MySeat portal has a per-day API call limit of ~1,500 across
# the official mobile app + integrations. Default 5 min = 288 polls/day
# already eats ~20% of the daily budget BEFORE the official app even
# logs in. Pycupra recommends ≥ 600 s (10 min) by default, ≥ 900 s
# (15 min) when push is enabled. Min raised from 3 min → 5 min.
# Existing entries with explicit lower values are not coerced upward
# at upgrade — only the default for fresh installs changes.
DEFAULT_SCAN_INTERVAL = 10   # minutes (was 5 — see v1.17.0 reasoning)
MIN_SCAN_INTERVAL     = 5    # minutes (was 3 — quota protection)
