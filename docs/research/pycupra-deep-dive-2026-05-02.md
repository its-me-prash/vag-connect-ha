# pycupra Deep-Research Sweep — Findings for vag-connect-ha

> **Sources:** `WulfgarW/pycupra` (`pycupra/{const,connection,vehicle,utilities,exceptions,firebase}.py`)
> + `WulfgarW/homeassistant-pycupra` (`__init__.py`, `const.py`, `config_flow.py`)
> **Created:** 2026-05-02 (post v1.16.1, during v1.17.0 planning)
> **Status:** Reference document — items below cross-tracked into ROADMAP.

## A) High-priority adopt (S/M complexity)

| # | Item | Source | Target |
|---|---|---|---|
| 1 | **`utilities.find_path()` / `is_valid_path()`** — dot-notation safe traversal returning `""` instead of raising. Eliminates dozens of nested `.get(...).get(...)` chains in our SEAT/CUPRA/Skoda clients. | `pycupra/utilities.py` | v1.17.x (port as `vag_connect/cariad/_safe_path.py`) |
| 2 | **`PyCupra*Exception` taxonomy** — especially `PyCupraThrottledException` (HTTP 429 with "start the car to reset" hint), `PyCupraRequestInProgressException`, `PyCupraEULAException`, `PyCupraMarketingConsentException`. | `pycupra/exceptions.py` | v1.17.x (extend our `cariad/exceptions.py`) |
| 3 | **OLA token refresh endpoint** = `https://ola.prod.code.seat.cloud.vwgroup.com/authorization/api/v1/token` (separate from `identity.vwgroup.io/oidc/v1/token` used for initial). With `asyncio.Lock` around `set_token()`. | `pycupra/connection.py::AUTH_REFRESH` | v1.17.x — verify our SEAT/CUPRA token refresh path uses the right endpoint |
| 4 | **Per-action 429 surface** with `persistent_notification` + 120s auto-dismiss. | pycupra `async_show_pycupra_notification` | v1.17.x |
| 5 | **`X-RateLimit-Remaining` extraction** in `_request()` → expose as diagnostic sensor `requests_remaining_today`. | pycupra `_request()` header parsing | v1.17.x |
| 6 | **Capability-parameter sub-flags** — read `capa['parameters']['supportsTargetStateOfCharge']` etc. We currently gate at cap-id only. | pycupra `vehicle.py` capability checks | v1.17.x |
| 7 | **Push (FCM) plumbing** — `firebase_messaging.FcmPushClient` + `FcmRegisterConfig(project_id, app_id, api_key, sender_id)`, persisted creds via `onFCMCredentialsUpdated`. CUPRA `FCM_APP_ID = 1:530284123617:android:9b9ba5a87c7ffd37fbeea0`, SEAT `…:d6187613ac3d7b08fbeea0`. | `pycupra/firebase.py` + `connection.py::_getFirebaseConfig` | **v1.18.0 Push Bundle** |
| 8 | **Bucket-flag-style refresh** (single coordinator, per-key TTL flags) — simpler than 3 separate coordinators, retrofit-friendly. | pycupra HA integration `__init__.py` | v1.17.x or own bundle (medium-size) |

## B) Medium-priority defensive patterns

- **Nightly reduction window 22:00–05:00** → halve poll cadence (`CONF_NIGHTLY_UPDATE_REDUCTION`). _We already have this unconditionally; should make it configurable._
- **Firebase-on extends full-update window 1100s → 1700s** (push covers gap).
- **`getCharger()` merges 3 endpoints** (`/charging/status`, `/charging/info`, `/charging/profiles`) into one cached blob — adopt for our charging client to reduce poll fanout.
- **`getPosition()` 204 handling** = vehicle in motion. We currently treat as error in places.
- **`setWantedStateOfProperty()` + `checkForRunningRequests('batterycharge')`** — track pending command vs current state to prevent duplicate POSTs and to drive an "operation pending" sensor.
- **`utilities.convertTimerUtcToLocal()`** for departure/climater timers.

## C) Skip / not applicable

