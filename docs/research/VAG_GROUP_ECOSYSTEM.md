# VAG Group — Connected Car Ecosystem Audit

> Research by Prash Balan (@its-me-prash) — April 2026  
> Apache 2.0 / CC-BY-SA 4.0

---

## Volkswagen Group Structure (Connected Services)

```
Volkswagen AG
├── PASSENGER CARS (connected services exist)
│   ├── Volkswagen EU          ← CARIAD BFF + IDK Auth
│   ├── Volkswagen NA (US/CA)  ← separate VW NA Auth + API
│   ├── Volkswagen CN          ← IDK Auth + China server (pre-2026)
│   │                             CEA / XPeng platform (2026+, undocumented)
│   ├── Audi EU                ← CARIAD BFF + IDK Auth + AZS/MBB extra steps
│   ├── Audi NA (AOA)          ← Audi of America GraphQL endpoint
│   ├── Škoda                  ← own API server + IDK Auth + MQTT
│   ├── SEAT                   ← own API server + IDK Auth
│   ├── CUPRA                  ← own API server + IDK Auth
│   └── Porsche                ← Auth0 (identity.porsche.com) + own API
├── COMMERCIAL VEHICLES
│   └── VW Nutzfahrzeuge       ← WeConnect Pro (IDK Auth, same as VW EU)
└── NO API (ultra-luxury / trucks)
    ├── Lamborghini            ← no public connected-car API found
    ├── Bentley                ← no public API found
    ├── Bugatti                ← no API (too small)
    ├── Ducati                 ← motorcycles, no car API
    ├── MAN Trucks             ← separate fleet API, not relevant
    └── Scania                 ← separate fleet API, not relevant
```

---

## Authentication Systems

### System 1 — VAG IDK (covers 6 of 9 brands)

**Endpoint:** `https://identity.vwgroup.io/oidc/v1/authorize`

**Flow:** Standard PKCE/OAuth2
```
1. GET  /oidc/v1/authorize?client_id=...&code_challenge=...&response_type=code
   → HTML page with CSRF token (hmac + relayState)

2. POST /signin-service/v1/{CLIENT_ID}/login/identifier
        {email, hmac, relayState, _csrf}

3. POST /signin-service/v1/{CLIENT_ID}/login/authenticate
        {email, password, hmac, relayState, _csrf}
   → redirect chain → {BRAND_URI}?code=AUTH_CODE

4. POST token_endpoint
        {client_id, grant_type=authorization_code, code, redirect_uri, code_verifier}
   → {access_token, refresh_token, id_token}

5. (Audi only: AZS token + MBB client register + MBB auth — 3 extra steps)
```

**Client IDs (all discovered from MIT/Apache open-source projects):**

| Brand | Client ID | Source | License |
|---|---|---|---|
| VW EU | `a24fba63-34b3-4d43-b181-942111e6bda8@apps_vw-dilab_com` | volkswagencarnet | GPL-3.0 |
| VW EU (WeConnect) | same as above | WeConnect-python | MIT |
| Audi (new) | `f4d0934f-32bf-4ce4-b3c4-699a7049ad26@apps_vw-dilab_com` | CC-connector-audi | MIT |
| Audi (legacy) | `09b6cbec-cd19-4589-82fd-363dfa8c24da@apps_vw-dilab_com` | audiconnect | MIT |
| Škoda | `7f045eee-7003-4379-9968-9355ed2adb06@apps_vw-dilab_com` | myskoda | MIT |
| SEAT | `99a5b77d-bd88-4d53-b4e5-a539c60694a3@apps_vw-dilab_com` | pycupra | Apache-2.0 |
| CUPRA | `3c756d46-f1ba-4d78-9f9a-cff0d5292d51@apps_vw-dilab_com` | pycupra | Apache-2.0 |

**Headers per brand:**
| Brand | User-Agent | App Package |
|---|---|---|
| VW | `Volkswagen/3.51.1-android/14` | `com.volkswagen.weconnect` |
| Audi | `Android/4.31.0 (Build 800341641...) Android/13` | `de.myaudi.mobile.assistant` |
| Škoda | dynamisch aus App | `cz.skodaauto.myskoda` |
| SEAT | `OLASeat/2.10.1 (Android 12; ...) Mobile` | `com.cupra.mycupra` |
| CUPRA | `OLACupra/2.10.0 (Android 12; ...) Mobile` | `com.cupra.mycupra` |

---

### System 2 — Porsche ID (Auth0)

