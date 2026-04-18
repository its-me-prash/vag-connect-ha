# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Data models for the CARIAD API client."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BrandConfig:
    """Per-brand constants for IDK authentication and API access."""

    name: str
    client_id: str
    redirect_uri: str
    user_agent: str
    api_base: str
    scope: str = (
        "openid profile badge birthdate birthplace nationalIdentifier "
        "nationality profession email vin phone nickname name picture mbb "
        "gallery cars dealers"
    )

    @property
    def app_prefix(self) -> str:
        """Scheme prefix used to detect auth redirect (e.g. 'myaudi')."""
        return self.redirect_uri.split("://")[0]


# All client IDs sourced from MIT/Apache-2.0 open-source projects.
# See docs/research/VAG_GROUP_ECOSYSTEM.md for full attribution.

BRAND_VW_EU = BrandConfig(
    name="volkswagen",
    client_id="a24fba63-34b3-4d43-b181-942111e6bda8@apps_vw-dilab_com",
    redirect_uri="weconnect://authenticated",
    user_agent="Volkswagen/3.51.1-android/14",
    api_base="https://emea.bff.cariad.digital",
    # scope from volkswagencarnet (robinostlund/volkswagencarnet, MIT) — confirmed working
    scope="openid profile badge cars dealers vin",
)

BRAND_AUDI = BrandConfig(
    name="audi",
    # client_id from audiconnect (arjenvrh/audi_connect_ha, MIT) — confirmed working
    client_id="09b6cbec-cd19-4589-82fd-363dfa8c24da@apps_vw-dilab_com",
    redirect_uri="myaudi:///",
    user_agent="Android/4.31.0 (Build 800341641.root project 'myaudi_android'.ext.buildTime) Android/13",
    api_base="https://emea.bff.cariad.digital",
    # scope exactly matching audiconnect — no extra "cars"/"dealers" scopes
    scope=(
        "address profile badge birthdate birthplace nationalIdentifier nationality "
        "profession email vin phone nickname name picture mbb gallery openid"
    ),
)

BRAND_SKODA = BrandConfig(
    name="skoda",
    client_id="7f045eee-7003-4379-9968-9355ed2adb06@apps_vw-dilab_com",
    redirect_uri="myskoda://redirect/login/",
    user_agent="MySkoda/1.0 Android",
    api_base="https://mysmob.api.connect.skoda-auto.cz",
    scope=(
        "address badge birthdate cars driversLicense dealers email mileage mbb "
        "nationalIdentifier openid phone profession profile vin"
    ),
)

BRAND_SEAT = BrandConfig(
    name="seat",
    client_id="99a5b77d-bd88-4d53-b4e5-a539c60694a3@apps_vw-dilab_com",
    redirect_uri="seat://oauth-callback",
    user_agent="OLASeat/2.10.1 (Android 12; sdk_gphone64_x86_64; Google) Mobile",
    api_base="https://ola.prod.code.seat.cloud.vwgroup.com",
    scope="openid profile nickname birthdate phone",
)

BRAND_CUPRA = BrandConfig(
    name="cupra",
    client_id="3c756d46-f1ba-4d78-9f9a-cff0d5292d51@apps_vw-dilab_com",
    redirect_uri="cupra://oauth-callback",
    user_agent="OLACupra/2.10.0 (Android 12; sdk_gphone64_x86_64; Google) Mobile",
    api_base="https://ola.prod.code.seat.cloud.vwgroup.com",
    scope="openid profile nickname birthdate phone",
)

BRAND_VW_NA_MODEL = BrandConfig(
    name="volkswagen_na",
    client_id="59992128-69a9-42c3-8621-7942041ba824_MYVW_ANDROID",
    redirect_uri="kombi:///login",
    user_agent="MyVW/1.0 Android",
    api_base="https://b-h-s.spr.us00.p.con-veh.net",
    scope="openid profile email offline_access mbb vin cars dealers",
)

BRAND_PORSCHE = BrandConfig(
    name="porsche",
    client_id="XhygisuebbrqQ80byOuU5VncxLIm8E6H",
    redirect_uri="my-porsche-app://auth0/callback",
    user_agent="My Porsche/2.1.0 (iPhone; iOS 17.0; Scale/3.00)",
    api_base="https://api.ppa.porsche.com",
    scope="openid profile email offline_access mbb vin cars charging",
)

BRANDS: dict[str, BrandConfig] = {
    "volkswagen":    BRAND_VW_EU,
    "audi":          BRAND_AUDI,
    "skoda":         BRAND_SKODA,
    "seat":          BRAND_SEAT,
    "cupra":         BRAND_CUPRA,
    "volkswagen_na": BRAND_VW_NA_MODEL,
    "porsche":       BRAND_PORSCHE,
}


