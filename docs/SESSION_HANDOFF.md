# VAG Connect HA — Session Handoff

> Living document. Updated at the end of every session so the next chat /
> contributor / maintainer has a single page to read.

Last updated: 2026-04-27 — End of mega-session (v1.8.0 → v1.8.5)

---

## Where to look first

| What | Where |
|---|---|
| Current sessioned roadmap | All 8 `README*.md` files (DE, EN, CS, ES, FR, NL, PL, SV) |
| Code audit + status by P0/P1 finding | [`docs/AUDIT_2026-04-26.md`](AUDIT_2026-04-26.md) |
| Active issues | https://github.com/its-me-prash/vag-connect-ha/issues |
| Brand & API ecosystem map | [`research/VAG_GROUP_ECOSYSTEM.md`](research/VAG_GROUP_ECOSYSTEM.md) |
| Image API | [`research/GRAPHQL_IMAGE_API.md`](research/GRAPHQL_IMAGE_API.md) |
| Out of scope brands | [`research/LUXURY_BRANDS.md`](research/LUXURY_BRANDS.md) + #77 (Ford Explorer Electric) |

---

## Current state — v1.8.5

```
Manifest:      version 1.8.5, iot_class cloud_polling
Tags:          v1.8.0, v1.8.1, v1.8.2, v1.8.3, v1.8.4, v1.8.5
Open issues:   27 (after closing #60, #68; #54 closed by user)
Open PRs:      0
CI:            all green (ruff + mypy strict + hassfest + HACS + pytest ≥65% coverage)
```

---

## Releases shipped this session

| Tag | Session | Key content |
|---|---|---|
| **v1.8.0** | Session 1 Foundation Fix | iot_class fix, per-VIN availability, S-PIN fail-fast, fake writables removed, reverse geocoding opt-in, PLATFORMS list sync (image+select) |
| **v1.8.1** | Privacy & Auth Polish | VIN masking (`mask_vin()` helper), diagnostics PII scrub (6 new fields), `ConfigEntryAuthFailed` on stale credentials (setup + poll loop), `userPosition` rationale documented |
| **v1.8.2** | Session 2A Foundation | `CommandFailureReason` enum (9 values), `classify_command_failure()` helper, `FeatureState` dataclass (3 orthogonal flags), capabilities cache (24h TTL), `SeatCupraClient.get_capabilities()`, SEAT/CUPRA OAuth scope broadened to match official apps |
| **v1.8.3** | Session 2B Button Gating | `vehicle_supports_capability()` three-valued helper, flash+wake buttons hidden for SEAT/CUPRA when capabilities say `False`, brand-scoped gating (only SEAT/CUPRA vocabulary verified), bilingual release notes generator |
| **v1.8.4** | Session 2C Lock Fix | SEAT/CUPRA SecToken flow for lock/unlock (pycupra-verified), `_get_sec_token()` helper, `SpinError` wrapper, coordinator lock now requires S-PIN for SEAT/CUPRA, `get_capabilities()` for CARIAD BFF (VW EU + Audi) + stubs for Porsche/VW NA |
| **v1.8.5** | Session 3A Command Profile | `CommandProfile` enum (12 values), coordinator `vehicle_command_profile` cache, VWEUClient `_post_command()` with per-VIN v1→v2 fallback on 404, 4 "set value" commands refactored (target_soc, climate_temp, charge_mode, min_soc), AudiClient inherits fix |

---

## Hard rules (NEVER violate)

