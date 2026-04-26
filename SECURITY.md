# Security Policy

> **Reporting context:** VAG Connect is a Home Assistant integration that
> talks to manufacturer APIs on behalf of vehicle owners. It handles
> credentials, OAuth tokens, S-PINs, vehicle GPS positions, and VINs. We
> take security reports seriously.

---

## Supported Versions

Only the **latest minor release line** receives security fixes. Older lines
are not patched.

| Version | Supported |
|---|---|
| 1.8.x | ✅ |
| 1.7.x | ❌ — please update |
| < 1.7 | ❌ — please update |

Home Assistant supports the integration on its own currently-supported core
versions (typically the last 4 monthly releases). Any HA below the
`hacs.json` minimum is unsupported.

---

## Reporting a Vulnerability

**Please do not file public GitHub issues for security vulnerabilities.**

Use one of the following private channels:

1. **GitHub Security Advisories (preferred)**
   <https://github.com/its-me-prash/vag-connect-ha/security/advisories/new>
   — sends an encrypted private report to the maintainer.

2. **Direct contact**
   Open a GitHub Discussion marked `security` and ask the maintainer to
   move it private. Or use the contact details on the maintainer's GitHub
   profile.

Please include, where possible:

- Affected version(s) of VAG Connect
- Affected Home Assistant version (if relevant)
- Steps to reproduce
- Impact assessment (what does an attacker gain?)
- Whether the issue has already been disclosed publicly

We will acknowledge receipt within **72 hours** and aim to publish a fix or
mitigation within **14 days** for high-severity issues.

---

## Scope

### In scope

- Code under `custom_components/vag_connect/`
- GitHub Actions workflows under `.github/workflows/`
- Documented installation and configuration paths

### Out of scope

- Vulnerabilities in upstream manufacturer APIs (CARIAD BFF, OLA,
  mysmob, PPA, etc.) — please report those to Volkswagen / Audi /
  Škoda / SEAT / CUPRA / Porsche directly.
- Issues caused by user misconfiguration or third-party HACS plugins.
- Theoretical issues without a working proof of concept.

---

## What we already do

- **Zero external runtime dependencies** (`requirements: []` in
  `manifest.json`) — no transitive supply-chain risk.
- **Credentials redaction** in `diagnostics.py` — passwords, S-PINs,
  usernames, GPS coordinates are never exposed in diagnostics exports.
- **S-PIN fail-fast** (since v1.8.0 / #60) — privileged commands raise
  `ServiceValidationError` before they reach the API.
- **Reverse geocoding opt-in** (since v1.8.0 / #60) — vehicle GPS is
  not sent to third-party services unless the user explicitly enables it.
- **TLS-only API calls** — the integration uses HTTPS for every endpoint.
- **No persistent token store outside Home Assistant** — tokens live in
  the standard HA config-entry storage, encrypted by Home Assistant.

---

## What is NOT a vulnerability

- Manufacturer accounts being temporarily rate-limited after too many
  poll requests. This is a server-side rate-limit, not a vulnerability.
- HA users on the same Home Assistant instance being able to read each
  other's vehicle data. This is a **Home Assistant access-control
  matter**, not a VAG Connect issue.

---

*Last updated: 2026-04-26 — v1.8.0*
