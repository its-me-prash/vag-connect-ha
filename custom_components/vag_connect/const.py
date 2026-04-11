"""Constants for VAG Connect."""

DOMAIN = "vag_connect"

# Config entry keys
CONF_BRAND          = "brand"
CONF_USERNAME       = "username"
CONF_PASSWORD       = "password"
CONF_SPIN           = "spin"
CONF_SCAN_INTERVAL  = "scan_interval"
CONF_FORCE_ACCESS   = "force_enable_access"

# Supported brands — must match CarConnectivity connector type strings
BRANDS = {
    "audi":        "Audi (myAudi)",
    "volkswagen":  "Volkswagen EU (WeConnect)",
    "volkswagen_na": "Volkswagen US/CA",
    "skoda":       "Škoda (MySkoda)",
    "seatcupra":   "SEAT / CUPRA",
}

# Polling interval
DEFAULT_SCAN_INTERVAL = 5    # minutes
MIN_SCAN_INTERVAL     = 3    # minutes
