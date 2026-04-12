<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Integracja Home Assistant dla Audi · VW · Škoda · SEAT · CUPRA</strong>
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

Chciałem w pełni sterować moim Audi z poziomu Home Assistant. Więc to zbudowałem.

**VAG Connect** to samodzielna integracja Home Assistant dla wszystkich marek VAG. Bez CarConnectivity, bez Dockera, bez zewnętrznych usług, bez zewnętrznych zależności.

Od v0.14.0 integracja **bezpośrednio** komunikuje się z API CARIAD — własny klient async, w pełni autonomiczny.

---

## Obsługiwane Marki

| Brand | Auth | API | Status |
|---|---|---|---|
| **Volkswagen EU** | IDK | emea.bff.cariad.digital | ✅ |
| **Audi** | IDK + AZS/MBB | emea.bff.cariad.digital | ✅ |
| **Škoda** | IDK | mysmob.api.connect.skoda-auto.cz | ✅ |
| **SEAT** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| **CUPRA** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| Porsche | Auth0 | api.ppa.porsche.com | 🔜 v0.15.0 |
| VW NA (US/CA) | VW NA Auth | b-h-s.spr.*.p.con-veh.net | 🔜 v0.16.0 |

> **Porsche:** Porsche używa całkowicie oddzielnego systemu Auth0. Planowane na v0.15.0. Dla Porsche teraz: [ha-porscheconnect](https://github.com/CJNE/ha-porscheconnect) (MIT).

---

## Funkcje

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
| Charge ETA | ✓ | ✓ | ✓ | ✓ |
| Charge target % | ✓ | ✓ | ✓ | ✓ |
| Window heating | ✓ | ✓ | ✓ | ✓ |
| Departure timers 1–3 | ✓ | ✓ | — | — |
| Battery temperature | ✓ | ✓ | — | — |
| AdBlue range | ✓ | ✓ | — | — |

---

## Instalacja

### HACS

1. HACS → Integracje → ⋮ → Niestandardowe repozytoria
2. URL: `https://github.com/its-me-prash/vag-connect-ha` — Kategoria: Integracja
3. Zainstaluj **VAG Connect** → Uruchom ponownie Home Assistant
4. Ustawienia → Integracje → **+ Integracja** → **VAG Connect**

### Manual

```bash
cp -r custom_components/vag_connect ~/.homeassistant/custom_components/
```

Uruchom ponownie Home Assistant.

---

## Konfiguracja

| Field | Required | Description |
|---|---|---|
| Marka | ✓ | Audi / Volkswagen / Škoda / SEAT / CUPRA |
| E-mail | ✓ | E-mail logowania z aplikacji producenta |
| Hasło | ✓ | Hasło z aplikacji |
| S-PIN | — | Wymagany do blokowania (w Bezpieczeństwo w aplikacji) |
| Interwał | — | Minuty między aktualizacjami (domyślnie: 5) |

**Która aplikacja?** Audi → myAudi · VW → WeConnect · Škoda → MyŠkoda · SEAT → My SEAT · CUPRA → MyCupra

---

## Znane Ograniczenia

- **S-PIN** wymagany do blokowania
- **Interwał** minimum 5 minut
- **2FA** — potwierdzić raz ręcznie w aplikacji
- **Porsche** — oddzielny system Auth0, planowane v0.15.0
- **VW Ameryka Północna** — oddzielny serwer auth, planowane v0.16.0

---

## Mapa Drogowa

| Version | Content |
|---|---|
| ✅ v0.14.0 | Platinum, own CARIAD client |
| 🔜 v0.15.0 | Porsche (Auth0 + PPA API) |
| 🔜 v0.16.0 | VW North America |
| 🎯 v1.0.0 | HACS Official |

---

## Licencja

Apache License 2.0 — [LICENSE](../LICENSE)

**VAG Connect™** jest niezastrzeżonym znakiem towarowym (™, nie ®). Prosimy nie używać tej nazwy w forkach, aby uniknąć nieporozumień.

Ta integracja jest niezależnym projektem społecznościowym bez powiązania z Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG ani żadną filią Grupy Volkswagen.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
