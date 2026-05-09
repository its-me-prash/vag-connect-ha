<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Home Assistant Integration for Audi · VW · Škoda · SEAT · CUPRA · Porsche · VW US/CA</strong><br>
  <em>One integration for all 7 VAG brands — direct API access, no middleware</em>
</p>

<p align="center">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg" alt="HACS"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/releases"><img src="https://img.shields.io/github/v/release/its-me-prash/vag-connect-ha" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://www.home-assistant.io"><img src="https://img.shields.io/badge/Home%20Assistant-2024.4%2B-blue" alt="Home Assistant"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/its-me-prash/vag-connect-ha/ci.yml?branch=main&label=CI" alt="CI"></a>
</p>

<p align="center">
  <a href="README.md">Deutsch</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.nl.md">Nederlands</a> ·
  <a href="README.pl.md">Polski</a> ·
  <a href="README.cs.md">Čeština</a> ·
  <a href="README.sv.md">Svenska</a>
</p>

---

## 🚗 What it does

Connects Home Assistant **directly** to your vehicle cloud account (myAudi, We Connect ID, MyŠkoda, MyCupra, MySeat, My Porsche, MyVW). **No middleware, no Docker, no extra service** — log in with your app credentials, done.

- **80+ entities** across **10 HA platforms** (sensors, switches, climate, lock, etc.)
- **14 services** (lock, climate, charging, departure-timer, etc.)
- **Vehicle render as device picture** + Custom Lovelace card support
- **GPS position on the HA map** as TrackerEntity
- **Multi-vehicle support** per account
- **Read-only mode** for safe use in automations
- **HACS Quality Scale: Platinum** ⭐

