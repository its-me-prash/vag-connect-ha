# VAG Connect HA — Session Handoff

> **Living document.** Updated at the end of every release sprint so the
> next chat / contributor / AI tool has a single page that orients them
> in 5 minutes.

**Last updated:** 2026-04-29 — post v1.8.12 sprint (Multi-Brand
Connection-State live, 7 releases shipped today)

---

## Where to look first (5-minute orientation)

| What | Where |
|---|---|
| 🎯 Verified API facts archive | [`docs/RESEARCH_NOTES_2026-04-29.md`](RESEARCH_NOTES_2026-04-29.md) |
| 📜 Full technical changelog with citations | [`docs/CHANGELOG_TECHNICAL.md`](CHANGELOG_TECHNICAL.md) |
| 👥 Human-friendly release notes | [`../CHANGELOG.md`](../CHANGELOG.md) |
| 📋 Sessioned roadmap | [`docs/ROADMAP.md`](ROADMAP.md) (mirrors README) |
| 🐛 Active issues | https://github.com/its-me-prash/vag-connect-ha/issues |
| 🔬 Original P0/P1 audit (v1.8.0 baseline) | [`docs/AUDIT_2026-04-26.md`](AUDIT_2026-04-26.md) |
| 🔬 Multi-source audit + session map | [`docs/AUDIT_2026-04-29.md`](AUDIT_2026-04-29.md) |
| 🌍 Brand & API ecosystem | [`research/VAG_GROUP_ECOSYSTEM.md`](research/VAG_GROUP_ECOSYSTEM.md) |
| 🚫 Out-of-scope brands | [`research/LUXURY_BRANDS.md`](research/LUXURY_BRANDS.md) |

---

## Current state — v1.8.12 (released as Latest 2026-04-29 09:16 UTC)

```
Branch:           main
Manifest:         version 1.8.12, iot_class cloud_polling
Quality scale:    clean (CI publishes badges dynamically)
Open PRs:         none
Branch protection: ON — 5 required checks (Lint, Tests, Hassfest, HACS, CHANGELOG)
Latest tag:       v1.8.12 → released
Open issues:      22 (3 user live-tests pending verification, 19 roadmap)
```

### Releases shipped today (2026-04-29)

| Version | Title | New tests |
|---|---|---|
| v1.8.6 | Docs Truthfulness + Multi-Brand-Successor positioning | — |
| v1.8.7 | Defensive Programming Pass — retry, stale-cache, token guard | 12 |
| v1.8.8 | Session 3B — CARIAD v1/v2 lock/climate/charging | 4 |
| v1.8.9 | Session 3C — CUPRA OLA status JSON paths fix | 12 |
| v1.8.10 | Hotfix legacy doors fallback inversion | — |
| v1.8.11 | Session 3S — Škoda carCapturedTimestamp connection-state | 10 |
| **v1.8.12** | **MVP-Move — Multi-Brand connection-state (all 4 CARIAD brands)** | **12** |

Total: ~50 new tests, 7 releases, all CI-green, all merged + tagged.

### Process improvements (don't lose these)

