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
    client_secret: str = ""
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
    user_agent="OLASeat/2.13.3 (Android 12; sdk_gphone64_x86_64; Google) Mobile",
    api_base="https://ola.prod.code.seat.cloud.vwgroup.com",
    # `address` + `email` mirror the official My SEAT app — defense in depth so
    # OLA endpoints that conditionally require either claim never get tripped.
    scope="openid profile address phone email birthdate nickname",
)

BRAND_CUPRA = BrandConfig(
    name="cupra",
    client_id="3c756d46-f1ba-4d78-9f9a-cff0d5292d51@apps_vw-dilab_com",
    redirect_uri="cupra://oauth-callback",
    user_agent="OLACupra/2.15.0 (Android 12; sdk_gphone64_x86_64; Google) Mobile",
    api_base="https://ola.prod.code.seat.cloud.vwgroup.com",
    client_secret="eb8814e641c81a2640ad62eeccec11c98effc9bccd4269ab7af338b50a94b3a2",
    # See BRAND_SEAT above — same OLA backend, same scope set.
    scope="openid profile address phone email birthdate nickname",
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
    # v1.10.0 (#94 — PHEV range triple).
    # ``range_km`` stays as the headline number (back-compat — existing
    # automations and dashboards keep working). Three new explicit fields
    # let PHEVs and EVs surface what the API actually distinguishes:
    #   electric_range_km — battery-only remaining range
    #   combustion_range_km — petrol/diesel/CNG/LPG remaining range
    #   total_range_km — combined range (only meaningful for hybrids)
    # Brand clients populate these from per-engine blocks
    # (``fuelStatus.rangeStatus.value.{primaryEngine,secondaryEngine}``
    # plus ``measurements.rangeStatus.value.{dieselRange,gasolineRange}``
    # for older Audi models). Conditional sensor creation in sensor.py
    # uses ``is not None`` so pure EVs never get a phantom combustion
    # entity and pure ICE never get an electric one.
    electric_range_km: int | None = None
    combustion_range_km: int | None = None
    total_range_km: int | None = None
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
    # v1.8.9 (Session 3C) — per-window state, mirrors ``doors_individual``.
    # Keys: frontLeft / frontRight / rearLeft / rearRight. Value True ==
    # window closed, False == open. Populated by SEAT/CUPRA OLA paths
    # (status.windows.{position}); other brands leave it empty for now.
    windows_individual: dict[str, bool] = field(default_factory=dict)

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
    # v1.8.11 (Session 3S) — when the *vehicle* last reported data to the
    # backend, derived from ``carCapturedTimestamp`` on the status response
    # sub-objects. ``last_updated_at`` above tracks when we last *polled*
    # the backend; this tracks when the backend last actually heard from
    # the car. The two diverge during weekend backend outages, when the
    # car is asleep, or when 12V drops too low to send heartbeats.
    # Currently populated by SkodaClient; other brands keep it None until
    # they grow analogous parsing.
    last_seen_at: Any | None = None

    # Service
    service_km: int | None = None
    service_due_at: Any | None = None
    oil_service_km: int | None = None
    oil_service_at: Any | None = None
    # v1.11.0 (#91 closure) — explicit "raw int days" sensors complementing
    # the existing DATE sensors. The DATE conversion (sensor.py) loses the
    # exact day count; users who want "5 days remaining" instead of
    # "May 5, 2026" can read these directly. Populated by brand parsers
    # from the same backend integers. Keep both fields populated so the
    # DATE-class sensor and the int sensor both work.
    service_due_in_days: int | None = None
    oil_service_due_in_days: int | None = None
    # v1.17.7 (#130 Chr1sDub + #133 christianmhz — two converging Skoda
    # Scout-Reports 2026-05-04). Skoda mysmob now exposes the user's
    # registered preferred-workshop info on the maintenance endpoint.
    # Surfaced as extra_state_attributes on the ``service_due_in_days``
    # sensor (see sensor.py) so users see workshop name + contact
    # alongside the "next service in X days" number. Dict shape is
    # whatever the backend ships — typical keys: name, brand,
    # partnerNumber, id, contact{phone, email}, address{street, city,
    # postalCode, country}, location{lat, lon}, openingHours[].
    # Currently populated by SkodaClient; other brands leave it None.
    preferred_workshop: dict[str, Any] | None = None

    # v1.19.1 — Pycupra-style API quota visibility. Populated from
    # X-RateLimit-Remaining response header captured by base.py
    # ``_capture_rate_limit_headers``. Brand-shared (the same auth
    # cookie / token has the same daily budget regardless of which
    # vehicle's endpoint we hit), so the coordinator copies it onto
    # every VIN's data dict for HA sensor mapping. ``None`` means the
    # backend has never sent the header for this brand — sensor stays
    # ``unknown`` instead of showing a stale 0.
    requests_remaining_today: int | None = None
    requests_limit_today: int | None = None
    requests_reset_at: Any | None = None

    # v1.20.0 (Bundle 2 Phase A — Skoda widget + vehicle-info + equipment).
    # Three new static-ish enrichment fields populated from myskoda PR
    # #557 widget endpoint + /vehicle-information/{vin} + /equipment.
    # Currently Skoda-only; other brands leave them None.
    # NOTE: ``license_plate`` already exists above (line 156) — do not
    # re-declare. Skoda widget parser populates the existing field.
    render_url: str | None = None          # widget.vehicle.renderUrl (image)
    equipment: list[dict[str, Any]] | None = None  # equipment.equipment[]
    equipment_count: int | None = None     # derived: len(equipment)
    # v1.22.x foundation (myskoda PR #571 confirmed live 2026-05-02) —
    # multi-angle composite renders from
    # ``GET /api/v1/vehicle-information/{vin}/renders``.
    # Keyed by lowercased ``viewPoint`` (e.g. ``exterior_side``,
    # ``interior_boot``); value is the highest-order ``REAL`` layer URL
    # found in that ``compositeRenders[]`` entry. SCAFFOLDING: parser
    # + cache wired here, image-platform entity expansion deferred to
    # next MINOR (would add ~6 new ImageEntity per Skoda VIN — strict
    # semver requires MINOR for new entity inventory).
    composite_render_urls: dict[str, str] | None = None

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

    # v1.12.0 (#23) — 12V starter battery status. Critical for older
    # vehicles with degrading 12V batteries — symptom is "API stops
    # responding for hours/days" and many users blame the integration
    # before realising their 12V is at 10.8V and the car can't keep
    # the modem awake. Threshold for ``warning_12v_low`` is documented
    # in the binary_sensor description; volkswagencarnet PR #940 used
    # 11.5 V (12.6 V is healthy, 11.5 V is "needs attention", 10.5 V
    # is "battery dead").
    voltage_12v: float | None = None
    warning_12v_low: bool | None = None

    # v1.11.0 (#91 closure) — Vehicle lights status.
    # ``lights_on`` is the safe aggregate ("any light on?"); created
    # whenever the ``vehicleLights.lightsStatus.value.lights[]`` array
    # is present (regardless of element shape).
    # ``lights_count`` mirrors the on-count for users who want a numeric
    # value in dashboards.
    # ``lights_individual`` is best-effort per-light state. We probe
    # several known shapes (``{name, status}``, ``{id, status}``,
    # ``{location.position, status}``) but if none match we leave it
    # empty rather than guess. Per-light binary_sensors are only
    # registered at setup time when this dict is populated.
    lights_on: bool | None = None
    lights_count: int | None = None
    lights_individual: dict[str, bool] = field(default_factory=dict)

    # Hood / trunk / sunroof
    hood_open: bool | None = None
    trunk_open: bool | None = None
    trunk_locked: bool | None = None
    sunroof_open: bool | None = None

    # v1.17.1 (Bruno seq 10/11) — SEAT/CUPRA Battery Care.
    # Two read-only fields populated from the new OLA endpoints:
    # - GET /v1/vehicles/{vin}/charging/battery-care → {enabled: bool}
    # - GET /v1/vehicles/{vin}/charging/battery-care/target → {targetSocPercentage: int}
    # Skoda also has battery-care under different paths (covered in
    # v1.15.0 cap-id work); this is the SEAT/CUPRA-specific surface.
    battery_care_enabled: bool | None = None
    battery_care_target_soc_pct: int | None = None

    # v1.16.0 (#25, #31) — Skoda Charging Profiles (mysmob endpoint
    # ``/v1/charging/{vin}/profiles``). Read-only sensors expose:
    # - which profile is active at the car's CURRENT GPS position
    #   (``active_charging_profile_name`` from
    #   ``currentVehiclePositionProfile.name``) — solves #25 location-
    #   based target SoC by surfacing the backend's own decision
    # - next upcoming charging time
    # - target SoC for the active profile
    # - count of registered profiles
    # ``charging_profiles`` (full list) lives in attributes for the
    # active-profile sensor — vermeidet 255-char state limit. Write-side
    # for editing profiles is deferred (myskoda has POST/PUT but those
    # endpoints need their own bundle).
    active_charging_profile_name: str | None = None
    active_charging_profile_target_soc_pct: int | None = None
    next_charging_time: str | None = None
    charging_profiles_count: int | None = None
    charging_profiles: list[dict[str, Any]] = field(default_factory=list)

    # v1.15.0 (#35) — Skoda Charging History (mysmob endpoint
    # ``/v1/charging/{vin}/history``). Drives HA Energy Dashboard via
    # ``total_charged_energy_kwh`` with state_class=TOTAL_INCREASING.
    # Skoda-only initially — CARIAD-BFF + OLA don't expose an equivalent
    # endpoint with chargedEnergy_kWh per session (verified 2026-05-02).
    # ``recent_sessions`` (last 5) lives in attributes to avoid the HA
    # 255-char state limit.
    total_charged_energy_kwh: float | None = None
    last_charging_session_kwh: float | None = None
    last_charging_session_duration_min: int | None = None
    last_charging_session_current_type: str | None = None
    last_charging_session_start: str | None = None
    recent_charging_sessions: list[dict[str, Any]] = field(default_factory=list)

    # v1.15.0 — Software-version + OTA update status (Skoda mysmob).
    # Endpoint ``GET /v1/vehicle-information/{vin}/software-version/update-status``
    # shipped in Skoda app v8.10.0+ (myskoda PR #541). Cross-brand support
    # deferred — CARIAD-BFF + OLA don't expose an equivalent endpoint yet
    # (Research 2026-05-02). Fields stay ``None`` for non-Skoda vehicles.
    # ``software_update_status`` is the raw enum string (NO_UPDATE_AVAILABLE
    # / UPDATE_SUCCESSFUL / future values) — defensive: we don't gate on
    # the enum, the bool ``ota_update_available`` is what entities consume.
    software_version: str | None = None
    software_update_status: str | None = None
    ota_update_available: bool | None = None
    ota_release_notes_url: str | None = None

    # v1.14.0 (#24) — Trip Statistics from CARIAD-BFF
    # ``GET /vehicle/v1/vehicles/{vin}/tripstatistics?type={shortTerm|longTerm}``.
    # Both endpoints return ``{tripDataList: {tripData: [...]}}``; we sort
    # by ``overallMileage`` desc and take ``[0]`` as the most recent
    # trip (the audi #113 "aggregate-in-state" convention — keeps each
    # field a separate sensor state rather than building a list entity).
    # Consumption fields come back from the API as integers ×10
    # (averageFuelConsumption: 68 ⇒ 6.8 l/100 km); the parser divides
    # by 10 so the value stored here is already the human number.
    # ``recent_trips`` holds the last 5 short-term trips for the
    # ``last_trip_distance_km`` sensor's ``extra_state_attributes`` —
    # avoids state-string-too-long (255 char limit).
    last_trip_distance_km: float | None = None
    last_trip_duration_min: int | None = None
    last_trip_avg_speed_kmh: float | None = None
    last_trip_avg_fuel_consumption_l_100km: float | None = None
    last_trip_avg_electric_consumption_kwh_100km: float | None = None
    last_trip_timestamp: str | None = None
    lifetime_distance_km: float | None = None
    lifetime_avg_fuel_consumption_l_100km: float | None = None
    lifetime_avg_electric_consumption_kwh_100km: float | None = None
    recent_trips: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to plain dict for coordinator.vehicles storage."""
        from dataclasses import asdict  # noqa: PLC0415
        return asdict(self)