> ✅ **Actively-maintained multi-brand successor** to [`mitch-dc/volkswagen_we_connect_id`](https://github.com/mitch-dc/volkswagen_we_connect_id) (archived 10/2025) and [`skodaconnect/homeassistant-skodaconnect`](https://github.com/skodaconnect/homeassistant-skodaconnect) (deprecated 03/2025).

---

## 📋 Supported brands

| Brand | Backend | Status | Highlights |
|---|---|---|---|
| **Audi** (myAudi) | Cariad-BFF + MBB Legacy | ✅ Stable | PPC/PPE climate, ICE engine start (#28) |
| **Volkswagen EU** (We Connect ID) | Cariad-BFF + MBB Legacy | ✅ Stable | PHEV range-triple, MBB tank fallback for Golf 7 GTE |
| **Škoda** (MyŠkoda mysmob) | Skoda mysmob | ✅ Stable | Charging profiles, OTA, workshop attrs, multi-angle renders |
| **SEAT** (MySEAT OLA) | OLA | ✅ Stable | OLA viewPoint renders (4-7 views) |
| **CUPRA** (MyCupra OLA) | OLA | ✅ Stable | OLA viewPoint renders, Born MY26 firmware shapes |
| **Porsche** (My Porsche) | PPA + Auth0 | ✅ Stable | Own HTTP hardening (retry/quota/storm-protection) |
| **VW US/CA** (myVW NA) | VW NA Cloud | 🟡 Beta | Charge ETA, climate, lock, doors |

---

## 🚀 Installation (HACS)

### Option 1: One-click install (recommended)

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=its-me-prash&repository=vag-connect-ha&category=integration)

### Option 2: HACS custom repository (manual)

1. **HACS → Integrations → ⋮ → Custom repositories**
2. URL: `https://github.com/its-me-prash/vag-connect-ha`
3. Category: **Integration**
4. Search **VAG Connect** + install
5. **Restart Home Assistant**

### Option 3: Manual installation

```bash
cd /config/custom_components
git clone https://github.com/its-me-prash/vag-connect-ha.git
mv vag-connect-ha/custom_components/vag_connect .
rm -rf vag-connect-ha
# Restart HA
```

---

## ⚙️ Configuration

**Settings → Devices & Services → Add integration → "VAG Connect"**

| Field | Example | Description |
|---|---|---|
| Brand | `Audi`, `Volkswagen EU`, etc. | Which brand app do you use? |
| Email | `you@example.com` | Your VAG account email |
| Password | `••••••••` | Your account password |
| S-PIN | `1234` *(optional)* | 4-digit PIN for lock/unlock on some brands |

**Options** (Settings → Devices & Services → VAG Connect → ⋮ → Configure):

- **Polling interval** (5-60 min) — default 10 min. Lower = fresher, but eats API quota faster.
- **Read-only mode** — when on: only status sensors, no switches/buttons that send commands.
- **Reverse geocoding** (opt-in) — sends GPS to OpenStreetMap for address resolution.
- **Push toggles** (Skoda MQTT / CUPRA-SEAT FCM / Audi-VW FCM) — foundation in place, live activation pending testers.

---

## 🎨 What you get

### Standard entities per vehicle (all brands)

**Sensors**: Battery SoC, range (electric/combustion/total), fuel level, odometer, outside temp, battery temp, 12V voltage, service days, oil service days, charging power/rate/type, last trip stats, charging history, plug state, lights count, equipment count, software version, quota remaining, connection state, last seen.

**Binary sensors**: Doors locked, doors open (per door), windows open (per window), trunk/hood/sunroof, plug connected, charging, OTA update available, 12V low warning, lights on (per light), vehicle online.

**Controls**: Lock/unlock, climate start/stop, charging start/stop, window heating, window heating combined, cabin ventilation (CUPRA/SEAT), aux heating (Webasto, CUPRA/SEAT), departure timer (1-3 via `time` platform), set target SoC, set target temp, set max charge current, set charge mode, honk-and-flash, wake vehicle, refresh.

**Image platform**: 1-7 vehicle renders per VIN (Audi/VW: GraphQL MediaService; CUPRA/SEAT: OLA viewPoints; Skoda: widget + multi-angle composites).

**Device tracker**: GPS position as TrackerEntity (`source_type: gps`) for the HA Lovelace map.

### Automatic vehicle picture

The car appears as **device picture** in HA, plus as `entity_picture` on every entity. Custom Lovelace cards ([Ultra-Vehicle-Card](https://github.com/WJDDesigns/Ultra-Vehicle-Card), [vehicle-info-card](https://github.com/ngocjohn/vehicle-info-card), [Mushroom](https://github.com/piitaya/lovelace-mushroom) templates) read `extra_state_attributes.image_url` automatically.

---

## 🗺️ Lovelace examples

### Map card

```yaml
type: map
title: Fleet
default_zoom: 12
hours_to_show: 24
entities:
  - device_tracker.audi_a4_b9_position
  - device_tracker.vw_golf_7_gte_position
  - zone.home
```

### Picture-entity card with vehicle render

```yaml
type: picture-entity
entity: image.audi_a4_b9_render_side_lg
camera_view: live
show_state: false
show_name: false
```

### Vehicle-info card (custom)

```yaml
type: custom:vehicle-info-card
entity: sensor.audi_a4_b9_battery_level
image: '[[ states.image.audi_a4_b9_render_side_lg.state ]]'
```

More examples in [`docs/FAQ.md#lovelace-examples`](docs/FAQ.md).

---

## 🔧 FAQ

| Question | Answer |
|---|---|
| **When is my car woken?** | Only on service calls (lock/climate/wake), never on status polls. Smart-wake cap: max 3 wakes/day per car (default), 5min cooldown between wakes. |
| **How much API quota?** | MyCupra/MySeat: ~1500 calls/day. With 10min default polling: ~144 calls/day = 10% of budget. Sensor `requests_remaining_today` shows current state. |
| **What if tank % is missing on Golf 7 GTE?** | v1.25.0 has MBB VSR Phase 2 read-side fallback. See [Golf 7 GTE tank guide](docs/GOLF_7_GTE_TANK_GUIDE.md). |
| **Token survives HACS update?** | ✅ Yes since v1.19.2 — token persistence via HA `Store` (no re-login after updates). |
| **How do I report bugs?** | HA → Integration → 🔧 Repair → Bug report. Diagnostics are anonymized (VINs masked, GPS rounded, tokens stripped). |

Full FAQ in [`docs/FAQ.md`](docs/FAQ.md).

---

## 🛡️ Privacy & security

- **No external services** — everything goes directly between HA and the manufacturer API
- **Token cache** locally in HA's `.storage/` (per-config-entry, JSON, automatically removed on integration removal)
- **Diagnostics anonymized**: VINs masked (`***ABC123`), GPS rounded to 1 decimal, tokens/passwords completely stripped
- **Reverse geocoding opt-in** — disabled by default
- **VIN masking** consistent across all logs

Details in [`PRIVACY.md`](PRIVACY.md) and [`SECURITY.md`](SECURITY.md).

---

## 🛣️ Roadmap

**Current:** v1.25.0 (Sprint C — cross-brand parity + UX/UI + MBB VSR Phase 2 for Golf 7 GTE tank).

**Pending testers** (see [`docs/EXTERNAL_BLOCKED_ROADMAP.md`](docs/EXTERNAL_BLOCKED_ROADMAP.md)):
- [#160 MBB Phase 2 write-side](https://github.com/its-me-prash/vag-connect-ha/issues/160) — Audi A4 B9 / Q5 2021 / Golf 7 / Passat B8 owner
- [#161 Push Phase 2](https://github.com/its-me-prash/vag-connect-ha/issues/161) — Skoda Connect+ / MyCupra/MySeat / Audi+VW Cariad-modern owner
- [#163 heaterSource](https://github.com/its-me-prash/vag-connect-ha/issues/163) — ID.4/7 / e-tron heat-pump owner

**Planned for v1.26.0**: `device_action` + `device_trigger` (GUI automations for vehicles), `system_health.py`, `logbook.py`, CommandDispatcher Phase 2 refactor, more translation coverage.

Full roadmap: [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## 🤝 Contributing

PRs welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md).

**Vehicle Data Scout** (live since v1.9.0): if your integration detects unknown JSON fields, it automatically creates an HA repair notification with a pre-filled GitHub issue link. **1-click bug report without you having to look at code.**

Live testers wanted for the external-blocked tracks above — comment under the relevant issue with `brand + model + year + subscription status`.

---

## 📜 License

[Apache License 2.0](LICENSE) — see also [`NOTICE.md`](NOTICE.md) for attributions to upstream projects ([myskoda](https://github.com/skodaconnect/myskoda), [pycupra](https://github.com/WulfgarW/homeassistant-pycupra), [audi_connect_ha](https://github.com/audiconnect/audi_connect_ha), [volkswagencarnet](https://github.com/Trekky12/volkswagencarnet), [evcc](https://github.com/evcc-io/evcc)).