**Auth endpoint:** `https://identity.porsche.com/authorize`  
**Token endpoint:** `https://identity.porsche.com/oauth/token`  
**Client ID:** `XhygisuebbrqQ80byOuU5VncxLIm8E6H`  
**X-Client-ID:** `41843fb4-691d-4970-85c7-2673e8ecef40`  
**API base:** `https://api.ppa.porsche.com/app`  
**Source:** pyporscheconnectapi (MIT)

Porsche uses Auth0, NOT the VAG IDK system — completely separate identity platform.

---

### System 3 — VW North America

**Auth endpoint:** `https://b-h-s.spr.{country}00.p.con-veh.net/oidc/v1/authorize`  
**Client IDs:**
- US: `59992128-69a9-42c3-8621-7942041ba824_MYVW_ANDROID`
- CA: `69eb3c39-d2be-4006-8197-37cc4971e8fe_MYVW_ANDROID`

**Source:** CarConnectivity-connector-volkswagen-na (MIT)

---

## API Backends per Brand

### VW EU — CARIAD BFF

**Base:** `https://emea.bff.cariad.digital`

```
GET  /vehicle/v1/vehicles                                     # vehicle list
GET  /vehicle/v1/vehicles/{vin}/selectivestatus               # all data
     ?jobs=access,automation,batteryChargingCare,charging,
           climatisation,climatisationTimers,departureTimers,
           fuelStatus,measurements,readiness,userCapabilities,
           vehicleLights,vehicleHealthInspection
POST /vehicle/v1/vehicles/{vin}/access/lock-unlock            # lock/unlock
POST /vehicle/v1/vehicles/{vin}/climatisation/start-stop     # climate
POST /vehicle/v1/vehicles/{vin}/charging/start-stop          # charging
GET  /vehicle/v1/vehicles/{vin}/parkingposition               # GPS
GET  /vehicle/v1/vehicles/{vin}/tripstatistics               # trips
GET  /vehicle/v1/vehicles/{vin}/pendingrequests               # command status
```

**Data paths (from vw_const.py, volkswagencarnet):**
```python
# Charging
"charging.chargingStatus.value.chargingState"
"charging.chargingStatus.value.chargePower_kW"
"charging.chargingStatus.value.chargeRate_kmph"
"charging.chargingStatus.value.remainingChargingTimeToComplete_min"
"charging.batteryStatus.value.currentSOC_pct"
"charging.batteryStatus.value.cruisingRangeElectric_km"
"charging.plugStatus.value.plugConnectionState"
"charging.chargingSettings.value.targetSOC_pct"
"charging.chargingSettings.value.maxChargeCurrentAC"

# Measurements
"measurements.odometerStatus.value.odometer"
"measurements.rangeStatus.value.totalRange_km"
"measurements.rangeStatus.value.electricRange"
"measurements.rangeStatus.value.gasolineRange"
"measurements.rangeStatus.value.adBlueRange"
"measurements.fuelLevelStatus.value.currentFuelLevel_pct"
"measurements.temperatureBatteryStatus.value.temperatureHvBatteryMin_K"
"measurements.temperatureBatteryStatus.value.temperatureHvBatteryMax_K"

# Access
"access.accessStatus.value.doorLockStatus"
"access.accessStatus.value.doors"
"access.accessStatus.value.windows"
"access.accessStatus.value.overallStatus"

# Climatisation
"climatisation.climatisationStatus.value.climatisationState"
"climatisation.climatisationStatus.value.remainingClimatisationTime_min"
"climatisation.climatisationSettings.value.targetTemperature_C"
"climatisation.windowHeatingStatus.value.windowHeatingStatus"
"climatisation.auxiliaryHeatingStatus.value.climatisationState"

# Readiness (online/offline)
"readiness.readinessStatus.value.connectionState.isOnline"
"readiness.readinessStatus.value.connectionState.isActive"
"readiness.readinessStatus.value.connectionState.batteryPowerLevel"

# Vehicle Health
"vehicleHealthInspection.maintenanceStatus.value.inspectionDue_days"
"vehicleHealthInspection.maintenanceStatus.value.inspectionDue_km"
"vehicleHealthInspection.maintenanceStatus.value.oilServiceDue_days"
"vehicleHealthInspection.maintenanceStatus.value.oilServiceDue_km"

# Departure Timers
"departureTimers.departureTimersStatus.value.timers"
"departureProfiles.departureProfilesStatus.value.timers"

# Parking
"parkingposition.lat"
"parkingposition.lon"
"parkingposition.carCapturedTimestamp"

# Lights
"vehicleLights.lightsStatus.value.lights"

# Trip Statistics
GET /vehicle/v1/vehicles/{vin}/tripstatistics?type=shortTerm
GET /vehicle/v1/vehicles/{vin}/tripstatistics?type=longTerm
```