- **EUDA endpoints** (`/proxy_api/euda-apim/...`) — EU data-delivery; SEAT/CUPRA only and requires consent flow we don't want to implement.
- **`API_LITERALS` (`/v1/content/apps/my-cupra/literals/{language}`)** — translation strings for MyCUPRA UI; not useful for HA.
- **Cross-endpoint battery-0% fallback** — searched both repos; **not present** in pycupra. pycupra logs warnings independently per endpoint. **Our existing fallback is already ahead.**
- **Single-coordinator simplicity** — pycupra HA uses ONE coordinator, not buckets. We already have multiple async helpers (refresh_trip_statistics, refresh_charging_history, refresh_charging_profiles); don't downgrade to single coordinator.

## D) New OLA endpoints discovered (catalog)

All under `{baseurl} = https://ola.prod.code.seat.cloud.vwgroup.com` unless noted.

### Already in our `seat_cupra.py`

- `GET /v5/users/{userId}/vehicles/{vin}/mycar` ✅
- `GET /v1/vehicles/{vin}/parkingposition` ✅
- `GET /v1/vehicles/{vin}/ranges` ✅
- `GET /v2/vehicles/{vin}/status` ✅
- `GET /v1/vehicles/{vin}/charging/status` ✅
- `GET /v1/vehicles/{vin}/charging/info` ✅
- `GET /v2/vehicles/{vin}/climatisation` ✅ (now with `/start|/stop` suffix from v1.16.1)
- `GET /v1/vehicles/{vin}/maintenance` ✅
- `GET /v1/vehicles/{vin}/remote-availability` ✅
- `GET /v1/vehicles/{vin}/capabilities` ✅
- `GET /v2/vehicles/{vin}/renders` ✅
- `POST /v1/vehicles/{vin}/honk-and-flash` ✅
- `POST /v1/vehicles/{vin}/access/{lock|unlock}` ✅ (with SecToken)
- `POST /v1/vehicles/{vin}/charging/actions` ✅

### New / not yet integrated

