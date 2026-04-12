<p align="center">
  <img src="https://raw.githubusercontent.com/Prash1407/vag-connect-ha/main/custom_components/vag_connect/logo.png" alt="VAG Connect" width="180">
</p>

<h1 align="center">VAG Connect</h1>

<p align="center">
  <strong>Integración de Home Assistant para Audi · VW · Škoda · SEAT · CUPRA</strong>
</p>

<p align="center">
  <a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge" alt="HACS"></a>
  <a href="https://github.com/Prash1407/vag-connect-ha/releases"><img src="https://img.shields.io/github/v/release/Prash1407/vag-connect-ha?style=for-the-badge" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License"></a>
  <a href="https://www.home-assistant.io"><img src="https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue?style=for-the-badge" alt="Home Assistant"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/Tests-192%2F192-brightgreen?style=for-the-badge" alt="Tests"></a>
</p>

<p align="center">
  <a href="README.md">Deutsch</a> · 
  <a href="README.en.md">English</a> ·
  <a href="README.fr.md">Français</a> ·
  <a href="README.nl.md">Nederlands</a> ·
  <a href="README.pl.md">Polski</a> ·
  <a href="README.cs.md">Čeština</a> ·
  <a href="README.sv.md">Svenska</a>
</p>

---

Quería controlar mi Audi en Home Assistant — completamente, no a medias. Así que construí esto.

**VAG Connect** es una integración autónoma de Home Assistant para todas las marcas VAG. Sin intermediarios, sin Docker, sin servicio separado. Instala la integración, introduce tus credenciales, listo.

El proyecto utiliza [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) de @tillsteinbach como motor de comunicación — y lo amplía con funciones que no existen en el núcleo de CC: temporizadores de salida, temperatura de batería, ETA de carga, información de estaciones de carga, direcciones de ubicación y más.


## Funciones principales

- Nivel de combustible/batería, autonomía, kilometraje
- GPS + dirección de aparcamiento
- Estado del vehículo (en marcha/aparcado/sin conexión)
- Carga: potencia, velocidad, hora de fin, info del punto de carga
- Temperatura de la batería · Capacidad de la batería
- Climatización, calefacción de asientos, desempañador
- Bloqueo/desbloqueo, señal luminosa
- **Métrico e imperial** automáticamente mediante ajustes de HA

Consulta el [README completo en inglés](README.en.md) para todos los detalles.

---

## Installation

Ajustes → Dispositivos y servicios → Añadir integración → **VAG Connect**

---

## Lizenz / License

MIT — [GitHub](https://github.com/Prash1407/vag-connect-ha)