---

### Audi EU — CARIAD BFF + AZS + MBB

Same CARIAD BFF endpoints as VW EU for data, but auth requires 3 extra steps:

```
After standard IDK auth:

5. POST https://emea.bff.cariad.digital/login/v1/audi/token
        {token: id_token, grant_type: "id_token", stage: "live", config: "myaudi"}
   → audiToken (AZS token)

6. POST https://mbboauth-1d.prd.ece.vwg-connect.com/mbbcoauth/mobile/register/v1
        {client_name, platform, client_brand: "Audi", appName, appVersion, appId}
   → {client_id: xclientId}

7. POST https://mbboauth-1d.prd.ece.vwg-connect.com/mbbcoauth/...
        {grant_type: "id_token", token: bearer_token.id_token, scope: "sc2:fal"}
        Header: X-Client-ID: {xclientId}
   → vwToken
```

Audi also has trip data via GraphQL:
```
POST https://app-api.live-my.audi.com/vgql/v1/graphql   # EU
POST https://app-api.my.aoa.audi.com/vgql/v1/graphql    # US/AOA
```

---

### Škoda — own server + IDK Auth + MQTT

**Base:** `https://mysmob.api.connect.skoda-auto.cz`

```
GET  /v2/garage                                              # vehicle list
GET  /v2/garage/vehicles/{vin}                               # vehicle detail
GET  /v2/vehicle-status/{vin}                               # status (locks, windows)
GET  /v1/charging/{vin}                                      # charging data
GET  /v2/air-conditioning/{vin}                             # AC/climate
GET  /v2/air-conditioning/{vin}/auxiliary-heating           # aux heating
GET  /v1/maps/positions?vin={vin}                           # GPS
GET  /v3/maps/positions/vehicles/{vin}/parking              # parking position
GET  /v1/trip-statistics/{vin}?offsetType=week              # trip stats
GET  /v1/trip-statistics/{vin}/single-trips                 # single trips
GET  /v3/vehicle-maintenance/vehicles/{vin}                 # maintenance
GET  /v3/vehicle-maintenance/vehicles/{vin}/report          # maintenance report
GET  /v2/vehicle-status/{vin}/driving-range                 # range
GET  /v2/vehicle-status/{vin}/driving-score                 # efficiency score
GET  /v1/vehicle-information/{vin}                          # model info
GET  /v1/vehicle-automatization/{vin}/departure/timers      # departure timers
GET  /v2/connection-status/{vin}/readiness                  # online status

POST /v1/vehicle-access/{vin}/lock                          # lock
POST /v1/vehicle-access/{vin}/unlock                        # unlock
POST /v2/air-conditioning/{vin}/start                       # start AC
POST /v2/air-conditioning/{vin}/stop                        # stop AC
POST /v2/air-conditioning/{vin}/start-window-heating        # window heating
POST /v2/air-conditioning/{vin}/stop-window-heating
POST /v2/air-conditioning/{vin}/auxiliary-heating/start     # aux heating
POST /v2/air-conditioning/{vin}/auxiliary-heating/stop
POST /v1/charging/{vin}/start                               # start charging
POST /v1/charging/{vin}/stop                                # stop charging
POST /v1/charging/{vin}/set-charge-limit                    # target SOC
POST /v1/charging/{vin}/set-care-mode                      # battery care
POST /v1/charging/{vin}/set-auto-unlock-plug               # auto unlock
POST /v1/charging/{vin}/set-charging-current               # max current
POST /v1/vehicle-access/{vin}/honk-and-flash               # flash lights
POST /v1/vehicle-wakeup/{vin}?applyRequestLimiter=true     # wake up
POST /v1/spin/verify                                        # SPIN verification

# MQTT (real-time events — push updates!)
Broker: mqtt.messagehub.de:8883
Topics: air-conditioning/*, charging/*, departure/*, vehicle-status/*, vehicle-connection-status-update
```

---

### SEAT / CUPRA — OLA server

**Base:** `https://ola.prod.code.seat.cloud.vwgroup.com`

