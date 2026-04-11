```
 _   _  ___  _____   _____                             _
| | | |/ _ \|  __ \ /  __ \                           | |
| | | / /_\ \ |  \/ | /  \/ ___  _ __  _ __   ___  ___| |_
| | | |  _  | | __  | |    / _ \| '_ \| '_ \ / _ \/ __| __|
\ \_/ / | | | |_\ \ | \__/\ (_) | | | | | | |  __/ (__| |_
 \___/\_| |_/\____/  \____/\___/|_| |_|_| |_|\___|\___|\__|

  Home Assistant Integration  |  Audi . VW . Skoda . SEAT . CUPRA
```

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Version](https://img.shields.io/github/v/release/Prash1407/vag-connect-ha)](https://github.com/Prash1407/vag-connect-ha/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![HA](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue)](https://www.home-assistant.io)
[![Tests](https://img.shields.io/badge/Tests-18%2F18-brightgreen)](tests/)

**[Deutsch](README.md) · [Francais](README.fr.md) · [Nederlands](README.nl.md) · [Espanol](README.es.md) · [Polski](README.pl.md) · [Cestina](README.cs.md) · [Svenska](README.sv.md)**

---

I wanted to control my Audi from Home Assistant without maintaining three separate integrations or running a dedicated MQTT broker. So I built this.

**VAG Connect** connects Home Assistant directly to the official apps of Audi, VW, Skoda, SEAT, and CUPRA. No middleware, no Docker, no extra service. Install the integration, enter your credentials, done.

The hard technical work was mostly done by Till Steinbach with his [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) framework. This integration is a clean Home Assistant wrapper around it.

---

## Supported Platforms

```
sensor  |  binary_sensor  |  device_tracker  |  switch  |  button  |  climate  |  number
```

---

## Features

### All brands

| Feature | Audi | VW EU | VW US/CA | Skoda | SEAT/CUPRA |
|---|:---:|:---:|:---:|:---:|:---:|
| Fuel / battery level | + | + | + | + | + |
| Range | + | + | + | + | + |
| Odometer | + | + | + | + | + |
| Position (GPS map) | + | + | + | + | + |
| Door status | + | + | + | + | + |
| Window status | + | + | + | + | + |
| Outside temperature | + | + | + | + | + |
| Climatisation status | + | + | + | + | + |
| Lock / unlock | + | + | + | + | + |
| Start / stop climatisation | + | + | + | + | + |
| Flash lights (Honk & Flash) | + | + | + | + | + |

### Electric and hybrid vehicles

| Feature | Audi e-tron | VW ID | Skoda Enyaq | CUPRA Born |
|---|:---:|:---:|:---:|:---:|
| State of charge (%) | + | + | + | + |
| Start / stop charging | + | + | + | + |
| Charge target slider | + | + | + | + |
| Charging state | + | + | + | + |
| Plug connected | + | + | + | + |

### Combustion only

| Feature | Availability |
|---|---|
| Oil level | Audi, VW |
| Service due (km) | Audi, VW, Skoda |
| Service date | Audi, VW, Skoda |
| Oil service due (km) | Audi, VW |

---

## Installation

### Via HACS (recommended)

1. Open HACS -> Integrations -> ... -> Custom Repositories
2. URL: `https://github.com/Prash1407/vag-connect-ha` , Category: Integration
3. Search for **VAG Connect**, install, restart HA

### Manual

Copy the `custom_components/vag_connect/` folder into your `config/custom_components/` directory, then restart Home Assistant.

---

## Setup

**Settings -> Devices & Services -> + Add Integration -> "VAG Connect"**

| Field | Description | Required |
|---|---|:---:|
| Brand | Audi / VW EU / VW US-CA / Skoda / SEAT-CUPRA | yes |
| Email | Same as in the app | yes |
| Password | Same as in the app | yes |
| S-PIN | Required for locking | no |
| Interval | Poll interval in minutes (min. 5) | yes |

---

## Poll interval

Default: 15 minutes. Don't go below 5. The manufacturer APIs are not built for high request rates and can temporarily lock your account.

---

## Services (Automations)

```yaml
# Lock
service: vag_connect.lock
data:
  vin: "WAUZZZ4G7EN123456"

# Start climatisation
service: vag_connect.start_climatisation
data:
  vin: "WAUZZZ4G7EN123456"

# Start charging
service: vag_connect.start_charging
data:
  vin: "WAUZZZ4G7EN123456"

# Stop charging
service: vag_connect.stop_charging
data:
  vin: "WAUZZZ4G7EN123456"

# Flash lights
service: vag_connect.flash_lights
data:
  vin: "WAUZZZ4G7EN123456"

# Force refresh (no VIN parameter)
service: vag_connect.refresh_vehicle
```

---

## Debugging

```yaml
# configuration.yaml
logger:
  logs:
    custom_components.vag_connect: debug
```

For bug reports: Settings -> Devices & Services -> VAG Connect -> ... -> Download Diagnostics. The file contains no passwords and no GPS coordinates.

---

## Versioning

This project uses [Semantic Versioning 2.0.0](https://semver.org/).

```
MAJOR.MINOR.PATCH

MAJOR  Breaking changes (renamed entities, removed platforms)
MINOR  New features (new brand, new sensors, new language)
PATCH  Bug fixes, translation corrections, dependency updates
```

Currently: `0.x.y` (pre-stable). Version `1.0.0` releases when Audi, VW, and Skoda are stable and tested.

---

## Contributing

PRs and issues welcome. Especially needed:

- Tester with **Porsche** (uses the same CARIAD API as Audi)
- Tester with a **Chinese VAG account** (CN region, different endpoints)
- More translations -- a new language file takes about 20 minutes, see [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Credits

This project builds on:

| Project | Author | Contribution |
|---|---|---|
| [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) | @tillsteinbach | API engine for all VAG brands |
| [CarConnectivity-connector-audi](https://github.com/acfischer42/CarConnectivity-connector-audi) | @acfischer42 | Audi CARIAD connector |
| [CarConnectivity-connector-volkswagen](https://github.com/tillsteinbach/CarConnectivity-connector-volkswagen) | @tillsteinbach | VW WeConnect connector |
| [CarConnectivity-connector-skoda](https://github.com/tillsteinbach/CarConnectivity-connector-skoda) | @tillsteinbach | Skoda MySkoda connector |
| [CarConnectivity-connector-seatcupra](https://github.com/tillsteinbach/CarConnectivity-connector-seatcupra) | @tillsteinbach | SEAT/CUPRA MyCupra connector |
| [audi_connect_ha](https://github.com/audiconnect/audi_connect_ha) | @audiconnect | Inspiration and HA integration patterns |
| [homeassistant-myskoda](https://github.com/skodaconnect/homeassistant-myskoda) | @skodaconnect | MQTT architecture reference |
| [ioBroker.vw-connect](https://github.com/TA2k/ioBroker.vw-connect) | @TA2k | API endpoint research |

---

## Legal

This integration uses unofficial APIs -- the same ones the official apps use. It is not authorized or endorsed by Audi AG, Volkswagen AG, CARIAD, Skoda Auto, SEAT S.A., or Nabu Casa.

All brand names are trademarks of their respective owners. Licenses and attributions: [NOTICE.md](NOTICE.md).

---

*Built by [prash1407](https://github.com/Prash1407) -- MIT License -- 2026*
