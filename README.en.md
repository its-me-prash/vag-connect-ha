<p align="center">
  <img src="https://raw.githubusercontent.com/Prash1407/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Home Assistant Integration for Audi · VW · Škoda · SEAT · CUPRA</strong>
</p>

<p align="center">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge" alt="HACS"></a>
  <a href="https://github.com/Prash1407/vag-connect-ha/releases"><img src="https://img.shields.io/github/v/release/Prash1407/vag-connect-ha?style=for-the-badge" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License"></a>
  <a href="https://www.home-assistant.io"><img src="https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue?style=for-the-badge" alt="Home Assistant"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/Tests-63%2F63-brightgreen?style=for-the-badge" alt="Tests"></a>
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

I wanted to control my Audi in Home Assistant without running three separate integrations or setting up an extra MQTT broker. So I built this.

**VAG Connect** connects Home Assistant directly to the official apps of Audi, VW, Skoda, SEAT and CUPRA. No middleware, no Docker, no separate service. Install the integration, enter your credentials, done.

The technical foundation is Till Steinbach's [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) framework. This integration is essentially a clean Home Assistant wrapper around it.

---

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
2. Enter URL: `https://github.com/Prash1407/vag-connect-ha`
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
| `vag_connect.lock` | Lock vehicle |
| `vag_connect.unlock` | Unlock vehicle |
| `vag_connect.start_climatisation` | Start climatisation |
| `vag_connect.stop_climatisation` | Stop climatisation |
| `vag_connect.start_charging` | Start charging |
| `vag_connect.stop_charging` | Stop charging |
| `vag_connect.start_window_heating` | Start window heating |
| `vag_connect.stop_window_heating` | Stop window heating |
| `vag_connect.wake_vehicle` | Wake up vehicle |
| `vag_connect.flash_lights` | Flash lights |
| `vag_connect.refresh_vehicle` | Force data refresh |

---

## Credits

This integration would not be possible without these open-source projects:

- **[CarConnectivity](https://github.com/tillsteinbach/CarConnectivity)** by @tillsteinbach — the core engine
- **[CarConnectivity-connector-audi](https://github.com/acfischer42/CarConnectivity-connector-audi)** by @acfischer42
- **[CarConnectivity-connector-volkswagen](https://github.com/tillsteinbach/CarConnectivity-connector-volkswagen)** by @tillsteinbach
- **[CarConnectivity-connector-skoda](https://github.com/tillsteinbach/CarConnectivity-connector-skoda)** by @tillsteinbach
- **[CarConnectivity-connector-seatcupra](https://github.com/tillsteinbach/CarConnectivity-connector-seatcupra)** by @tillsteinbach
- **[CarConnectivity-connector-volkswagen-na](https://github.com/matpoulin/CarConnectivity-connector-volkswagen-na)** by @matpoulin
- **[ioBroker.vw-connect](https://github.com/TA2k/ioBroker.vw-connect)** by @TA2k — API research

---

## License

MIT — see [LICENSE](LICENSE).

This integration uses unofficial APIs — the same ones the official apps use. No guarantee it will always work. Audi, Volkswagen, Škoda, SEAT and CUPRA are registered trademarks of their respective manufacturers.
