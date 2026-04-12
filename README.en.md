<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Home Assistant Integration for Audi · VW · Škoda · SEAT · CUPRA</strong>
</p>

<p align="center">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge" alt="HACS"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/releases"><img src="https://img.shields.io/github/v/release/its-me-prash/vag-connect-ha?style=for-the-badge" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License"></a>
  <a href="https://www.home-assistant.io"><img src="https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue?style=for-the-badge" alt="Home Assistant"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/Tests-192%2F192-brightgreen?style=for-the-badge" alt="Tests"></a>
</p>

<p align="center">
  <a href="README.md">Deutsch</a> · 
  <a href="README.fr.md">Français</a> ·
  <a href="README.nl.md">Nederlands</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.pl.md">Polski</a> ·
  <a href="README.cs.md">Čeština</a> ·
  <a href="README.sv.md">Svenska</a>
</p>

---

I wanted to control my Audi in Home Assistant — properly, not halfway. So I built this.

**VAG Connect** is a standalone Home Assistant integration for all VAG brands. No middleware, no Docker, no separate service. Install the integration, enter your credentials, done.

The project uses [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) by @tillsteinbach as its communication engine — and extends it with features that don't exist in CC's core: departure timers, battery temperature, charge completion ETA, charging station details, location addresses, and more. What CarConnectivity can't do, we build ourselves.


## Supported Platforms

```
sensor  |  binary_sensor  |  device_tracker  |  switch  |  button  |  climate  |  number
```

---

## Features

### All Vehicles

| Feature | Audi | VW EU | VW US/CA | Škoda | SEAT/CUPRA |
|---|:---:|:---:|:---:|:---:|:---:|
| Fuel / Battery level | ✓ | ✓ | ✓ | ✓ | ✓ |
| Range | ✓ | ✓ | ✓ | ✓ | ✓ |
| Odometer | ✓ | ✓ | ✓ | ✓ | ✓ |
| GPS Location | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Location as address** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Heading (direction)** | ✓ | ✓ | ✓ | ✓ | ✓ |
| Doors (overall + individual) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Windows | ✓ | ✓ | ✓ | ✓ | ✓ |
| Outside temperature | ✓ | ✓ | ✓ | ✓ | ✓ |
| Climatisation | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Vehicle state** (driving/parked/offline) | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Reachability** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **License plate** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Firmware version** | ✓ | ✓ | ✓ | ✓ | ✓ |
| Lock / unlock doors | ✓ | ✓ | ✓ | ✓ | ✓ |
| Start / stop climatisation | ✓ | ✓ | ✓ | ✓ | ✓ |
| Flash lights | ✓ | ✓ | ✓ | ✓ | ✓ |
| Wake up vehicle | ✓ | ✓ | ✓ | ✓ | ✓ |

### Electric and Hybrid Vehicles

**Pure electric (EV):**
Audi Q4 e-tron · Q4 Sportback e-tron · e-tron · e-tron GT · Q6 e-tron · A6 e-tron
VW ID.3 · ID.4 · ID.5 · ID.7 · ID.Buzz
Škoda Enyaq iV · Enyaq Coupé iV · Elroq
CUPRA Born · Tavascan · Raval · SEAT el-Born

**Plug-in Hybrid (PHEV):**
Audi Q5 TFSI e · Q7 TFSI e · Q8 TFSI e · A3 TFSI e · A6 TFSI e
VW Golf GTE · Passat GTE · Tiguan eHybrid
Škoda Octavia iV · Superb iV
CUPRA Leon e-Hybrid · Formentor e-Hybrid · SEAT Leon e-Hybrid

| Feature | Audi e-tron | VW ID | Škoda Enyaq | CUPRA Born |
|---|:---:|:---:|:---:|:---:|
| Battery level (%) | ✓ | ✓ | ✓ | ✓ |
| Start / stop charging | ✓ | ✓ | ✓ | ✓ |
| Set charge target (%) | ✓ | ✓ | ✓ | ✓ |
| Charging state | ✓ | ✓ | ✓ | ✓ |
| Charging power (kW) | ✓ | ✓ | ✓ | ✓ |
| Charging speed (km/h or mph) | ✓ | ✓ | ✓ | ✓ |
| **Charge complete ETA** | ✓ | ✓ | ✓ | ✓ |
| **Charge type (AC/DC)** | ✓ | ✓ | ✓ | ✓ |
| **Current charging station** | ✓ | ✓ | ✓ | ✓ |
| **Battery temperature** | ✓ | ✓ | ✓ | ✓ |
| **Battery capacity (kWh)** | ✓ | ✓ | ✓ | ✓ |
| Window heating | ✓ | ✓ | ✓ | ✓ |
| Seat heating | ✓ | ✓ | ✓ | ✓ |
| **Limit max charging current** | ✓ | ✓ | ✓ | ✓ |
| **Auto-unlock plug after charging** | ✓ | ✓ | ✓ | ✓ |

### Combustion and Hybrid

| Feature | Availability |
|---|---|
| Fuel level | All combustion + PHEV |
| Next service (km) | Audi, VW, Škoda |
| Service date | Audi, VW, Škoda |
| Next oil change (km) | Audi, VW |
| Oil change date | Audi, VW |