1. **NEVER sign as Claude/AI** in commits, comments, releases, PR bodies
2. **EN-first bilingual** in all user-facing text (issue templates, comments, release notes)
3. **8 READMEs synchronized** at every version bump / roadmap change
4. **CHANGELOG bilingual** (EN first, DE below each section)
5. **VINs masked** everywhere (`mask_vin()` → `***` + last 6 chars) — never full VINs in logs, diagnostics, comments, prompts
6. **Car-friendly translations** (Lichthupe not Lichtsignal, Klimaanlage not Klimatisierung)
7. **Semver checked** before every bump — patch for bugfix, minor for new entities/features
8. **git pull before git tag** — tags must point at the merge commit, not the old HEAD
9. **Refresh PR page before clicking Merge** — race condition lost Session 2B once (#71 merged without 2B commit)
10. **`config_entry.options` is for user settings only** — capabilities, feature_states, command_profile go in coordinator runtime cache

---

## Architecture: key modules

| Module | Purpose |
|---|---|
| `cariad/exceptions.py` | `CommandFailureReason`, `CommandProfile`, `classify_command_failure()`, all exception classes |
| `cariad/_util.py` | `mask_vin()` privacy helper |
| `cariad/api/base.py` | `CariadBaseClient` with HTTP helpers, token refresh, `get_capabilities()` default |
| `cariad/api/vw_eu.py` | VW EU + (via inheritance) Audi: status, commands, capabilities, **v1→v2 fallback** |
| `cariad/api/seat_cupra.py` | SEAT/CUPRA OLA: status, commands, capabilities, **SecToken lock flow** |
| `cariad/api/skoda.py` | Škoda mysmob: status, commands |
| `cariad/api/porsche.py` | Porsche PPA: separate Auth0 auth, status, commands |
| `cariad/api/vw_na.py` | VW US/CA: separate IDK auth per country |
| `coordinator.py` | `FeatureState`, capabilities cache (24h TTL), `vehicle_command_profile`, `_trigger_reauth()`, per-VIN poll success, reverse geocoding opt-in |
| `button.py` | Flash+wake **capability-gated** for SEAT/CUPRA only, brand-scoped via `_BRANDS_WITH_CAPABILITY_GATING` |
| `diagnostics.py` | Recursive `_scrub()` with `_REDACT_KEYS` (10 PII fields), VIN masked in dict keys |
| `__init__.py` | `ConfigEntryAuthFailed` on invalid_credentials, `ConfigEntryNotReady` for other errors |

---

## Active live testers

| Issue | User | Vehicle | Status | Waiting for |
|---|---|---|---|---|
| **#53** | Gerhard2808 | CUPRA Born 2023 | **Paused** (NUC dead) | NUC repair, then v1.8.5 test |
| **#42** | migendi | CUPRA Formentor 2023 | **Silent** since v1.8.0 | User reply (subscription expired, limited testing possible) |
| **#51** | gleeballs | VW Tiguan 2022 UK | Free tier confirmed | v1.8.5 test (v1→v2 fallback might help some sensors) |
| **#54** | GitHobi | Škoda Octavia 2025 | **✅ Closed — all sensors working on v1.8.4!** | — |
| **#74** | Marco Grewe | VW Passat 2025 B9 | **New** — filed from Facebook | Debug log for PPE/PPC endpoint routing |
| **#75** | Christian Müller | Škoda Kodiaq Mk2 | **New** — filed from Facebook | Debug log for mysmob v3 garage endpoint |
| **#76** | Tobias Schmalzl | VW T6 Multivan 2016 | **New** — filed from Facebook | Command test + debug log (legacy MBB check) |

### Facebook-only testers (not on GitHub yet)

| User | Vehicle | Status |
|---|---|---|
| Richard Farmer | Ford Explorer Electric | Out of scope → `marq24/ha-fordpass` (#77) |
| Grant Shewan | Audi RS e-tron GT | Same as #51 — should test v1.8.5 |

---

## Next sessions (roadmap from READMEs)

| Session | Version | Scope | Depends on |
|---|---|---|---|
| **3B** | v1.8.6 | Lock/Climate/Charging v1→v2 fallback for Audi+VW EU; LEGACY_MBB profile for T6 Multivan | Tobias (#76) debug log |
| **3C** | v1.8.7 | SKODA_MYSMOB_V3 for Kodiaq Mk2; Škoda garage endpoint v3 fallback | Christian (#75) debug log |
| **4** | v1.8.8 | Diagnostics + Fixtures (#62): fixture-based regression tests, API tracing opt-in | Can start anytime |
| **5** | — | Process & Governance (#64): Brand Captains, CODEOWNERS, CONTRIBUTING.md | Can start anytime |
| **6** | v1.9.0 | Read-only mode, command locking, cloud/wake distinction (#63) | After Sessions 3–4 |
| **7** | v1.9.1 | Firebase FCM push for CUPRA/SEAT (#57) | Research done, needs impl |
| **8** | v1.9.2 | MQTT push for Škoda (#57) | After Session 7 |
| **9** | v1.10.0 | Feature batch: consumption data, charging history, departure timer UI, alarm sensors, charge profiles (#24, #35, #26, #33, #31, #25, #28, #36, #23) | After Sessions 6–8 |
| **10** | v2.0.0 | HACS default listing, compatibility matrix, EU Data Act prep (#13, #59) | Everything above |

---

## Cross-check audit results (ChatGPT 5.5 + Gemini Pro)

Both AIs independently agreed on these design principles which are now implemented:

1. **Foundation first, then behaviour** — error taxonomy before entity gating (Session 2A before 2B)
2. **Three different root causes** — `missing-capability` ≠ `expired-subscription` ≠ `free-tier-404`
3. **Don't create entity at all** (not `available=False`) for truly unsupported features
4. **Capabilities cached in coordinator runtime** — NOT in `config_entry.options`
5. **TTL-based refresh** (24h) + error-triggered re-fetch on `MISSING_CAPABILITY` or `WRONG_API_PROFILE`
6. **Conservative classifier** — ambiguous `400 internal-error` maps to `BACKEND_ERROR`, never `MISSING_CAPABILITY`
7. **`userPosition` in OLA honk-and-flash is the vehicle GPS** despite the parameter name — verified against pycupra + myskoda
8. **Rate limiting is the #1 enemy** of other VAG integrations — dynamic polling (Session 6) is critical

---

## How to start the next session

```
Read docs/SESSION_HANDOFF.md for full context.

Then check:
1. GitHub issues for new comments since 2026-04-27
2. git log origin/main --oneline -5  (verify v1.8.5 is HEAD)
3. Open issues needing attention: #53, #42, #51, #74, #75, #76

Pick the next session based on which live testers responded:
- If Marco (#74) or Tobias (#76) sent debug logs → Session 3B
- If Christian (#75) sent debug logs → Session 3C
- If nobody responded → Session 4 (Diagnostics + Fixtures)
- If user wants something else → ask
```

---

*Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0*
