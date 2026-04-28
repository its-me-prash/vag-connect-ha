# VAG Connect HA — Session Handoff

> Living document. Updated at the start of every session so the next chat /
> contributor / maintainer has a single page to read.

Last updated: 2026-04-29 — post v1.8.5 (Session 3A merged), pre v1.8.6/v1.8.7 hotfixes

---

## Where to look first

| What | Where |
|---|---|
| Current sessioned roadmap | [`docs/ROADMAP.md`](ROADMAP.md) (mirrors README) |
| Latest multi-source audit + session map | [`docs/AUDIT_2026-04-29.md`](AUDIT_2026-04-29.md) |
| Original P0/P1 audit (v1.8.0 baseline) | [`docs/AUDIT_2026-04-26.md`](AUDIT_2026-04-26.md) |
| Active issues | https://github.com/its-me-prash/vag-connect-ha/issues |
| Brand & API ecosystem map | [`research/VAG_GROUP_ECOSYSTEM.md`](research/VAG_GROUP_ECOSYSTEM.md) |
| Image API research (now known to be a dead-end officially) | [`research/GRAPHQL_IMAGE_API.md`](research/GRAPHQL_IMAGE_API.md) |
| Why no Bentley/Lamborghini | [`research/LUXURY_BRANDS.md`](research/LUXURY_BRANDS.md) |

---

## Current state — v1.8.5 (merged on `main`)

```
Branch:        main
Manifest:      version 1.8.5, iot_class cloud_polling
Quality scale: clean (CI publishes badges)
Open PRs:      none
Sessions done: 1 (v1.8.0), 2A/B/C (v1.8.1–v1.8.4), 3A (v1.8.5)
Next up:       v1.8.6 Docs Truthfulness  →  v1.8.7 Defensive Pass  →  Session 3B/3C/3S
```

### What changed since AUDIT_2026-04-26