---

## Installation

### Via HACS (recommended)

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Enter URL: `https://github.com/its-me-prash/vag-connect-ha`
3. Category: **Integration**
4. Add → Search in HACS: **VAG Connect** → Install
5. Restart Home Assistant
6. Settings → Devices & Services → Add integration → **VAG Connect**

### Manual

1. Download this repository
2. Copy the `custom_components/vag_connect/` folder to your HA config directory
3. Restart Home Assistant
4. Settings → Devices & Services → Add integration → **VAG Connect**

---

## Configuration

| Field | Description |
|---|---|
| **Brand** | Audi, VW EU, VW US/CA, Škoda or SEAT/CUPRA |
| **Email** | The email address from the respective app |
| **Password** | The app password |
| **S-PIN** | Only needed for door locking. Found in the app under Security. |
| **Interval** | How often data is fetched. Default: 5 minutes. |
| **Force door access** | For older models where door state is missing. |

---

## Multiple Vehicles

**One account, multiple vehicles:** All vehicles on the account are automatically discovered and set up as separate vehicles.

**Different brands** (e.g. Audi + Škoda): Simply add the integration twice — once for Audi, once for Škoda.

**Two identical models:** Entity IDs automatically get a counter suffix:
```
sensor.audi_q4_e_tron_akkustand       ← first vehicle
sensor.audi_q4_e_tron_2_akkustand     ← second vehicle
```

---

## Update interval

Default: 15 minutes. Don't go below 5 minutes. The manufacturer APIs aren't designed for very frequent polling — too many requests may result in temporary account suspension.

Reactive updates still arrive instantly: when the car reports something (door opens, charging starts), Home Assistant is updated immediately — without waiting for the next interval.

---

## Metric / Imperial

VAG Connect uses Home Assistant's built-in unit system. Change it under:
**Settings → System → General → Unit system**

All distance, temperature and speed sensors convert automatically (km ↔ mi, °C ↔ °F, km/h ↔ mph).

---

## Login Issues

### Two-factor authentication (2FA)

If the account has 2FA enabled: sign in manually in the app once and confirm the email code. After that, VAG Connect stores the login token locally — no re-authentication needed on HA restarts.

### Terms & Conditions / Privacy

After a terms update, a notification appears under **Settings → System → Repairs** with exact steps.

---

## Services

| Service | Description |
|---|---|
| `vag_connect.lock` | Lock the vehicle |
| `vag_connect.unlock` | Unlock the vehicle |
| `vag_connect.start_climatisation` | Start pre-conditioning |
| `vag_connect.stop_climatisation` | Stop pre-conditioning |
| `vag_connect.start_charging` | Start charging |
| `vag_connect.stop_charging` | Stop charging |
| `vag_connect.start_window_heating` | Start window heating |
| `vag_connect.stop_window_heating` | Stop window heating |
| `vag_connect.wake_vehicle` | Wake up vehicle |
| `vag_connect.flash_lights` | Flash lights |
| `vag_connect.refresh_vehicle` | Force data refresh |
| `vag_connect.set_target_soc` | Set charge target (%) |
| `vag_connect.set_climatisation_temperature` | Set climatisation temperature |
| `vag_connect.set_departure_timer` | Set departure timer (new in v0.5.0) |

## Recent Changes

**[v0.9.0](CHANGELOG.md)** — Critical fix: Python 3.11 compatibility
- Fixed 500 Internal Server Error in config flow (removed Python 3.12-only syntax)
- All users on HA 2024.x should update immediately

**[v0.8.0](CHANGELOG.md)** — Gold Quality Scale complete
- `icons.json` — 64 icon definitions across all platforms
- Stale devices: vehicles removed from the account are automatically cleaned up in HA
- 192 tests, 72% coverage, 0 mypy errors

**[v0.7.0](CHANGELOG.md)** — HA Quality Scale Gold
- `entry.runtime_data`, `async_step_reauth`, `async_step_reconfigure`
- `ServiceValidationError`, `log_when_unavailable`, `parallel_updates=0`
- 15 DIAGNOSTIC sensors disabled by default

➜ [Full Changelog →](CHANGELOG.md)

## Credits

This integration builds on the following open-source projects:

- **[CarConnectivity](https://github.com/tillsteinbach/CarConnectivity)** by @tillsteinbach — communication engine for all VAG APIs
- **[CarConnectivity-connector-audi](https://github.com/acfischer42/CarConnectivity-connector-audi)** by @acfischer42
- **[CarConnectivity-connector-volkswagen](https://github.com/tillsteinbach/CarConnectivity-connector-volkswagen)** by @tillsteinbach
- **[CarConnectivity-connector-skoda](https://github.com/tillsteinbach/CarConnectivity-connector-skoda)** by @tillsteinbach
- **[CarConnectivity-connector-seatcupra](https://github.com/tillsteinbach/CarConnectivity-connector-seatcupra)** by @tillsteinbach
- **[CarConnectivity-connector-volkswagen-na](https://github.com/matpoulin/CarConnectivity-connector-volkswagen-na)** by @matpoulin
- **[ioBroker.vw-connect](https://github.com/TA2k/ioBroker.vw-connect)** by @TA2k — API research

