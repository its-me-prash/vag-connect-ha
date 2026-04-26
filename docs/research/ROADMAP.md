# VAG Connect — Research Roadmap (archive)

> This file used to plan releases up to v0.14.x. The canonical session-based
> roadmap now lives in [`docs/ROADMAP.md`](../ROADMAP.md) and mirrors the
> README tables in all 8 languages.

Last updated: 2026-04-26

---

## Why this file is now an archive

The original plan in this folder targeted v0.15 (Porsche), v0.16 (VW NA),
and v0.17 (feature expansion). All three goals shipped in v1.0.0.
Subsequent planning moved into the README and individual GitHub issues.

For historical context the original v0.x roadmap is preserved at the
bottom of this file. For current planning, see:

- **Canonical roadmap:** [`docs/ROADMAP.md`](../ROADMAP.md) and the README
- **Active issues:** https://github.com/its-me-prash/vag-connect-ha/issues
- **Session 1 PR:** https://github.com/its-me-prash/vag-connect-ha/pull/65

---

## Current research status

| Topic | Status | Source |
|---|---|---|
| VAG group ecosystem map | Active | [`VAG_GROUP_ECOSYSTEM.md`](VAG_GROUP_ECOSYSTEM.md) |
| GraphQL vehicle image API | Active | [`GRAPHQL_IMAGE_API.md`](GRAPHQL_IMAGE_API.md) |
| Luxury / non-API brands | Documented (no implementation) | [`LUXURY_BRANDS.md`](LUXURY_BRANDS.md) |
| EU Data Act 2026 | Tracking only | Issue #59 |
| Firebase / MQTT push | Research planned | Issue #57 (Sessions 7–8) |
| Capabilities check | Implementation planned | Issue #56 (Session 2) |
| Command profile layer | Implementation planned | Issue #61 (Session 3) |

---

## Original v0.x roadmap (archive)

Kept for context only. All items below are **shipped**:

- v0.15.0 — Porsche support → shipped in v1.0.0
- v0.16.0 — VW US/CA support → shipped in v1.0.0
- v0.17.0 — Feature expansion (trip stats, charging history, etc.) → partially shipped, remainder tracked in #11/#18/#24/#35
- v1.0.0 — HACS official → blocked on live tests (Issue #13) and HACS Default submission (Session 10)

The original quality numbers (95% coverage, 342 tests, Platinum) were captured before the v1.5 entity audit. CI now publishes live numbers — see badges in the README.