```
GET  /v2/users/{userId}/garage/vehicles                      # vehicle list
GET  /v5/users/{userId}/vehicles/{vin}/mycar                 # full status
GET  /v1/vehicles/{vin}/charging                             # charging
GET  /v2/vehicles/{vin}/climatisation                        # climate
GET  /v1/vehicles/{vin}/climatisation/status                 # climate status
GET  /v1/vehicles/{vin}/parkingposition                      # GPS
GET  /v2/vehicles/{vin}/driving-data/CUSTOM?from=...&to=...  # trip data
GET  /v1/vehicles/{vin}/mileage                              # odometer
GET  /v1/vehicles/{vin}/maintenance                          # service data
GET  /v2/vehicles/{vin}/status                               # locks/windows

POST /v1/vehicles/{vin}/access/{action}                     # lock/unlock
POST /v2/vehicles/{vin}/climatisation                       # climate control
POST /v1/vehicles/{vin}/{capability}/actions                # general actions
POST /v1/vehicles/{vin}/vehicle-wakeup/request              # wake up
POST /v2/users/{userId}/spin/verify                         # SPIN
POST /v1/vehicles/{vin}/honk-and-flash                      # flash
```

---

### Porsche — Auth0 + PPA API

**Base:** `https://api.ppa.porsche.com/app`

```
GET  /core/api/v3/sp/vehicles                                # vehicle list
GET  /core/api/v3/sp/vehicles/{vin}/selectivestatus          # data (similar to VW)
     measurements: BATTERY_LEVEL, FUEL_LEVEL, MILEAGE,
                   GPS_LOCATION, LOCK_STATE_VEHICLE,
                   CLIMATIZER_STATE, CHARGING_SUMMARY,
                   CHARGING_PROFILES, DEPARTURES,
                   TIRE_PRESSURE, OIL_LEVEL_CURRENT, ...
POST /core/api/v3/sp/vehicles/{vin}/command/{command}        # actions
     LOCK, UNLOCK, HONK_FLASH, REMOTE_CLIMATIZER_START/STOP,
     DIRECT_CHARGING_START/STOP, TIMERS_EDIT, ...
GET  /core/api/v3/sp/vehicles/{vin}/tripstatistics/{type}    # trips
```

---

## Reference Projects Used

| Project | License | URL | Notes |
|---|---|---|---|
| volkswagencarnet | GPL-3.0 | github.com/robinostlund/volkswagencarnet | VW EU API reference, cannot copy code |
| audiconnect | MIT | github.com/audiconnect/audi_connect_ha | Audi API, code referenceable |
| myskoda | MIT | github.com/skodaconnect/myskoda | Škoda API, usable as dependency |
| pycupra | Apache-2.0 | github.com/WulfgarW/pycupra | SEAT/CUPRA API reference |
| pyporscheconnectapi | MIT | github.com/CJNE/pyporscheconnectapi | Porsche API reference |
| CC-connector-audi | MIT | github.com/acfischer42/CarConnectivity-connector-audi | Newer Audi client_id |
| CC-connector-vw-na | MIT | github.com/zackcornelius/CarConnectivity-connector-volkswagen-na | VW NA auth |
| WeConnect-python | MIT | github.com/tillsteinbach/WeConnect-python | VW EU legacy reference |
| ha-porscheconnect | MIT | github.com/CJNE/ha-porscheconnect | Porsche HA integration |

---

## Why CarConnectivity Must Go

1. **requests~=2.32.5 pin** — incompatible with HA 2026.x (`requests==2.33.1`). Blocks installation entirely.
2. **Sync dependency** — violates HA `async-dependency` Platinum rule.
3. **No `inject-websession`** — cannot share HA's aiohttp session.
4. **Upstream fragility** — one maintainer (@tillsteinbach), release pace unpredictable.
5. **No control** — we cannot fix bugs in our own integration if they live upstream.

---

*Last updated: 2026-04-12 | Prash Balan (@its-me-prash)*

---

## GraphQL & Vehicle Images (April 2026)

Die vollständige API-Knowledge-Base für den VW-Group GraphQL Layer (`vgql`)
und das `mediaservice.audi.com` Fahrzeugbilder-System ist dokumentiert in:

→ **[GRAPHQL_IMAGE_API.md](./GRAPHQL_IMAGE_API.md)**

Enthält: Auth-Flow, alle API-Endpoints, GraphQL-Schema, Response-Beispiele,
7 MediaTypes, Cross-Brand Endpoint-Matrix, Implementierungsstand.
