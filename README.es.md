<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Integración de Home Assistant para Audi · VW · Škoda · SEAT · CUPRA</strong>
</p>

<p align="center">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/releases"><img src="https://img.shields.io/github/v/release/its-me-prash/vag-connect-ha?style=for-the-badge"></a>
  <a href="../LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/its-me-prash/vag-connect-ha/ci.yml?branch=main&style=for-the-badge&label=CI" alt="CI"></a>
  <a href="https://github.com/its-me-prash/vag-connect-ha/releases"><img src="https://img.shields.io/github/downloads/its-me-prash/vag-connect-ha/total?style=for-the-badge&label=Downloads" alt="Downloads"></a>
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

Desde v0.14.1, la integración habla **directamente** con la API CARIAD — cliente async propio, completamente autónomo. Arquitectura cloud-polling, 80+ entidades en 10 plataformas, 14 servicios.

> ✅ **Sucesor multi-marca mantenido activamente** de [`mitch-dc/volkswagen_we_connect_id`](https://github.com/mitch-dc/volkswagen_we_connect_id) (archivado el 2025-10-29) y [`skodaconnect/homeassistant-skodaconnect`](https://github.com/skodaconnect/homeassistant-skodaconnect) (obsoleto el 2025-03-14). Una integración para Audi, VW, Škoda, SEAT, CUPRA, Porsche y VW US/CA — sin plugin separado por marca.

## Estado actual y límites honestos (v1.8.12)

### ✅ Qué funciona AHORA (todas las 7 marcas)

- 🟢🟡⚫ **Sensor Multi-Brand Connection-State** — online / standby / offline para todas las marcas (v1.8.12).
- 🛡️ **Estabilidad defensiva** — retry 504, retry errores de red transitorios, cache 6h + tolerancia 3 fallos (v1.8.7).
- 🔓 **Comandos Lock / Climate / Charging** para Audi 2024+ y VW Passat 2025 — 10 comandos con fallback CARIAD `/v1/` ↔ `/v2/` (v1.8.5 + v1.8.8).
- 🚪 **CUPRA / SEAT entidades completas** con rutas JSON OLA verificadas + binary sensors por ventana (v1.8.9).
- 🚙 **Škoda** `detail` block + `reliableLockStatus` + `fullyChargedAt` (v1.8.11).

### ⚠️ Aún en progreso

Capability filter fase 2 (v1.8.13) · Defensive coding fase 2 (v1.8.14) · Diagnostics anonimizados (Sesión 4) · Smart-wake + protección 12V (Sesión 6) · Push updates (v1.9.1/2) · Trip stats + EU Data Act (v1.10.0+).

### 🚫 Límites conscientes

- **Plataforma image:** no existe API CARIAD render oficial. Será eliminada o cambiada a URLs de usuario en v1.10.0.
- **PPC/PPE Audi 2025+** (Q5, A5/S5, A6 e-tron, Q6 e-tron, RS e-tron GT Facelift) — graceful degradation en lugar de 404.
- **Ford / marcas no-VAG:** fuera de alcance — ver [`marq24/ha-fordpass`](https://github.com/marq24/ha-fordpass).

### 🔧 Requisito de privacidad

**"Compartir mi posición"** debe estar activado en My-VW / My-Audi / MySkoda / MyCupra — sino backend 403.

### 📚 Más información

- 🗺️ [`../docs/ROADMAP.md`](../docs/ROADMAP.md) · 📜 [`../docs/CHANGELOG_TECHNICAL.md`](../docs/CHANGELOG_TECHNICAL.md) · 🤝 [`../docs/SESSION_HANDOFF.md`](../docs/SESSION_HANDOFF.md) · 🔬 [`../docs/RESEARCH_NOTES_2026-04-29.md`](../docs/RESEARCH_NOTES_2026-04-29.md)

---

## Marcas Compatibles

| Brand | Auth | API | Status |
|---|---|---|---|
| **Volkswagen EU** | IDK | emea.bff.cariad.digital | ✅ |
| **Audi** | IDK + AZS/MBB | emea.bff.cariad.digital | ✅ |
| **Škoda** | IDK | mysmob.api.connect.skoda-auto.cz | ✅ |
| **SEAT** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| **CUPRA** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| Porsche | Auth0 | api.ppa.porsche.com | ✅ Beta |
| VW NA (US/CA) | VW NA Auth | b-h-s.spr.*.p.con-veh.net | ✅ Beta |

> **Porsche & VW NA:** Ambas marcas están disponibles como Beta desde v1.0.0. Buscamos testers — reporta feedback como [Issue](https://github.com/its-me-prash/vag-connect-ha/issues)!

---

## Características

| Feature | Audi | VW EU | Škoda | SEAT/CUPRA |
|---|:---:|:---:|:---:|:---:|
| Fuel / Battery level | ✓ | ✓ | ✓ | ✓ |
| Range | ✓ | ✓ | ✓ | ✓ |
| Odometer | ✓ | ✓ | ✓ | ✓ |
| GPS position | ✓ | ✓ | ✓ | ✓ |
| Doors (total + per door) | ✓ | ✓ | ✓ | ✓ |
| Windows | ✓ | ✓ | ✓ | ✓ |
| Climate start/stop | ✓ | ✓ | ✓ | ✓ |
| Target temperature | ✓ | ✓ | ✓ | ✓ |
| Lock / Unlock | ✓ | ✓ | ✓ | ✓ |
| Flash lights | ✓ | ✓ | ✓ | ✓ |
| Wake vehicle | ✓ | ✓ | ✓ | ✓ |
| Service due km/days | ✓ | ✓ | ✓ | ✓ |
| Online status | ✓ | ✓ | ✓ | ✓ |
| Battery SoC % | ✓ | ✓ | ✓ | ✓ |
| Charge state | ✓ | ✓ | ✓ | ✓ |
| Charge power kW | ✓ | ✓ | ✓ | ✓ |
| Charge speed km/h | ✓ | ✓ | ✓ | ✓ |
| Charge ETA | ✓ | ✓ | ✓ | ✓ |
| Charge target % | ✓ | ✓ | ✓ | ✓ |
| Trunk / hood / sunroof | ✓ | ✓ | ✓ | ✓ |
| Window heating | ✓ | ✓ | ✓ | ✓ |
| Vehicle renders | ✓ | — | — | ✓ |
| Departure timers 1–3 | ✓ | ✓ | — | — |
| Battery temperature | ✓ | ✓ | — | — |
| AdBlue range | ✓ | ✓ | — | ✓ |

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

### Logrado hasta ahora

| Versión | Contenido | Estado |
|---|---|---|
| v1.0–v1.5 | 9 plataformas, 7 marcas, correcciones & auditoría de entidades | ✅ Listo |
| v1.6.0 | SEAT/CUPRA 9 endpoints, corrección Škoda, Audi PPC, cerradura, modo nocturno | ✅ Listo |
| v1.7.0 | Reescritura completa Škoda, traducciones automovilísticas en todos los idiomas, fiabilidad | ✅ Listo |

### Plan de sesiones (P0 → P2)

| Sesión | Versión | Alcance | Issues |
|---|---|---|---|
| **1 — Foundation Fix** | v1.8.0 | iot_class, disponibilidad por VIN, S-PIN fail-fast, writables falsos eliminados | **#60** |
| **1.5 — Privacidad & Auth** | v1.8.1 | Enmascarado de VIN en logs/diagnósticos, ConfigEntryAuthFailed con credenciales obsoletas, documentación userPosition | — |
| **2A — Capabilities Foundation** | v1.8.2 | Taxonomía de errores, modelo 3-estados, caché capabilities (TTL 24h) | #68 |
| **2B — Button gating** | v1.8.3 | Ocultar flash/wake en SEAT/CUPRA según capabilities | #56 |
| **2C — Lock debug + userPosition** | v1.8.4 | Investigar `internal-error` de lock + verificar userPosition | #56 |
| **3 — Command Profile** | v1.8.5 | Routing por marca/región/plataforma, fix RS e-tron GT | #61, #51 |
| **4 — Diagnostics + Fixtures** | v1.8.6 | Diagnósticos anonimizados, tests de regresión | #62, #58 |
| **5 — Process & Governance** | — | Issue forms, brand captains, CODEOWNERS, guía de privacidad | #64 |
| **6 — Read-only + Locking** | v1.9.0 | Modo read-only, command locking, cloud vs wake | #63, #55 |
| **7 — Push CUPRA/SEAT** | v1.9.1 | Firebase FCM vía mqtt.messagehub.de | #57 |
| **8 — Push Škoda** | v1.9.2 | Integración broker MQTT | #57 |
| **9 — Feature batch** | v1.10.0 | Estadísticas, historial carga, UI timers, alarma, perfiles carga | #24, #35, #26, #33, #31 |
| **10 — HACS Default + v2.0.0** | v2.0.0 | Tests live todas las marcas, compatibility matrix, EU Data Act | #13, #59 |

> Orden estricto P0 → P1 → P2. Sesiones 1–4 son innegociables antes de añadir nuevas funcionalidades.

---

## Licencia

Apache License 2.0 — [LICENSE](../LICENSE)

**VAG Connect™** es una marca no registrada (™, no ®). Por favor no uses este nombre en forks para evitar confusión.

Esta integración es un proyecto comunitario independiente sin afiliación con Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG ni ninguna filial del Grupo Volkswagen.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