- `GET /v1/vehicles/{vin}/mileage` — `mileageKm` (we have it via `mycar` aggregate; standalone might be cheaper)
- `GET /v3/vehicles/{vin}/warninglights` — service warnings (`statuses`)
- `GET /v1/vehicles/{vin}/measurements/engines` — live engine telemetry
- `GET /v1/vehicles/{vin}/climatisation/status` (separate from settings)
- `GET /v2/vehicles/{vin}/climatisation/settings`
- `GET /vehicles/{vin}/climatisation/timers`
- `GET /v1/vehicles/{vin}/departure-timers` — discrete timers
- `GET /v1/vehicles/{vin}/departure/profiles` — saved profiles
- `GET /v2/vehicles/{vin}/driving-data/CUSTOM?from=...` — trip stats (we have BFF version; this is OLA equivalent)
- `GET /v1/vehicles/{vin}/driving-data/{dataType}` — legacy v1 trips per type
- `GET /v1/shop/vehicles/{vin}/articles` — purchasable services catalog
- `GET /v1/users/{userId}/vehicles/{vin}/relation-status` — primary user / dealer-mode flag
- `GET /v1/user/{userId}/invitations` — pending vehicle-share invites
- `GET /v2/users/{userId}/vehicles/{vin}/psp` — paired smart products / chargers
- `POST /v1/vehicles/{vin}/vehicle-wakeup/request` — explicit wake (we have variant)
- `POST /v2/users/{userId}/spin/verify` — S-PIN sec-token mint
- `PUT /v1/users/vehicles/{vin}/destination` — send POI to nav (closes #36 — Navigation: Ziel ans Auto senden)
- `POST /v1/vehicles/{vin}/auxiliary-heating/{start|stop}` — Webasto with SecToken
- Generic action wrappers: `POST /vehicles/{vin}/{capability}/requests/{start|stop}` and `/v1/vehicles/{vin}/{capability}/actions/{update-*}`
- User-info: `GET https://identity-userinfo.vwgroup.io/oidc/userinfo`
- Customer profile (non-OLA): `https://customer-profile.vwgroup.io/v3/customers/{userId}/{personalData|mbbStatusData}`

## E) Bucket polling pseudo-code (TTL-flag style)

Saved here for future bucket-polling refactor session:

```python
BUCKET_TTL = {1: 120, 2: 600, 3: 1800}  # seconds: live / standard / nightly
BUCKET_OF = {
    "status": 1, "position": 1, "charging": 1, "climatisation": 1,
    "mileage": 2, "ranges": 2, "warninglights": 2, "measurements": 2,
    "maintenance": 3, "trips": 3, "shop": 3, "capabilities": 3,
}

class VagCoordinator(DataUpdateCoordinator):
    def __init__(...):
        self._last: dict[str, datetime] = {}
        self._force_next: set[str] = set()
        self.update_interval = timedelta(seconds=60)  # tick

    def _due(self, key: str) -> bool:
        if key in self._force_next: return True
        ttl = BUCKET_TTL[BUCKET_OF[key]]
        if self._nightly_reduction and (22 <= now().hour or now().hour < 5):
            ttl *= 2
        if self._push_active and BUCKET_OF[key] == 1:
            ttl *= 3  # push covers it
        return (now() - self._last.get(key, EPOCH)).total_seconds() >= ttl

    async def _async_update_data(self):
        async with self._vin_lock:
            for key in BUCKET_OF:
                if not self._cap_ok(key): continue
                if not self._due(key): continue
                try:
                    self.data[key] = await self._fetch(key)
                    self._last[key] = now()
                except PyCupraThrottledException:
                    self._notify_throttle(key)
        self._force_next.clear()
        return self.data

    def force_refresh(self, key: str | None = None):
        self._force_next.update(BUCKET_OF if key is None else {key})
        self.async_request_refresh()
```

## F) Push notification dispatcher template (v1.18.0 prep)

```python
class VagPushDispatcher:
    HANDLERS = {
        "vehicle-charging-status": "_on_charging_change",
        "vehicle-charging-completed": "_on_charging_change",
        "vehicle-climatisation-status": "_on_climater_change",
        "vehicle-locked": "_on_access_change",
        "vehicle-unlocked": "_on_access_change",
        "vehicle-honk-and-flash": "_on_command_ack",
    }

    async def on_fcm_message(self, payload: dict, persistent_id: str):
        msg_type = payload.get("data", {}).get("type", "")
        vin = payload.get("data", {}).get("vin")
        if vin not in self._coordinators:
            _LOGGER.debug("push for unknown VIN %s", vin); return
        handler = self.HANDLERS.get(msg_type, "_on_unknown")
        try:
            await getattr(self, handler)(vin, payload)
        except Exception as e:
            _LOGGER.warning("push handler %s failed: %s", handler, e)

    async def _on_unknown(self, vin, payload):
        _LOGGER.info("unhandled push type=%s vin=%s",
                     payload["data"].get("type"), vin)
        self._coordinators[vin].force_refresh()  # full sweep as fallback
```

Register via `firebase_messaging.FcmPushClient(callback=on_fcm_message,
FcmRegisterConfig(project_id, FCM_APP_ID[brand], api_key, sender_id))`,
persist creds with `onFCMCredentialsUpdated` writing to
`.storage/vag_connect_fcm_{brand}.json`.

## G) Open questions for follow-up research

1. **FCM project_id / api_key / sender_id** for SEAT/CUPRA — pycupra reads them at runtime from a server-provided config endpoint we didn't fully trace. Need to inspect `_getFirebaseConfig()` in `connection.py`.
2. **Exact push `data.type` strings** — `firebase.py` defers to upstream `firebase_messaging`; the type taxonomy lives in observed payloads only. Need a real device sample.
3. **`setRefresh` / vehicle-wakeup quota** — pycupra surfaces 429 but doesn't document the daily budget; needs empirical capture in our wake-budget tracker.

## Mapping into ROADMAP

- **A1** (find_path port) — quick add to v1.17.x
- **A2** (exception taxonomy) — quick add to v1.17.x
- **A3** (token refresh endpoint check) — verify in v1.17.x
- **A4** (429 notification with auto-dismiss) — v1.17.x
- **A5** (`requests_remaining_today` sensor) — v1.17.x
- **A6** (capability sub-parameters) — v1.17.x
- **A7** (FCM push) — **v1.18.0 Push Bundle** (was already planned)
- **A8** (bucket polling) — own bundle, **v1.19.0 or v2.0.0 prep**
- **D** (new OLA endpoints) — pick + integrate per-feature need
  - Notably: `PUT /v1/users/vehicles/{vin}/destination` closes **#36 Navigation**
  - `POST /v1/vehicles/{vin}/auxiliary-heating/{start|stop}` is a new feature ask
- **E** + **F** are template stubs for future sessions