| Tag | What |
|---|---|
| v1.8.0 | Foundation Fix — 7 P0 release blockers (#60) |
| v1.8.1 | Privacy & Auth Polish — VIN masking, ConfigEntryAuthFailed wiring |
| v1.8.2 | Session 2A — error taxonomy + 3-state feature model + capabilities cache (#68) |
| v1.8.3 | Session 2B — capability gating for SEAT/CUPRA flash + wake buttons |
| v1.8.4 | Session 2C — SEAT/CUPRA SecToken lock fix (#53, #68) |
| v1.8.5 | Session 3A — `CommandProfile` enum + CARIAD v1/v2 fallback (#51, #61, #74); 4 set-value commands ported |

### Strategic context (new since 2026-04-29 audit)

- `mitch-dc/volkswagen_we_connect_id` archived 2025-10-29 → marketplace gap
- `skodaconnect/homeassistant-skodaconnect` deprecated 2025-03-14 → successor `homeassistant-myskoda`
- tillsteinbach `WeConnect-*` → EOL 2026, ecosystem migrating to multi-brand `CarConnectivity-*`
- **vag-connect-ha is now structurally positioned as the active multi-brand successor** — to be reflected in v1.8.6 README

---

## Architecture map

```
custom_components/vag_connect/
  __init__.py          # PLATFORMS = 10 (sensor, binary_sensor, device_tracker,
                       # switch, button, climate, number, lock, image, select)
                       # NOTE: image platform may be removed/refactored in v1.10.0 — no official render API exists
  coordinator.py       # Poll loop, per-VIN vehicle_success, vehicle_capabilities
                       # (24h TTL), feature_states, vehicle_command_profile (in-memory)
                       # ServiceValidationError on missing S-PIN
                       # Reverse-geocoding behind enable_reverse_geocoding opt-in
  entity_base.py       # available property = per-VIN poll success
  config_flow.py       # Options flow exposes enable_reverse_geocoding
  cariad/
    auth/idk.py        # IDK PKCE — VW EU, Audi, Škoda (proprietary), SEAT, CUPRA, VW NA
    auth/porsche.py    # Auth0 PKCE — Porsche
    api/base.py        # Abstract client + per-VIN v1/v2 path memo
                       # → v1.8.7 will add centralised retry/backoff layer
    api/vw_eu.py       # CARIAD BFF + _post_command(vin, suffix) v1→v2 fallback
    api/audi.py        # Inherits VW EU + AZS token for vgql/render images
    api/skoda.py       # mysmob + camelCase token + proprietary token exchange
                       # → 3S will add /v3/garage fallback + carCapturedTimestamp
                       # connection-state computation
    api/seat_cupra.py  # OLA + CUPRA client_secret + honk-and-flash with userPosition
                       # SecToken-based lock/unlock (v1.8.4)
                       # → 3C will add /v5/users/{userID}/vehicles/{vin}/mycar
                       # for missing doors/windows/range entities
    api/porsche.py     # api.ppa.porsche.com
    api/vw_na.py       # VW US/CA UUID-based endpoints
    api/graphql.py     # vgql GraphQL for vehicle render images (Audi)
    exceptions.py      # APIError, AuthenticationError, RateLimitError, CommandProfile, ...
    models.py          # VehicleData, BrandConfig, TokenSet
```

Translation strings: English in `strings.json`, mirrored across
`translations/{de,en,cs,es,fr,nl,pl,sv}.json`.

---

## Sessioned roadmap (revised after 2026-04-29 audit)

| Session | Version | Scope | Issues |
|---|---|---|---|
| **v1.8.6** Docs Truthfulness | v1.8.6 | README + GitHub About truthful (`cloud_polling`, real entity count, fake-writables removed); position as successor to archived repos; clarify capability-gating + v1/v2 scope; image platform honest disclaimer; "Share my position" privacy note | partial #74 expectation alignment |
| **v1.8.7** Defensive Programming Pass | v1.8.7 | Centralised retry+backoff (2s/4s/8s/16s for 429/5xx); 6h stale-cache; 3-failure tolerance before Unavailable; strict 401/403/404/5xx discrimination; EULA repair-issue; generic-except audit; manifest version `>=` ranges | reduces support volume across many issues |
| **3B** | v1.8.8 | CARIAD v1/v2 fallback for `lock/unlock`, `climate_start/stop`, `charging_start/stop`; PPC/PPE graceful degradation (skip command entities, repair-issue, no endpoint guessing); optimistic-update + state-restoration | #51, #74 commands |
| **3C** _new_ | v1.8.9 | CUPRA `/v5/users/{userID}/vehicles/{vin}/mycar` for missing doors/windows/range; userID caching from `/v1/users/me`; pycupra bucket pattern (high/mid/low frequency); 404 → `/v2/.../status` fallback | Gerhard's CUPRA Born 19 entities |
| **3S** _new_ | v1.8.10 | Škoda mysmob v3: `/v3/garage` fallback for `/v2/garage` 403; `compute_connection_state()` via `carCapturedTimestamp` (`<30min` online / `<24h` standby / `>24h` offline); `binary_sensor.<vehicle>_connection`; GPS retention during `vehicle_in_motion` | #54, #75 |
| **4** Diagnostics + Fixtures | v1.9.0-pre | Diagnostics dump with `last_good_at`, `last_error_type`, `consecutive_failures`, `capability_404_endpoints`, `command_profile`, `device_platform`; fixtures from we_connect_id #165, myskoda #751, CC-seatcupra #49; VIN/userID/GPS masking | #62, #58 |
| **5** Process & Governance | — | Issue forms, brand captains, CODEOWNERS, privacy guide | #64 |
| **6** Read-only + Smart-Wake | v1.9.0 | Read-only mode; persistent wake counter (max 3/day); `wake_count_today` sensor; smart-wake guarded by `connectionState != online` AND time-since-user-action; **wake NEVER triggered automatically from coordinator** | #63, #55 |
| **7** Push CUPRA/SEAT | v1.9.1 | Firebase FCM via `mqtt.messagehub.de` | #57 |
| **8** Push Škoda | v1.9.2 | mysmob MQTT broker (Škoda-only — NOT portable to other brands) | #57 |
| **9** Trip Stats + Image refactor | v1.10.0 | Audi `tripstatistics/v1` schema portable to `cariad/api/trip_stats.py`; `TripStatistics` dataclass; aggregate-in-state convention; image platform → user-supplied URL or removal | #24, #35, #37 partial |
| **10** HACS Default + v2.0.0 | v2.0.0 | Live tests all brands, compatibility matrix, EU Data Act ready, multi-brand-successor positioning | #13, #59 |

> Strict order. Hotfixes v1.8.6 + v1.8.7 must merge before Session 3B/3C/3S.

---

## Known live issues (waiting on user verification with v1.8.5)

| Issue | User | Brand / Model | Status |
|---|---|---|---|
| #54 | @GitHobi | Škoda | **Pending Session 3S** — `carCapturedTimestamp` connection-state logic |
| #53 | @Gerhard2808 | CUPRA Born | Lock/Unlock fixed v1.8.4; **missing 19 entities pending Session 3C** (`/v5/.../mycar`) |
| #42 | @migendi | CUPRA Formentor 2023 | v1.6.x auth fix + better repair messages — verify on v1.8.5 |
| #51 | G.S. (Facebook) | Audi RS e-tron GT | 4 set-value commands fixed v1.8.5; **lock/climate/charging pending Session 3B** |
| #74 | @marcogrewe | VW Passat 2025 (B9) | Set-value commands fixed v1.8.5; status/clima/location debug pending Session 3B |
| #75 | (Kodiaq Mk2 reporter) | Škoda Kodiaq 2 (Mk2) | `/v2/garage` 403 — **pending Session 3S** (try `/v3/garage`) |
| #76 | @tobias-t6 | VW T6 Multivan 2016 | **Awaiting Tobias' logs** before any LEGACY_MBB routing — no speculative implementation |
| #77 | — | Ford Explorer Electric | **Out of scope** — uses FordPass, not CARIAD. Documented. |

---

## Useful constants (do not hardcode in tests; import from code)

```python
# Auth
IDK_BASE      = "https://identity.vwgroup.io"
CARIAD_BFF    = "https://emea.bff.cariad.digital"
AZS_TOKEN_URL = "https://emea.bff.cariad.digital/login/v1/audi/token"
OLA_BASE      = "https://ola.prod.code.seat.cloud.vwgroup.com"
SKODA_BASE    = "https://mysmob.api.connect.skoda-auto.cz"
PORSCHE_PPA   = "https://api.ppa.porsche.com"

# CUPRA confidential client (OAuth requires client_secret, unlike SEAT)
CUPRA_SECRET  = "eb8814e6…"  # see cariad/models.py BRAND_CUPRA

# Audi vgql via AZS token (NOT IDK bearer)
AZS_APP_API   = "app-api.live-my.audi.com"

# Reverse geocoding (opt-in)
NOMINATIM     = "https://nominatim.openstreetmap.org/reverse"

# Session 3C — CUPRA OLA additional endpoints (verified in pycupra/connection.py)
OLA_USER_ME      = f"{OLA_BASE}/v1/users/me"                # → userID, cache once
OLA_MYCAR        = f"{OLA_BASE}/v5/users/{{user_id}}/vehicles/{{vin}}/mycar"
OLA_MILEAGE      = f"{OLA_BASE}/v1/vehicles/{{vin}}/mileage"
OLA_PARKING      = f"{OLA_BASE}/v1/vehicles/{{vin}}/parkingposition"

# Session 9 — Audi Trip Statistics (verified in audi_connect_ha/audi_services.py:337)
AUDI_TRIPSTATS = "{home_region}/api/bs/tripstatistics/v1/vehicles/{vin}/tripdata/{kind}"
# kind ∈ {"longTerm", "shortTerm"}  — "cyclic" in API spec but not used by audi_connect_ha

# Session 10 (#59 EU Data Act) — pycupra already has reference implementation
EUDA_BASE = "https://eu-data-act.drivesomethinggreater.com"
EUDA_RELATIONS = f"{EUDA_BASE}/proxy_api/vum/v2/users/me/relations/{{vin}}"
# See pycupra/eudaconnection.py — saves us reverse-engineering when EU Data Act lands Sep 2026

# Session 3S — Škoda connection state (verified in homeassistant-myskoda)
# State derives from carCapturedTimestamp on every status sub-object:
#   age < 1800   s   →  online
#   age < 86400  s   →  standby
#   age >= 86400 s   →  offline
```

---

## Reference projects (clean-room, MIT/Apache-2.0)

| Project | Status | Used for |
|---|---|---|
| arjenvrh/audi_connect_ha | Active fork | AZS token exchange for Audi vgql |
| audiconnect/audi_connect_ha | Active | Trip statistics endpoint schema (Session 9) |
| robinostlund/homeassistant-volkswagencarnet | Active | VW EU endpoints reference; EULA repair pattern |
| skodaconnect/myskoda | Active | Škoda mysmob endpoints; `carCapturedTimestamp` logic |
| skodaconnect/homeassistant-myskoda | Active | Stale-cache pattern, wake limits, optimistic update |
| skodaconnect/homeassistant-skodaconnect | **Deprecated 2025-03** | Historical reference only |
| WulfgarW/pycupra | Active | SEAT/CUPRA OLA endpoints incl. `/v5/.../mycar` bucket pattern |
| WulfgarW/homeassistant-pycupra | Active | Live-test issue tracker |
| CJNE/pyporscheconnectapi | Active | Porsche Auth0 + PPA |
| matpoulin/CarConnectivity-connector-volkswagen-na | Active | VW US/CA endpoints |
| mitch-dc/volkswagen_we_connect_id | **Archived 2025-10-29** | Historical issue forensics (we have inherited their userbase) |
| tillsteinbach/CarConnectivity-* | Active | Multi-brand connector framework — ecosystem direction |

---

## Hard rules ("learnings" — do not repeat the bugs)

1. **Never sign as Claude or AI** — commits, comments, releases. Author lines and footers stay neutral.
2. **Bilingual user-facing text** — contributor's language first, translation below.
3. **README + 8 translations updated together** at every release.
4. **CHANGELOG entry per version** — CI fails the PR otherwise.
5. **VINs anonymised** — masked or example placeholders in code, docs, tests, fixtures. Same for userID and precise GPS.
6. **Car-friendly translations** — "Lichthupe", "Klimaanlage", "Zentralverriegelung" — drivers' language, not API jargon.
7. **Semver before bump** — patch = bug fix only, minor = new features, major = breaking change.
8. **Do not guess API behaviour** — verify against pycupra / myskoda / audi_connect_ha references and add the URL to the commit body.
9. **Never expose tokens, S-PIN, account IDs, precise GPS** — in logs, diagnostics, fixtures, issue bodies.
10. **Capability-first** — new entities check `capabilities` before being created.
11. **404 ≠ auth-fail** — capability missing for newer models is the most common cause. Strict status-code discrimination.
12. **Wake the car only on explicit user request** — never auto-trigger from coordinator. Persistent counter, max 3/day.
13. **Aggregate in state, JSON in attributes** — HA state limit is 255 chars. JSON-blob states will be truncated and break dashboards.
14. **Stale-but-visible > unavailable** on transient backend errors. 6h cache window.
15. **Do not endpoint-guess for PPC/PPE** — wait for upstream (acfischer42/CC-audi, tillsteinbach SeatCupra #49) before any blind requests against E³ 1.2 backends. Risks Audi account suspension.
