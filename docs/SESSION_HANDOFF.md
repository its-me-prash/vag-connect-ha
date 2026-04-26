# VAG Connect HA — Session Handoff

> Living document. Updated at the start of every session so the next chat /
> contributor / maintainer has a single page to read.

Last updated: 2026-04-26 — Session 1 (v1.8.0 PR #65)

---

## Where to look first

| What | Where |
|---|---|
| Current sessioned roadmap | [`docs/ROADMAP.md`](ROADMAP.md) (mirrors README) |
| Code audit + status by P0/P1 finding | [`docs/AUDIT_2026-04-26.md`](AUDIT_2026-04-26.md) |
| Active issues | https://github.com/its-me-prash/vag-connect-ha/issues |
| Active PR | https://github.com/its-me-prash/vag-connect-ha/pull/65 |
| Brand & API ecosystem map | [`research/VAG_GROUP_ECOSYSTEM.md`](research/VAG_GROUP_ECOSYSTEM.md) |
| Image API | [`research/GRAPHQL_IMAGE_API.md`](research/GRAPHQL_IMAGE_API.md) |
| Why no Bentley/Lamborghini | [`research/LUXURY_BRANDS.md`](research/LUXURY_BRANDS.md) |

---

## Current state — v1.8.0 (in PR #65)

```
Branch:        claude/analyze-test-coverage-gG3d8
Manifest:      version 1.8.0, iot_class cloud_polling
Quality scale: cleaned (no more hardcoded numbers — CI publishes badges)
Open issues:   #56–#64 (P1 work for Sessions 2–6) + user bugs #42, #51, #53, #54
```

### CI status (last run on commit `caf050a`)

| Check | Status |
|---|---|
| Lint & Validate (ruff + mypy strict + manifest + JSON + CHANGELOG check) | ✅ green |
| HA Hassfest | ✅ green |
| HACS Validation | ✅ green |
| CHANGELOG.md aktualisiert? | ✅ green |
| Unit Tests + Coverage | 🔧 Two tests being fixed — `test_seat_commands` and `test_async_unlock_passes_spin` (both consequences of the v1.8.0 behaviour changes; tests now updated to match) |

If Tests still fail after the next push, the `pytest-output` artifact uploaded by the workflow contains the full traceback.

---

## Architecture map

```
custom_components/vag_connect/
  __init__.py          # PLATFORMS = 10 (sensor, binary_sensor, device_tracker,
                       # switch, button, climate, number, lock, image, select)
  coordinator.py       # Poll loop, per-VIN vehicle_success tracking,
                       #   ServiceValidationError on missing S-PIN,
                       #   reverse-geocoding behind enable_reverse_geocoding opt-in
  entity_base.py       # available property = per-VIN poll success
  config_flow.py       # Options flow now exposes enable_reverse_geocoding
  cariad/
    auth/idk.py        # IDK PKCE — VW EU, Audi, Škoda (proprietary), SEAT, CUPRA, VW NA
    auth/porsche.py    # Auth0 PKCE — Porsche
    api/base.py        # Abstract client; command_flash signature now accepts
                       #   latitude/longitude kwargs (only SEAT/CUPRA use them)
    api/vw_eu.py       # CARIAD BFF
    api/audi.py        # CARIAD BFF + AZS token for vgql/render images
    api/skoda.py       # mysmob + camelCase token + proprietary token exchange
    api/seat_cupra.py  # OLA + CUPRA client_secret + honk-and-flash with userPosition
    api/porsche.py     # api.ppa.porsche.com
    api/vw_na.py       # VW US/CA UUID-based endpoints
    api/graphql.py     # vgql GraphQL for vehicle render images (Audi confirmed)
    exceptions.py      # APIError, AuthenticationError, RateLimitError, ...
    models.py          # VehicleData, BrandConfig, TokenSet
```

Translation strings: English in `strings.json`, mirrored across
`translations/{de,en,cs,es,fr,nl,pl,sv}.json`.

---

## What changed in this session (v1.8.0 PR #65)

7 P0 release blockers identified by an independent audit, all fixed in one
atomic PR. See [`docs/AUDIT_2026-04-26.md`](AUDIT_2026-04-26.md) for the
full table. Highlights:

- Per-VIN availability tracking (was: all vehicles flashed `success=True`)
- S-PIN fail-fast with `ServiceValidationError(spin_required)`
- Removed `max_charge_current`, `seat_heating_switch`, `auto_unlock_switch`
  entities (they only logged or mutated internal state)
- Reverse geocoding off by default — opt-in via `enable_reverse_geocoding`
- `iot_class` corrected to `cloud_polling`
- `image` and `select` platforms actually loaded now (and use
  `entry.runtime_data` instead of the old `hass.data[DOMAIN]` lookup)

Plus a bug fix for #53: CUPRA/SEAT honk-and-flash payload was wrong —
needs `{"mode": "flash", "userPosition": {…}}`, not `{"mode": "FLASH_ONLY"}`.

---

## Sessioned roadmap (next steps)

| Session | Version | Scope |
|---|---|---|
| 1 — Foundation Fix | v1.8.0 | **Current** — PR #65 awaiting CI green + merge |
| 2 — Capabilities | v1.8.1 | #56 — capability-gated entity creation |
| 3 — Command Profile | v1.8.2 | #61 + #51 — fixes Audi RS e-tron GT 404 |
| 4 — Diagnostics + Fixtures | v1.8.3 | #62 + #58 — anonymised diagnostics, regression tests |
| 5 — Process & Governance | — | #64 — issue forms, brand captains, CODEOWNERS |
| 6 — Read-only + Locking | v1.9.0 | #63 + #55 — read-only mode, command lock, smart wake-up |
| 7 — Push CUPRA/SEAT | v1.9.1 | #57 — Firebase FCM via mqtt.messagehub.de |
| 8 — Push Škoda | v1.9.2 | #57 — MQTT broker integration |
| 9 — Feature batch | v1.10.0 | #24, #35, #26, #33, #31 — trip stats, charging history, etc. |
| 10 — HACS Default + v2.0.0 | v2.0.0 | #13, #59 — live tests all brands, EU Data Act ready |

> Strict order. Sessions 1–4 must merge before any new features land.

---

## Known live issues (waiting on user verification with v1.8.0)

| Issue | User | Brand / Model | What changed in v1.8.0 |
|---|---|---|---|
| #54 | @GitHobi | Škoda | Per-VIN availability + JSON path fixes still in place |
| #53 | @Gerhard2808 | CUPRA Born | `command_flash` payload fix → should work after one status poll caches GPS |
| #42 | @migendi | CUPRA Formentor 2023 | Same v1.6.x auth fix + better repair messages |
| #51 | G.S. (Facebook) | Audi RS e-tron GT | **Not yet fixed** — Session 3 (#61) command profile layer |

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
```

---

## Reference projects (clean-room, MIT/Apache-2.0)

| Project | Used for |
|---|---|
| arjenvrh/audi_connect_ha | AZS token exchange for Audi vgql |
| robinostlund/homeassistant-volkswagencarnet | VW EU endpoints reference |
| skodaconnect/myskoda | Škoda mysmob endpoints |
| WulfgarW/pycupra | SEAT/CUPRA OLA endpoints + honk-and-flash payload |
| CJNE/pyporscheconnectapi | Porsche Auth0 + PPA |
| matpoulin/CarConnectivity-connector-volkswagen-na | VW US/CA endpoints |

---

## Hard rules ("learnings" — do not repeat the bugs)

1. **Never sign as Claude or AI** — commits, comments, releases. Author lines and footers stay neutral.
2. **Bilingual user-facing text** — contributor's language first, translation below.
3. **README + 8 translations updated together** at every release.
4. **CHANGELOG entry per version** — CI fails the PR otherwise.
5. **VINs anonymised** — masked or example placeholders in code, docs, tests, fixtures.
6. **Car-friendly translations** — "Lichthupe", "Klimaanlage", "Zentralverriegelung" — drivers' language, not API jargon.
7. **Semver before bump** — patch = bug fix only, minor = new features, major = breaking change.
8. **Do not guess API behaviour** — verify against pycupra / myskoda / audiconnect references and add the URL to the commit body.
9. **Never expose tokens, S-PIN, account IDs, precise GPS** — in logs, diagnostics, fixtures, issue bodies.
10. **Capability-first** — new entities check `capabilities` before being created (Session 2 #56 onwards).
