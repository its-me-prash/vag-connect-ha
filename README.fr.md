<p align="center">
  <img src="https://raw.githubusercontent.com/its-me-prash/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Intégration Home Assistant pour Audi · VW · Škoda · SEAT · CUPRA</strong>
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
  <a href="README.nl.md">Nederlands</a> ·
  <a href="README.es.md">Español</a> ·
  <a href="README.pl.md">Polski</a> ·
  <a href="README.cs.md">Čeština</a> ·
  <a href="README.sv.md">Svenska</a>
</p>

---

Je voulais contrôler mon Audi dans Home Assistant — complètement, pas à moitié. Alors j'ai construit ça.

**VAG Connect** est une intégration Home Assistant autonome pour toutes les marques VAG. Pas d'intermédiaire, pas de Docker, pas de service séparé. Installez l'intégration, entrez vos identifiants, c'est tout.

Le projet utilise [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) de @tillsteinbach comme moteur de communication — et l'étend avec des fonctionnalités qui n'existent pas dans le cœur de CC : minuteries de départ, température de la batterie, heure de fin de charge, informations sur les bornes de recharge, adresses de localisation, et plus encore.


## Fonctionnalités principales

- Niveau de carburant/batterie, autonomie, kilométrage
- GPS + adresse de stationnement
- État du véhicule (conduite/stationné/hors ligne)
- Charge : puissance, vitesse, heure de fin, borne de recharge
- Température de la batterie · Capacité de la batterie
- Climatisation, chauffage des sièges, dégivrage
- Verrouillage/déverrouillage, signal lumineux
- **Métrique et impérial** automatiquement via les paramètres HA

Voir [README complet en anglais](README.en.md) pour tous les détails.

---

## Installation

Paramètres → Appareils et services → Ajouter une intégration → **VAG Connect**

---

## Dernières modifications

**[v0.8.0](CHANGELOG.md)** — Gold Quality Scale complet — icons.json, appareils obsolètes, 192 tests
**[v0.7.0](CHANGELOG.md)** — Gold — entry.runtime_data, reauth, reconfigure, ServiceValidationError
**[v0.6.0](CHANGELOG.md)** — EntityCategory.DIAGNOSTIC / CONFIG, 4 nouveaux capteurs

➜ [Journal des modifications →](CHANGELOG.md)

---

## Lizenz / License

MIT — [GitHub](https://github.com/its-me-prash/vag-connect-ha)