- ✅ **Branch protection on `main`** — 5 required status checks
  (Lint, Unit Tests, HA Hassfest, HACS, CHANGELOG). Failing CI now
  blocks merge (lesson from v1.8.9 incident where failing test got
  merged because protection wasn't on)
- ✅ **CI watcher fallback** — `gh pr checks --watch` returns exit 0
  on "completed" (not "all green"). Always parse `gh pr checks <num>`
  explicitly: count non-SUCCESS conclusions before merging
- ✅ **`changelog_check.yml` triggers also on `CHANGELOG.md` and
  `docs/CHANGELOG_TECHNICAL.md`** — doc-only PRs no longer BLOCKED by
  required check that wouldn't run
- ✅ **CHANGELOG split** — `CHANGELOG.md` is human-friendly with emojis,
  `docs/CHANGELOG_TECHNICAL.md` has full technical detail with all
  issue/PR citations

---

## Architecture map (where to look in code)

```
custom_components/vag_connect/
├── __init__.py              PLATFORMS list = 10, service registration, setup hooks
├── coordinator.py           Own poll loop (NOT HA scheduler), per-VIN
│                            availability, capabilities cache, command profile,
│                            failure tolerance + 6h stale-cache (v1.8.7)
├── entity_base.py           VagConnectEntity — per-VIN availability check
├── config_flow.py           Setup + Options flow (reverse_geocoding opt-in)
├── const.py                 Brand IDs, conf keys
├── manifest.json            ⚠️  Single source of truth for version
├── strings.json             English source for translations
├── translations/{cs,de,en,es,fr,nl,pl,sv}.json   Mirror of strings.json
├── sensor.py                ~30 sensor descriptions, including
│                            connection_state (v1.8.11), vehicle_state
├── binary_sensor.py         ~16 binary sensors + per-door + per-window
│                            (v1.8.9 added windows_individual + VagWindowSensor)
├── switch.py, button.py, climate.py, number.py, lock.py, image.py,
│   select.py, device_tracker.py    Other 9 platforms
└── cariad/
    ├── _util.py             mask_vin (privacy) + compute_connection_state
    │                        (v1.8.12 — recursive timestamp walk, brand-agnostic)
    ├── exceptions.py        APIError, AuthenticationError,
    │                        TermsAndConditionsError, MarketingConsentError,
    │                        TwoFactorRequiredError, RateLimitError,
    │                        TokenExpiredError, SpinError, VehicleCommandError,
    │                        CommandProfile (12-value enum, v1.8.5),
    │                        CommandFailureReason (10-value enum, v1.8.2),
    │                        classify_command_failure() helper
    ├── models.py            BrandConfig (1 per brand), VehicleData (~80 fields)
    ├── factory.py           CariadClientFactory.create(brand, ...)
    ├── auth/
    │   ├── idk.py           IDK PKCE — VW EU, Audi, Škoda, SEAT, CUPRA, VW NA
    │   └── porsche.py       Auth0 PKCE — Porsche
    └── api/
        ├── base.py          CariadBaseClient — _request with v1.8.7 retry
        │                    layer; _post_command (v1/v2 fallback v1.8.5)
        ├── vw_eu.py         VWEUClient — selectivestatus parsing,
        │                    _post_command_with_fallback_paths (v1.8.8),
        │                    connection_state via helper (v1.8.12)
        ├── audi.py          AudiClient(VWEUClient) — AZS token + vgql GraphQL
        ├── skoda.py         SkodaClient — mysmob endpoints, detail block
        │                    (v1.8.11), reliableLockStatus, fullyChargedAt,
        │                    connection_state refactored to helper (v1.8.12)
        ├── seat_cupra.py    SeatCupraClient — OLA endpoints, SecToken lock
        │                    flow (v1.8.4), pycupra-style status paths (v1.8.9),
        │                    Live-API charging fields (v1.8.9),
        │                    connection_state via helper (v1.8.12)
        ├── porsche.py       PorscheClient — api.ppa.porsche.com
        ├── vw_na.py         VWNorthAmericaClient — VW US/CA
        └── graphql.py       VehicleImageFetcher — Audi vgql GraphQL only
```

### Reading order for a new contributor / AI tool

1. **This file** — orientation
2. [`docs/RESEARCH_NOTES_2026-04-29.md`](RESEARCH_NOTES_2026-04-29.md) —
   verified API facts, every claim cited
3. [`docs/CHANGELOG_TECHNICAL.md`](CHANGELOG_TECHNICAL.md) — what
   changed and why
4. `cariad/api/base.py` — request lifecycle, retry semantics
5. `cariad/_util.py:compute_connection_state` — example of clean,
   well-tested, brand-agnostic helper
6. `cariad/api/skoda.py` — most recent example of a brand client
   following all v1.8.x patterns

---

## Sessioned roadmap (next sessions)

| Session | Version | Scope | Issues |
|---|---|---|---|
| ~~1 — Foundation Fix~~ | ~~v1.8.0~~ | ✅ Done — 7 P0 release blockers | ✅ #60 |
| ~~2A — Capabilities Foundation~~ | ~~v1.8.2~~ | ✅ Done — error taxonomy + 3-state model + cache | ✅ #68 |
| ~~2B — Button gating~~ | ~~v1.8.3~~ | ✅ Done — SEAT/CUPRA flash/wake | ✅ partial #56 |
| ~~2C — SEAT/CUPRA Lock~~ | ~~v1.8.4~~ | ✅ Done — SecToken flow | ✅ #53 partial |
| ~~3A — Command Profile~~ | ~~v1.8.5~~ | ✅ Done — v1/v2 fallback for 4 set-value | ✅ #51, #61 done, #74 partial |
| ~~Docs Truthfulness~~ | ~~v1.8.6~~ | ✅ Done | ✅ |
| ~~Defensive Programming~~ | ~~v1.8.7~~ | ✅ Done — retry, stale-cache, token guard | ✅ |
| ~~3B — CARIAD v1/v2 main commands~~ | ~~v1.8.8~~ | ✅ Done — lock, unlock, climate, charging | ✅ #51, #74 |
| ~~3C — CUPRA OLA status fix~~ | ~~v1.8.9~~ | ✅ Done — Gerhard's 19 entities | ✅ #53 commands |
| ~~Hotfix~~ | ~~v1.8.10~~ | ✅ Done — legacy doors inversion | — |
| ~~3S — Škoda connection-state~~ | ~~v1.8.11~~ | ✅ Done — closes #54 | ✅ #54 |
| ~~MVP-Move — Multi-Brand connection-state~~ | ~~v1.8.12~~ | ✅ Done — VW EU + Audi + CUPRA + SEAT | — |
| **Vehicle Data Scout + Error Reporter** | v1.8.13 | Two new diagnostic sensors sharing one **Reporter Pipeline** for crowd-sourced bug discovery. (1) **Vehicle Data Scout** — logs JSON fields the parser doesn't read (mirrors tillsteinbach `CarConnectivity-*` "Unexpected Keys found" pattern, our richest source of API findings — CC-seatcupra #109, CC-skoda #50). User-facing name brand-localised (DE: "API-Beobachter", FR: "Détecteur de nouvelles données", etc.). (2) **Error Reporter** — captures last N Exceptions / API errors / stack traces from the integration with brand + model + firmware context. **Common Reporter Pipeline (1-click workflow, both sources):** detection → HA repair notification → user clicks "Mehr Info" → modal shows anonymised content + 2 buttons: `📤 Bug auf GitHub melden` (opens pre-filled GitHub issue) AND `📋 Copy für Forum/Facebook` (copies formatted Markdown to clipboard for non-GitHub users). Especially valuable for the Facebook community — non-technical users get a one-click way to share usable bug reports without learning Markdown or GitHub. ~30 sec end-to-end. NO auto-push to external servers (GDPR + HACS-Default + GitHub ToS); opt-in telemetry is a separate v1.9.x scope. Privacy: every value passes through `mask_vin`-style anonymisation. Implementation: `cariad/_unexpected_keys.py` + `cariad/_error_reporter.py` + shared `_reporter_pipeline.py` for HA-side modal/notifications + 8-language strings for buttons + brand-localised sensor names. | new |
| **Capability-Filter Phase 2** | v1.8.14 | `capability.active && capability.user-enabled` before entity creation. CC-seatcupra #64 pattern. | #56 |
| **Defensive Coding Phase 2** | v1.8.15 | Generic `except Exception` audit across all API clients. Enum tolerance for `CHARGING_INTERRUPTED`, `NOT_ACTIVATED`, `NO_UPDATE_AVAILABLE` etc. | #58 |
| **3B-Part-3 — Optimistic Lock/Climate** | v1.8.16 | myskoda #832 pattern — optimistic update + state restoration | — |
| **4 — Diagnostics + Fixtures** | v1.9.0-pre | Anonymized diagnostics export with `last_seen_at`, `command_profile`, `device_platform`, fixtures from CC-seatcupra #109, CC-skoda #50, volkswagencarnet #921 | #62, #58 |
| **5 — Process & Governance** | — | Issue forms, brand captains, CODEOWNERS, privacy guide | #64 |
| **6 — Read-only + Smart-Wake** | v1.9.0 | Read-only mode; persistent wake counter (max 3/day); `wake_count_today` sensor; **NEVER auto-wake**. Plus 12V drain detection from `connectionWarning.insufficientBatteryLevelWarning` (volkswagencarnet #940) | #63, #55, #23 |
| **7 — Push CUPRA/SEAT** | v1.9.1 | Firebase FCM via `mqtt.messagehub.de` | #57, #27 |
| **8 — Push Škoda** | v1.9.2 | mysmob MQTT broker (Škoda-only) | #57 |
| **9 — Trip Stats + Image refactor** | v1.10.0 | Audi `tripstatistics/v1` schema (verified audi_services.py:337); per-trip data model; image platform → user-supplied URL or removal | #24, #35, #36 |
| **10 — HACS Default + v2.0.0** | v2.0.0 | Live tests all brands, compatibility matrix, EU Data Act ready (pycupra `EUDAConnection` ready to port) | #13, #59 |

### Out-of-band (no fixed version yet)

- **PPC/PPE Plattform Support** for Audi 2025+ (Q5, A5/S5, A6 e-tron,
  Q6 e-tron, RS e-tron GT Facelift) — depends on public reverse-engineering
  by audi_connect_ha or CC-audi. Currently graceful degradation only.
  See [`docs/AUDIT_2026-04-29.md`](AUDIT_2026-04-29.md) for status.
- **LEGACY_MBB Routing** for VW T6 Multivan 2016 (#76) — blocked on
  Tobias' diagnostic logs. No speculative implementation.
- **Skoda Kodiaq Mk2 `/v2/garage` 403** (#75) — likely
  `connectivityGenerations: ["MOD5"]` needed; `/v3/garage` does not exist
  (verified). Awaiting User diagnostics.

---

## Known live issues (waiting on user verification with v1.8.12)

| Issue | User | Brand / Model | Status |
|---|---|---|---|
| #54 | @GitHobi | Škoda | ✅ Should be fixed by v1.8.11 connection_state — **awaiting verification** |
| #53 | @Gerhard2808 | CUPRA Born | ✅ 5 fixes flowed in (v1.8.4, 1.8.8, 1.8.9, 1.8.10, 1.8.12) — **awaiting verification** |
| #42 | @migendi | CUPRA Formentor | ✅ Same fix bundle as #53 — **awaiting verification** |
| #51 | G.S. (Facebook) | Audi RS e-tron GT | ✅ pre-Facelift fixed by v1.8.5/8; Facelift via graceful degradation only |
| #74 | @marcogrewe | VW Passat 2025 (B9) | ✅ Set-value + main commands fixed by v1.8.5/8/12 — **awaiting verification** |
| #75 | (Kodiaq Mk2) | Škoda Kodiaq 2 (Mk2) | ⏳ `/v2/garage` 403, `/v3/garage` doesn't exist — needs diagnostic dump |
| #76 | @tobias-t6 | VW T6 Multivan 2016 | ⏳ awaiting Tobias' logs before any LEGACY_MBB routing |

---

## Hard rules ("learnings" — do not repeat the bugs)

1. **Never sign as Claude or AI** — commits, comments, releases. Author lines and footers stay neutral.
2. **Bilingual user-facing text** — contributor's language first, translation below.
3. **README + 8 translations updated together** at every release.
4. **CHANGELOG entry per version** — CI fails the PR otherwise.
5. **VINs anonymised** — masked or example placeholders in code, docs, tests, fixtures. Same for userID and precise GPS.
6. **Car-friendly translations** — "Lichthupe", "Klimaanlage", "Zentralverriegelung" — drivers' language, not API jargon.
7. **Semver before bump** — patch = bug fix only, minor = new features, major = breaking change.
8. **Do not guess API behaviour** — verify against `pycupra` / `myskoda` / `audi_connect_ha` / `volkswagencarnet` references and add the URL to the commit body.
9. **Never expose tokens, S-PIN, account IDs, precise GPS** — in logs, diagnostics, fixtures, issue bodies.
10. **Capability-first** — new entities check `capabilities` before being created.
11. **404 ≠ auth-fail** — capability missing for newer models is the most common cause. Strict status-code discrimination.
12. **Wake the car only on explicit user request** — never auto-trigger from coordinator. Persistent counter, max 3/day.
13. **Aggregate in state, JSON in attributes** — HA state limit is 255 chars. JSON-blob states will be truncated and break dashboards.
14. **Stale-but-visible > unavailable** on transient backend errors. 6h cache window.
15. **Do not endpoint-guess for PPC/PPE** — wait for upstream (audi_connect_ha, acfischer42/CC-audi, tillsteinbach SeatCupra #49) before any blind requests against E³ 1.2 backends. Risks Audi account suspension.
16. **CI explicit-check before merge** — `gh pr checks <num>` must show 0 non-SUCCESS conclusions. Don't trust `--watch` exit codes alone (lesson from v1.8.9 ship-with-failing-test).
17. **Doc-only PRs without code change** — no manifest bump, but CHANGELOG.md change still triggers `changelog_check.yml` (since v1.8.12 workflow extension).

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

# Connection-state thresholds (v1.8.12 — universal across brands)
CONNECTION_ONLINE_THRESHOLD_S  = 1800   # < 30 min
CONNECTION_STANDBY_THRESHOLD_S = 86400  # < 24 h; older = "offline"
```

---

## Reference projects (clean-room, MIT/Apache-2.0)

For full attribution and "what to look up where" matrix, see
[`docs/RESEARCH_NOTES_2026-04-29.md`](RESEARCH_NOTES_2026-04-29.md)
section 4. Quick summary:

| Project | Status | Used for |
|---|---|---|
| `arjenvrh/audi_connect_ha` | active fork | AZS token exchange |
| `audiconnect/audi_connect_ha` | active | Trip statistics + audi_models.py reference |
| `robinostlund/homeassistant-volkswagencarnet` | active | VW EU patterns; EULA repair pattern; Service Discovery |
| `skodaconnect/myskoda` | active | mysmob endpoints; `carCapturedTimestamp` |
| `skodaconnect/homeassistant-myskoda` | active | Stale-cache UX, wake limits |
| `skodaconnect/homeassistant-skodaconnect` | **deprecated 2025-03** | Historical reference only |
| `WulfgarW/pycupra` | active | OLA endpoints, `EUDAConnection` (EU Data Act ready) |
| `WulfgarW/homeassistant-pycupra` | active | Live-test issue tracker |
| `CJNE/pyporscheconnectapi` | active | Porsche Auth0 + PPA |
| `matpoulin/CarConnectivity-connector-volkswagen-na` | active | VW US/CA |
| `mitch-dc/volkswagen_we_connect_id` | **archived 2025-10-29** | Historical issue forensics — we are the active successor |
| `tillsteinbach/CarConnectivity-*` | active | Multi-brand connector ecosystem direction |

---

## How to start the next session (recipe for a fresh AI / contributor)

1. Read this file (top to bottom, ~10 min)
2. Read [`docs/RESEARCH_NOTES_2026-04-29.md`](RESEARCH_NOTES_2026-04-29.md)
   sections 1, 2, 3, 6 (~20 min)
3. Pick a session from the "Sessioned roadmap" above
4. Verify the source(s) for that session in
   [`docs/RESEARCH_NOTES_2026-04-29.md`](RESEARCH_NOTES_2026-04-29.md)
   section 4
5. If anything is unclear or unverified: spawn a research agent against
   the relevant reference repo (recipe in `RESEARCH_NOTES` section 7)
6. Implement on a branch named `claude/v1.8.X-session-name` from `main`
7. Add tests (target: 5-12 new per session)
8. CHANGELOG entry: human-friendly in `CHANGELOG.md`, full technical in
   `docs/CHANGELOG_TECHNICAL.md`
9. Manifest bump (only if code changed)
10. PR + watch CI explicitly (`gh pr checks <num>`, count non-SUCCESS)
11. Merge with `gh pr merge --merge --delete-branch` (don't squash —
    we keep individual commits for git-blame archaeology)
12. Tag the merge commit: `git tag v1.8.X $MERGE_SHA && git push origin v1.8.X`
13. After tag-push the release workflow auto-publishes; if needed:
    `gh release edit v1.8.X --draft=false --latest`
14. Update relevant open issues with "Fixed in v1.8.X — please verify"
15. Update this file's "Current state" + "Releases shipped today" + roadmap