@dataclass
class TokenSet:
    """OAuth2 token bundle from IDK."""

    access_token: str
    refresh_token: str
    id_token: str
    expires_at: float = 0.0  # Unix timestamp — 0 = unknown, refresh proactively 60s before

    def is_valid(self) -> bool:
        """Return True if all required tokens are present."""
        return bool(self.access_token and self.refresh_token and self.id_token)

    def needs_refresh(self) -> bool:
        """True if token expires within 60 seconds or expiry is unknown."""
        if not self.expires_at:
            return False  # unknown → let the API tell us via 401
        import time
        return time.time() >= self.expires_at - 60


@dataclass
class VehicleData:
    """Unified vehicle data model — brand-agnostic.

    All fields are Optional so partial data never raises KeyError.
    Coordinator maps this to its vehicles dict.
    """

    vin: str
    model: str | None = None
    model_year: int | None = None
    manufacturer: str | None = None
    firmware_version: str | None = None
    license_plate: str | None = None

    # Render images — dict of mediaType → public URL (fetched via GraphQL, no auth needed to GET)
    # e.g. {"MYAPN8NB": "https://mediaservice.audi.com/media/fast/v3_...", ...}
    image_urls: dict = None  # type: ignore[assignment]
    # Vehicle media names from GraphQL (vehicle.media.shortName/longName)
    # Warning lights
    warning_active: bool = False
    warning_count: int = 0
    warning_oil: bool = False
    warning_engine: bool = False
    warning_tyre: bool = False
    warning_brakes: bool = False

    media_short_name: str | None = None  # e.g. "Q4 e-tron"
    media_long_name: str | None = None   # e.g. "Audi Q4 50 e-tron quattro"
    media_exterior_color: str | None = None

    def __post_init__(self) -> None:
        """Initialise mutable defaults."""
        if self.image_urls is None:
            self.image_urls = {}

    # Drivetrain
    is_electric: bool = False
    has_battery: bool = False
    has_combustion: bool = False
    is_hybrid: bool = False

    # Range & energy
    battery_soc: int | None = None
    battery_available_kwh: float | None = None
    battery_cap_kwh: float | None = None
    battery_temp: float | None = None
    fuel_level: int | None = None
    range_km: int | None = None
    range_estimated_full_km: int | None = None
    range_wltp_km: int | None = None
    odometer_km: int | None = None

    # Charging
    charging_state: str | None = None
    is_charging: bool = False
    plug_state: str | None = None
    plug_connected: bool = False
    charging_power_kw: float | None = None
    charging_rate_kmh: float | None = None
    charge_complete_eta: Any | None = None
    charging_type: str | None = None
    target_soc: int | None = None
    max_charge_current: float | None = None
    min_soc: int | None = None  # Minimum SoC for departure timer (PHEV)
    auto_unlock_charge: bool = False
    connector_locked: bool = False
    charging_station_name: str | None = None
    charging_station_address: str | None = None
    charging_station_kw: float | None = None
    charging_station_operator: str | None = None
    charge_mode: str | None = None  # MANUAL | TIMER | PREFERRED_CHARGING_TIMES | IMMEDIATE_DISCHARGING

    # Climate
    climatisation_state: str | None = None
    climatisation_active: bool = False
    target_temperature: float | None = None
    outside_temp: float | None = None

    # Access
    doors_locked: bool = False
    doors_open: bool = False
    windows_open: bool = False
    doors_individual: dict[str, bool] = field(default_factory=dict)

    # Location
    latitude: float | None = None
    longitude: float | None = None
    parking_address: str | None = None
    parking_city: str | None = None
    heading: int | None = None

    # Status
    vehicle_state: str | None = None
    connection_state: str | None = None
    is_driving: bool = False
    is_online: bool = False
    last_updated_at: Any | None = None

    # Service
    service_km: int | None = None
    service_due_at: Any | None = None
    oil_service_km: int | None = None
    oil_service_at: Any | None = None

    # Departure timers
    departure_timer_1_enabled: bool = False
    departure_timer_1_time: str | None = None
    departure_timer_2_enabled: bool = False
    departure_timer_2_time: str | None = None
    departure_timer_3_enabled: bool = False
    departure_timer_3_time: str | None = None

    # Window heating
    window_heating_front: bool | None = None
    window_heating_back: bool | None = None

    # AdBlue (diesel)
    adblue_range_km: int | None = None

    # Hood / trunk / sunroof
    hood_open: bool | None = None
    trunk_open: bool | None = None
    trunk_locked: bool | None = None
    sunroof_open: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to plain dict for coordinator.vehicles storage."""
        from dataclasses import asdict  # noqa: PLC0415
        return asdict(self)
