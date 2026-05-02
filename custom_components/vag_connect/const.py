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
DEFAULT_SCAN_INTERVAL = 5    # minutes
MIN_SCAN_INTERVAL     = 3    # minutes
