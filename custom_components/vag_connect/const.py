"""Constants for VAG Connect integration."""

DOMAIN = "vag_connect"

# Config flow keys
CONF_BRAND = "brand"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SPIN = "spin"
CONF_REGION = "region"
CONF_SCAN_INTERVAL = "scan_interval"

# Supported brands → maps to CarConnectivity connector type
BRANDS = {
    "audi":          "Audi (myAudi)",
    "volkswagen":    "Volkswagen / VW (WeConnect EU)",
    "volkswagen_na": "Volkswagen / VW (WeConnect US/CA)",
    "skoda":         "Škoda (MySkoda)",
    "seatcupra":     "SEAT / CUPRA (MyCupra)",
}

# Regions
REGIONS = {
    "DE": "Deutschland / Europe",
    "US": "United States",
    "CA": "Canada",
    "CN": "China",
}

# Default scan interval (minutes) — minimum 15 to avoid account bans
DEFAULT_SCAN_INTERVAL = 15
MIN_SCAN_INTERVAL = 5

# CarConnectivity data paths (relative to /garage/{VIN}/)
PATH_FUEL_LEVEL         = "fuellevel/value"
PATH_BATTERY_SOC        = "charging/batteryStatus/stateOfChargeInPercent"
PATH_RANGE              = "range/value"
PATH_ODOMETER           = "odometer/value"
PATH_DOORS_LOCK_STATE   = "access/accessStatus/doorLockStatus"
PATH_DOORS              = "access/accessStatus/doors"
PATH_WINDOWS            = "access/accessStatus/windows"
PATH_POSITION_LAT       = "position/latitude"
PATH_POSITION_LON       = "position/longitude"
PATH_CLIMATISATION      = "climatisation/climatisationStatus/climatisationState"
PATH_CHARGING_STATE     = "charging/chargingStatus/chargingState"
PATH_PLUG_STATE         = "charging/plugStatus/plugConnectionState"
PATH_TARGET_SOC         = "charging/chargingSettings/targetSOCInPercent"
PATH_REMAINING_RANGE_EL = "charging/batteryStatus/currentSOCInPercent"
PATH_OIL_LEVEL          = "measurements/oilLevel/value"
PATH_SERVICE_DAYS       = "vehicleHealthInspection/maintenanceStatus/inspectionDueDays"
PATH_SERVICE_KM         = "vehicleHealthInspection/maintenanceStatus/inspectionDueDistance"
PATH_OUTSIDE_TEMP       = "measurements/outsideTemperature/value"

# Icons
ICON_CAR        = "mdi:car"
ICON_FUEL       = "mdi:gas-station"
ICON_BATTERY    = "mdi:battery-charging"
ICON_RANGE      = "mdi:map-marker-distance"
ICON_ODOMETER   = "mdi:counter"
ICON_LOCK       = "mdi:car-door-lock"
ICON_DOOR       = "mdi:car-door"
ICON_WINDOW     = "mdi:car-windshield"
ICON_LOCATION   = "mdi:map-marker"
ICON_CLIMATE    = "mdi:thermometer"
ICON_CHARGE     = "mdi:ev-plug-type2"
ICON_SERVICE    = "mdi:wrench-clock"
ICON_OIL        = "mdi:oil"
ICON_TEMP       = "mdi:thermometer"

CONF_FORCE_ACCESS = "force_enable_access"  # VW/Audi ohne access-Capability
