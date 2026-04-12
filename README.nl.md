<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Home Assistant Integratie voor Audi · VW · Škoda · SEAT · CUPRA</strong>
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
  <a href="README.es.md">Español</a> ·
  <a href="README.pl.md">Polski</a> ·
  <a href="README.cs.md">Čeština</a> ·
  <a href="README.sv.md">Svenska</a>
</p>

---

Ik wilde mijn Audi volledig bedienen vanuit Home Assistant. Dus bouwde ik dit.

**VAG Connect** is een zelfstandige Home Assistant-integratie voor alle VAG-merken. Geen middleware, geen Docker, geen aparte dienst. Installeer de integratie, voer je inloggegevens in, klaar.

Het project gebruikt [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) van @tillsteinbach als communicatie-engine — en breidt het uit met functies die niet in de CC-kern bestaan: vertrektimers, batterijtemperatuur, laadtijd ETA, laadstation-informatie, locatieadressen en meer.


## Hoofdfuncties

- Brandstof-/accuniveau, actieradius, kilometerstand
- GPS + parkeerlocatie als adres
- Voertuigstatus (rijden/geparkeerd/offline)
- Laden: vermogen, snelheid, gereed-tijdstip, laadpaal-info
- Accutemperatuur · Accucapaciteit
- Klimaatregeling, stoelverwarming, ruitenverwarming
- Vergrendelen/ontgrendelen, lichtsignaal
- **Metrisch en imperiaal** automatisch via HA-instellingen

Zie de [volledige README in het Engels](README.en.md) voor alle details.

---

## Installation

Instellingen → Apparaten en diensten → Integratie toevoegen → **VAG Connect**

---

## Lizenz / License

MIT — [GitHub](https://github.com/its-me-prash/vag-connect-ha)
