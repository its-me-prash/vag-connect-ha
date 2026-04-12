<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Integracja Home Assistant dla Audi · VW · Škoda · SEAT · CUPRA</strong>
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
  <a href="README.en.md">English</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.nl.md">Nederlands</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.cs.md">Čeština</a> ·
  <a href="README.sv.md">Svenska</a>
</p>

---

Chciałem sterować moim Audi z Home Assistant — w pełni, nie połowicznie. Więc to zbudowałem.

**VAG Connect** to samodzielna integracja Home Assistant dla wszystkich marek VAG. Bez pośredników, bez Dockera, bez osobnego serwisu. Zainstaluj integrację, wprowadź dane logowania, gotowe.

Projekt używa [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) autorstwa @tillsteinbach jako silnika komunikacji — i rozszerza go o funkcje, których nie ma w rdzeniu CC: timery odjazdu, temperatura baterii, ETA ładowania, informacje o stacjach ładowania, adresy lokalizacji i więcej.


## Główne funkcje

- Poziom paliwa/baterii, zasięg, przebieg
- GPS + adres miejsca parkowania
- Stan pojazdu (jedzie/zaparkowany/offline)
- Ładowanie: moc, prędkość, czas zakończenia, info o stacji
- Temperatura baterii · Pojemność baterii
- Klimatyzacja, ogrzewanie siedzeń, ogrzewanie szyb
- Blokowanie/odblokowanie, sygnał świetlny
- **Metryczny i imperialny** automatycznie przez ustawienia HA

Szczegóły w [pełnym README po angielsku](README.en.md).

---

## Installation

Ustawienia → Urządzenia i usługi → Dodaj integrację → **VAG Connect**

---

## Ostatnie zmiany

**[v0.8.0](CHANGELOG.md)** — Gold Quality Scale ukończony — icons.json, stare urządzenia, 192 testy
**[v0.7.0](CHANGELOG.md)** — Gold — entry.runtime_data, reauth, reconfigure, ServiceValidationError
**[v0.6.0](CHANGELOG.md)** — EntityCategory.DIAGNOSTIC / CONFIG, 4 nowe sensory

➜ [Pełny dziennik zmian →](CHANGELOG.md)

---

## Lizenz / License

MIT — [GitHub](https://github.com/its-me-prash/vag-connect-ha)
