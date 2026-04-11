<p align="center">
  <img src="https://raw.githubusercontent.com/Prash1407/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Home Assistant-integration för Audi · VW · Škoda · SEAT · CUPRA</strong>
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
  <a href="README.en.md">English</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.nl.md">Nederlands</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.pl.md">Polski</a> ·
  <a href="README.cs.md">Čeština</a>
</p>

---

Jag ville styra min Audi i Home Assistant — ordentligt, inte halvhjärtat. Så jag byggde det här.

**VAG Connect** är en fristående Home Assistant-integration för alla VAG-märken. Ingen mellanhand, ingen Docker, ingen separat tjänst. Installera integrationen, ange dina inloggningsuppgifter, klart.

Projektet använder [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) av @tillsteinbach som kommunikationsmotor — och utökar den med funktioner som inte finns i CC:s kärna: avgångstimer, batteritemperatur, laddnings-ETA, laddningsstationsinformation, platsadresser med mera.


## Huvudfunktioner

- Bränsle-/batterinivå, räckvidd, mätarställning
- GPS + parkeringsplats som adress
- Fordonsstatus (kör/parkerat/offline)
- Laddning: effekt, hastighet, klar-tid, info om laddpunkt
- Batteritemperatur · Batterikapacitet
- Klimatisering, sätesvärme, rutavfrostning
- Lås/lås upp, ljussignal
- **Metriska och imperiala** enheter automatiskt via HA-inställningar

Se [fullständig README på engelska](README.en.md) för all information.

---

## Installation

Inställningar → Enheter och tjänster → Lägg till integration → **VAG Connect**

---

## Lizenz / License

MIT — [GitHub](https://github.com/Prash1407/vag-connect-ha)
