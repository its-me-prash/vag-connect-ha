<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Integración de Home Assistant para Audi · VW · Škoda · SEAT · CUPRA · Porsche</strong>
</p>

<p align="center">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/releases"><img src="https://img.shields.io/github/v/release/its-me-prash/vag-connect-ha?style=for-the-badge"></a>
  <a href="../LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge"></a>
  <a href="../tests/"><img src="https://img.shields.io/badge/Tests-342%2F342-brightgreen?style=for-the-badge"></a>
  <a href="../custom_components/vag_connect/quality_scale.yaml"><img src="https://img.shields.io/badge/Quality%20Scale-Platinum%20%F0%9F%8F%86-gold?style=for-the-badge"></a>
</p>

<p align="center">
  <a href="../README.md">Deutsch</a> ·
  <a href="README.en.md">English</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.nl.md">Nederlands</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.pl.md">Polski</a> ·
  <a href="README.cs.md">Čeština</a> ·
  <a href="README.sv.md">Svenska</a>
</p>

---

Quería controlar mi Audi en Home Assistant — completamente. Así que construí esto.

**VAG Connect** es una integración autónoma de Home Assistant para todas las marcas VAG. Sin dependencias externas, sin Docker, sin servicios externos.

Desde v0.14.1, la integración habla **directamente** con la API CARIAD — cliente async propio, completamente autónomo.

---

## Marcas Compatibles

| Brand | Auth | API | Status |
|---|---|---|---|
| **Volkswagen EU** | IDK | emea.bff.cariad.digital | ✅ |
| **Audi** | IDK + AZS/MBB | emea.bff.cariad.digital | ✅ |
| **Škoda** | IDK | mysmob.api.connect.skoda-auto.cz | ✅ |
| **SEAT** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| **CUPRA** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| **Porsche** | Auth0 | api.ppa.porsche.com | ✅ Beta |
| **VW NA (US/CA)** | VW NA Auth | b-h-s.spr.*.p.con-veh.net | ✅ Beta |

> **Porsche & VW NA:** Ambas marcas están disponibles como Beta desde v1.0.0. Porsche usa Auth0 (separado de VAG IDK), VW NA un servidor auth separado. Buscamos testers — reporta tu experiencia como [Issue](https://github.com/its-me-prash/vag-connect-ha/issues)!

---

## Características

### Todos los vehículos (70+ Entities)

| Feature | Audi | VW EU | Škoda | SEAT/CUPRA | Porsche |
|---|:---:|:---:|:---:|:---:|:---:|
| Fuel / Battery level | ✓ | ✓ | ✓ | ✓ | ✓ |
| Range (current + WLTP + estimated full) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Odometer | ✓ | ✓ | ✓ | ✓ | ✓ |
| GPS position + parking address | ✓ | ✓ | ✓ | ✓ | ✓ |
| Doors (total + per door) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Windows | ✓ | ✓ | ✓ | ✓ | ✓ |
| Climate start/stop | ✓ | ✓ | ✓ | ✓ | ✓ |
| Target temperature | ✓ | ✓ | ✓ | ✓ | ✓ |
| Lock / Unlock | ✓ | ✓ | ✓ | ✓ | ✓ |
| Flash lights | ✓ | ✓ | ✓ | ✓ | ✓ |
| Wake vehicle | ✓ | ✓ | ✓ | ✓ | ✓ |
| Service due km/days | ✓ | ✓ | ✓ | ✓ | ✓ |
| Oil service km/days | ✓ | ✓ | ✓ | ✓ | — |
| Online status | ✓ | ✓ | ✓ | ✓ | ✓ |
| Vehicle state (driving/parked) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Outside temperature | ✓ | ✓ | ✓ | ✓ | ✓ |
| Vehicle render images | ✓ | — | — | — | — |
| Firmware version | ✓ | ✓ | ✓ | ✓ | ✓ |
| License plate | ✓ | ✓ | ✓ | ✓ | ✓ |

### Vehículos eléctricos e híbridos

| Feature | Audi | VW EU | Škoda | SEAT/CUPRA | Porsche |
|---|:---:|:---:|:---:|:---:|:---:|
| Battery SoC % | ✓ | ✓ | ✓ | ✓ | ✓ |
| Electric range | ✓ | ✓ | ✓ | ✓ | ✓ |
| Charge state | ✓ | ✓ | ✓ | ✓ | ✓ |
| Charge power kW | ✓ | ✓ | ✓ | ✓ | ✓ |
| Charge speed km/h | ✓ | ✓ | ✓ | ✓ | ✓ |
| Charge ETA | ✓ | ✓ | ✓ | ✓ | ✓ |
| Charge type (AC/DC) | ✓ | ✓ | ✓ | ✓ | ✓ |
| Charging station (name/address/kW/operator) | ✓ | ✓ | ✓ | ✓ | — |
| Plug status + connector lock | ✓ | ✓ | ✓ | ✓ | ✓ |
| Charge start/stop | ✓ | ✓ | ✓ | ✓ | ✓ |
| Charge target % | ✓ | ✓ | ✓ | ✓ | ✓ |
| Seat heating | ✓ | ✓ | ✓ | ✓ | — |
| Window heating | ✓ | ✓ | ✓ | ✓ | — |
| Departure timers 1–3 | ✓ | ✓ | — | — | — |
| Battery temperature | ✓ | ✓ | — | — | — |
| Battery capacity kWh | ✓ | ✓ | — | — | — |
| AdBlue range | ✓ | ✓ | — | — | — |

---

## Instalación

### HACS

1. HACS → Integraciones → ⋮ → Repositorios personalizados
2. URL: `https://github.com/its-me-prash/vag-connect-ha` — Categoría: Integración
3. Instalar **VAG Connect** → Reiniciar Home Assistant
4. Ajustes → Integraciones → **+ Integración** → **VAG Connect**

### Manual

```bash
cp -r custom_components/vag_connect ~/.homeassistant/custom_components/
```

Reinicia Home Assistant.

---

## Configuración

| Field | Required | Description |
|---|---|---|
| Marca | ✓ | Audi / Volkswagen / Škoda / SEAT / CUPRA |
| Correo | ✓ | Correo de la app del fabricante |
| Contraseña | ✓ | Contraseña de la app |
| S-PIN | — | Requerido para bloqueo (en Seguridad en la app) |
| Intervalo | — | Minutos entre actualizaciones (predeterminado: 5) |

**¿Qué app?** Audi → myAudi · VW → WeConnect · Škoda → MyŠkoda · SEAT → My SEAT · CUPRA → MyCupra

---

## Limitaciones Conocidas

- **S-PIN** necesario para bloqueo
- **Intervalo** mínimo 5 minutos
- **2FA** — confirmar una vez manualmente en la app
- **Porsche / VW NA** — funcional como Beta, buscamos testers

---

## Hoja de Ruta

| Version | Content |
|---|---|
| ✅ v0.14.1 | Platinum, own CARIAD client |
| ✅ v1.0.0 | Porsche + VW NA (Beta), 7 brands |
| ✅ v1.5.6 | Vehicle images, 70+ entities, 14 services |
| 🔜 v2.0.0 | HACS Default, trip statistics, charging history |

---

## Licencia

Apache License 2.0 — [LICENSE](../LICENSE)

**VAG Connect™** es una marca no registrada (™, no ®). Por favor no uses este nombre en forks para evitar confusión.

Esta integración es un proyecto comunitario independiente sin afiliación con Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG ni ninguna filial del Grupo Volkswagen.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
