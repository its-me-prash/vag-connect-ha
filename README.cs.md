<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Integrace Home Assistant pro Audi · VW · Škoda · SEAT · CUPRA</strong>
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
  <a href="README.pl.md">Polski</a> ·
  <a href="README.sv.md">Svenska</a>
</p>

---

Chtěl jsem ovládat své Audi v Home Assistant — pořádně, ne napůl. Tak jsem to postavil.

**VAG Connect** je samostatná integrace Home Assistant pro všechny značky VAG. Žádný middleware, žádný Docker, žádná samostatná služba. Nainstalujte integraci, zadejte přihlašovací údaje, hotovo.

Projekt využívá [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) od @tillsteinbach jako komunikační engine — a rozšiřuje ho o funkce, které v jádře CC neexistují: časovače odjezdu, teplota baterie, ETA nabíjení, informace o nabíjecích stanicích, adresy polohy a další.


## Hlavní funkce

- Hladina paliva/stav baterie, dojezd, nájezd
- GPS + adresa parkování
- Stav vozidla (jede/zaparkováno/offline)
- Nabíjení: výkon, rychlost, čas dokončení, info o stanici
- Teplota baterie · Kapacita baterie
- Klimatizace, vyhřívání sedadel, vyhřívání skel
- Zamykání/odemykání, světelný signál
- **Metrické a imperiální** automaticky přes nastavení HA

Podrobnosti v [úplném README v angličtině](README.en.md).

---

## Installation

Nastavení → Zařízení a služby → Přidat integraci → **VAG Connect**

---


---

## Poslední změny

**[v0.9.0](CHANGELOG.md)** — Kritická oprava: kompatibilita Python 3.11 (chyba 500 v konfiguračním toku)
**[v0.8.0](CHANGELOG.md)** — Gold Quality Scale dokončen — icons.json, zastaralá zařízení, 192 testů
**[v0.7.0](CHANGELOG.md)** — Gold — entry.runtime_data, reauth, reconfigure, ServiceValidationError

➜ [Kompletní changelog →](CHANGELOG.md)

---

## Lizenz / License

MIT — [GitHub](https://github.com/its-me-prash/vag-connect-ha)
