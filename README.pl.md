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
  <a href="../tests/"><img src="https://img.shields.io/badge/Tests-337%2F337-brightgreen?style=for-the-badge"></a>
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

Chciałem w pełni sterować moim Audi z poziomu Home Assistant. Więc to zbudowałem.

**VAG Connect** to samodzielna integracja Home Assistant dla wszystkich marek VAG. Bez zewnętrznych zależności, bez Dockera, bez zewnętrznych usług.

Od v0.14.1 integracja **bezpośrednio** komunikuje się z API CARIAD — własny klient async, w pełni autonomiczny.

---

## Obsługiwane Marki

| Brand | Auth | API | Status |
|---|---|---|---|
| **Volkswagen EU** | IDK | emea.bff.cariad.digital | ✅ |
| **Audi** | IDK + AZS/MBB | emea.bff.cariad.digital | ✅ |
| **Škoda** | IDK | mysmob.api.connect.skoda-auto.cz | ✅ |
| **SEAT** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| **CUPRA** | IDK | ola.prod.code.seat.cloud.vwgroup.com | ✅ |
| Porsche | Auth0 | api.ppa.porsche.com | ✅ Beta |
| VW NA (US/CA) | VW NA Auth | b-h-s.spr.*.p.con-veh.net | ✅ Beta |

> **Porsche & VW NA:** Obie marki są dostępne jako Beta od v1.0.0. Szukamy testerów — zgłoś opinię jako [Issue](https://github.com/its-me-prash/vag-connect-ha/issues)!

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
- **Porsche / VW NA** — działające jako Beta, szukamy testerów

---

## Mapa Drogowa

### Osiągnięte

| Wersja | Zawartość | Status |
|---|---|---|
| v1.0–v1.5 | 9 platform, 7 marek, poprawki & audyt encji | ✅ Gotowe |
| v1.6.0 | SEAT/CUPRA 9 endpointów, poprawka Škoda, Audi PPC, zamek, tryb nocny | ✅ Gotowe |
| v1.7.0 | Kompletne przepisanie Škoda, motoryzacyjne tłumaczenia we wszystkich językach, niezawodność | ✅ Gotowe |

### Plan sesji (P0 → P2)

| Sesja | Wersja | Zakres | Issues |
|---|---|---|---|
| **1 — Foundation Fix** | v1.8.0 | iot_class, dostępność per VIN, S-PIN fail-fast, fałszywe writable usunięte | **#60** |
| **2 — Capabilities** | v1.8.1 | Encje wg możliwości, detekcja subskrypcji | #56 |
| **3 — Command Profile** | v1.8.2 | Routing marka/region/platforma, fix RS e-tron GT | #61, #51 |
| **4 — Diagnostics + Fixtures** | v1.8.3 | Anonimizowane diagnostyki, testy regresji | #62, #58 |
| **5 — Process & Governance** | — | Issue forms, brand captains, CODEOWNERS, przewodnik prywatności | #64 |
| **6 — Read-only + Locking** | v1.9.0 | Tryb read-only, command locking, cloud vs wake | #63, #55 |
| **7 — Push CUPRA/SEAT** | v1.9.1 | Firebase FCM via mqtt.messagehub.de | #57 |
| **8 — Push Škoda** | v1.9.2 | Integracja brokera MQTT | #57 |
| **9 — Feature batch** | v1.10.0 | Statystyki, historia ładowania, UI timerów, alarm, profile ładowania | #24, #35, #26, #33, #31 |
| **10 — HACS Default + v2.0.0** | v2.0.0 | Live testy wszystkich marek, compatibility matrix, EU Data Act | #13, #59 |

> Ścisła kolejność P0 → P1 → P2. Sesje 1–4 są nienegocjowalne przed nowymi funkcjami.

---

## Licencja

Apache License 2.0 — [LICENSE](../LICENSE)

**VAG Connect™** jest niezastrzeżonym znakiem towarowym (™, nie ®). Prosimy nie używać tej nazwy w forkach, aby uniknąć nieporozumień.

Ta integracja jest niezależnym projektem społecznościowym bez powiązania z Volkswagen AG, Audi AG, Škoda Auto, SEAT S.A., CUPRA, Porsche AG ani żadną filią Grupy Volkswagen.

---

*Copyright 2026 [Prash Balan](https://github.com/its-me-prash) · Apache License 2.0*
