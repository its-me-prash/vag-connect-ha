# Community VAG-HA Landscape (Research Snapshot 2026-05-03)

Crawl of two HA-community forums for VW Connect / Audi connect / MyCupra / MySkoda / Home Assistant integration discussions, plus a competitor inventory and feature-gap survey.

> **Method note** — `WebFetch` and live-browser tools were not permitted in this session, so the crawl was done via `WebSearch` against `site:community.simon42.com` and `site:community.home-assistant.io`. Reply counts and exact dates inside threads can therefore only be partially reconstructed; thread URLs are the authoritative reference.

---

## A) `community.home-assistant.io` findings

### Top relevant threads

| # | Thread | Topic | Notes |
|---|---|---|---|
| 1 | [VW Connect & Homekit Integration (#984692)](https://community.home-assistant.io/t/vw-connect-homekit-integration/984692) | New HA user wants VW Connect data exposed via Apple HomeKit. Switches and locks already work; battery level + cruising range are the missing pieces. | Active early 2026; primary outreach target. |
| 2 | [Custom Integration: Volkswagen WeConnect ID (Europe) (#380933)](https://community.home-assistant.io/t/custom-integration-volkswagen-weconnect-id-europe/380933) | Long-running megathread (23+ pages) for `mitch-dc/volkswagen_we_connect_id`. Repeated complaints about login breakage, missing climate switch, ID.4 sensors not updating. | Upstream repo archived 2025-10-29, so this thread is now an orphan support channel. |
| 3 | [HA integration for Volkswagen cars (#667118)](https://community.home-assistant.io/t/ha-integration-for-volkswagen-cars/667118) | Generic "which integration should I use" thread; repeated asks for T7 PHEV, ID.7, US-region support; SmartCar workaround mentioned for North America. | Good spot to leave a multi-brand recommendation. |
| 4 | [VW Connect integration does not update (#856617)](https://community.home-assistant.io/t/vw-connect-integration-does-not-update/856617) | Sensors only refresh on manual reload — exact symptom that VAG Connect's coordinator + smart-wake budget addresses. | High-signal outreach target. |
| 5 | [VW Connect integration updatet nicht (#856613)](https://community.home-assistant.io/t/vw-connect-integration-updatet-nicht/856613) | German-language duplicate of #856617. | Outreach target (German reply). |
| 6 | [Integration VW WeConnect - switch climatisation (#684572)](https://community.home-assistant.io/t/integration-vw-weconnect-switch-climatisation/684572) | User can see auxiliary-climatisation switch + target-temp entity but cannot actually change/start. | Direct match for VAG Connect's `command_set_target_temperature` + climate switch. |
| 7 | [How to integrate my Cupra Born? (#410996)](https://community.home-assistant.io/t/how-to-integrate-my-cupra-born/410996) | Multi-page thread; users converge on `daernsinstantfortress/cupra_we_connect` and later `WulfgarW/homeassistant-pycupra`. | Mention multi-brand alternative without dismissing existing tools. |
| 8 | [Cupra Born EV integration (#580016)](https://community.home-assistant.io/t/cupra-born-ev-integration/580016) | The official "share your project" thread for `daernsinstantfortress/cupra_we_connect`. Cupra Tavascan compatibility raised in late 2024. | Reference thread — do NOT spam. |
| 9 | [MySkoda - Only 1 entity after installing (#826546)](https://community.home-assistant.io/t/myskoda-only-1-entity-after-installing-how-to-get-started/826546) | After install user only gets `MySkodaUpdate` — common confusion. | Out of scope for direct outreach. |
| 10 | [Setting AC times and days in MySkoda (#999587)](https://community.home-assistant.io/t/setting-ac-times-and-days-in-myskoda/999587) | Asks for weekly preheat schedules — feature gap across all integrations. | Feature-gap signal. |
| 11 | [Audi Connect and Charging Target (#518042)](https://community.home-assistant.io/t/audi-connect-and-charging-target/518042) | User wants writable target SoC. | Signal for v1.16.0. |
| 12 | [Audi MMI support (#46543)](https://community.home-assistant.io/t/audi-mmi-support/46543) | Long-running 25+ page feature-request thread for native MMI/Audi connect support. | Watch only; mostly historical. |
| 13 | [Audi connect — Sensor Status display issue (#864821)](https://community.home-assistant.io/t/audi-connect-sensor-status-display-issue/864821) | Sensor unit/display problems on dashboards (March 2025). | Quality-of-life signal. |
| 14 | [Skoda Connect (#88288)](https://community.home-assistant.io/t/skoda-connect/88288) | 20+ page legacy thread for the now-deprecated `skodaconnect/homeassistant-skodaconnect`. | Mention deprecation + point to alternatives. |

### High-value reply drafts (ready to post)

> Tone: helpful, brand-neutral first paragraph, soft mention of `vag-connect-ha` only when it solves the asker's specific problem. Always link to the upstream alternative too — anti-spam.

**Reply 1 — for `#984692` (VW Connect & HomeKit):**

> For battery + range you basically need any HA integration that exposes them as `sensor.*`, then HA's own HomeKit Bridge will hand them to Apple Home automatically (battery shows up nicely if you set `device_class: battery`). The classic option is `mitch-dc/volkswagen_we_connect_id`, but that repo was archived in Oct 2025, so a few alternatives have grown up around it: `tillsteinbach/CarConnectivity` (MQTT-based, multi-brand) or `vag-connect-ha` (single HACS integration covering VW EU + ID, Audi, Škoda, SEAT, CUPRA, Porsche, VW US/CA — exposes `sensor.*_state_of_charge`, `sensor.*_range_km`, `sensor.*_electric_range_km`). Whichever you pick, just expose the sensors to HomeKit and you should see them in the Home app.

**Reply 2 — for `#856617` / `#856613` (sensors not auto-updating):**

> The "stale sensors until I reload" pattern is usually one of two things: (a) the underlying API stopped pushing because the car went into deep sleep / low 12V, or (b) the integration's coordinator silently failed and the entity went stale instead of `unavailable`. The archived `mitch-dc` integration didn't recover well from either. Two paths forward — `tillsteinbach/CarConnectivity` (Docker + MQTT, very robust) or `vag-connect-ha` (drop-in HACS replacement, has 12V-battery monitoring + a wake-budget that prevents silent outages). Both will surface a `connection_state` sensor so you actually see when the car is offline rather than just stale.

**Reply 3 — for `#684572` (climate switch / target-temp not changing):**

> If you can see `climate.*` and a target-temp number entity but writes don't take effect, it's almost always a missing PPC/PPE body shape on the POST or a missing capability flag in your subscription. `mitch-dc/volkswagen_we_connect_id` never finished the climate POST mapping for newer ID.4/ID.5 firmware and is now archived. Worth trying `vag-connect-ha` — it has a `command_set_target_temperature` plus `command_start_climate` service, optimistic UI (the switch flips immediately and reverts on failure), and a capability-filter that disables the entity if the backend says `not_entitled` instead of letting the click look successful. If you can paste the `homeassistant.log` line at the moment you toggle the switch, that usually pins it down.

---

## B) `community.simon42.com` findings

### Top relevant threads

| # | Thread | Topic | Notes |
|---|---|---|---|
| 1 | [VW ID3 in Home Assistant — keine vernünftige Integration verfügbar?! (#35037)](https://community.simon42.com/t/vw-id3-in-home-assistant-keine-vernuenftige-integration-verfuegbar/35037) | OP says CUPRA Born has a working HACS integration but only finds an outdated GitHub repo for ID.3, not in HACS. | Direct outreach target. |
| 2 | [Volkswagen Connect funktioniert nicht mehr (#39633)](https://community.simon42.com/t/volkswagen-connect-funktioniert-nicht-mehr/39633) | 22+ replies, Nov 2025, login error `Form with ID 'emailPass'` after backend change. Some users got it back via uninstall+reinstall. | High-signal outreach target — entire thread is the post-mortem of the archived `mitch-dc` integration. |
| 3 | [VW ID in HomeAssistant einbinden (#34405)](https://community.simon42.com/t/vw-id-in-homeassistant-einbinden/34405) | "Wie binde ich es ein" beginner question. | Target for brief recommendation. |
| 4 | [Volkswagen We Connect ID kein Login möglich (#46430)](https://community.simon42.com/t/volkswagen-we-connect-id-kein-login-moeglich/46430) | Jan 2025; same login/2FA breakage class. | Target. |
| 5 | [Vw Connect & HomeBridge (#77825)](https://community.simon42.com/t/vw-connect-homebridge/77825) | Same use case as the HA-community HomeKit thread, German side. | Target. |
| 6 | [Cupra WeConnect — Verbindungsaufbau klappt nicht mehr (#29122)](https://community.simon42.com/t/cupra-weconnect-verbindungsaufbau-klappt-nicht-mehr/29122) | Token / connection breakage on Cupra. | Target. |
| 7 | [VW Connect — Km-Zähler ab laden für ID3 (#27450)](https://community.simon42.com/t/vw-connect-km-zaehler-ab-laden-fuer-id3/27450) | User wants a "since last charge" odometer derived helper. | Feature-gap signal. |
| 8 | [Volkswagen We Connect ID Fahrzeug Bild in Home Assistant (#77892)](https://community.simon42.com/t/volkswagen-we-connect-id-fahrzeug-bild-in-home-assistant/77892) | Feb 2026; user built first own integration to fetch the car render image. | Validates our v1.16+ image-platform decision (no official CARIAD render API). |
| 9 | [Audi Connect — Klimatisierung starten (#13011)](https://community.simon42.com/t/audi-connect-klimatisierung-starten/13011) | Wants Standheizung/Klima start equivalent to MyAudi app. | Direct match for our climate services. |
| 10 | [Audi Connect — Entitäten fehlen nun (#34653)](https://community.simon42.com/t/audi-connect-entitaeten-fehlen-nun/34653) | Battery, km, location, Standheizung entities disappeared after a backend change. | Target. |
| 11 | [VW ID Connect Europe — keine Anzeige des Trips Verbrauchs (#57444)](https://community.simon42.com/t/vw-id-connect-europe-keine-anzeige-des-trips-verbrauchs/57444) | Trip-stats not showing. | Maps to our planned v1.14.0 trip-statistics. |
| 12 | [Auto- und Heatmode Solltemperatur (#44172)](https://community.simon42.com/t/auto-und-heatmode-solltemperatur/44172) | Wants HA to drive the climate setpoint. | Match for `command_set_target_temperature`. |
| 13 | [Automatisches Fahrtenbuch für VW ID Modelle via WeConnect ID (#11936)](https://community.simon42.com/t/automatisches-fahrtenbuch-fuer-vw-id-modelle-via-weconnect-id/11936) | Existing community recipe (Google-Sheets driven trip log). | Reference, not outreach. |

### High-value reply drafts (ready to post)

**Reply 4 — for `#35037` (ID.3 keine vernünftige Integration):**

> Das Repo, das du gefunden hast, ist sehr wahrscheinlich `mitch-dc/volkswagen_we_connect_id` — der Autor hat das Projekt am 29.10.2025 archiviert, deshalb keine Updates mehr. Aktuell aktiv gepflegt sind: `tillsteinbach/CarConnectivity` (Python+MQTT, Multi-Brand, sehr stabil aber braucht Docker/MQTT-Broker) und `vag-connect-ha` (eine HACS-Integration für VW EU+ID, Audi, Škoda, SEAT, CUPRA, Porsche, VW US/CA — kein Docker, nur App-Login). Beide funktionieren mit der ID.3 inkl. SoC, Reichweite, Standheizung-Schalter und Türschloss.

**Reply 5 — for `#39633` (Volkswagen Connect funktioniert nicht mehr):**

> Der `Form with ID 'emailPass'`-Fehler kommt von der Login-Flow-Änderung im CARIAD-Backend Mitte/Ende 2025. Das Original-Repo `mitch-dc/volkswagen_we_connect_id` ist seit 29.10.2025 archiviert, daher kein Patch mehr von dort. Funktionierende Alternativen: `tillsteinbach/CarConnectivity` (mit aktualisiertem Login-Flow) oder `vag-connect-ha` (HACS-Integration mit Token-Refresh-Storm-Schutz und 504-Retry, deckt VW EU+ID + 6 weitere VAG-Marken ab). Bei Login-Problemen lohnt es sich, davor in der My-VW-App einmal manuell auszuloggen + neu einzuloggen, dann in HA neu zu konfigurieren.

**Reply 6 — for `#13011` / `#34653` (Audi Klimatisierung / fehlende Entitäten):**

> `audiconnect/audi_connect_ha` ist weiterhin aktiv, hat aber bekanntlich ein paar PPC/PPE-Lücken (neuere Q4 / Q6 e-tron Firmware). Falls dir Entitäten fehlen oder die Standheizung sich nicht starten lässt, lohnt ein Vergleich mit `vag-connect-ha` — das ist eine Multi-Brand HACS-Integration die u.a. Audi diesel-Range-Fallback und Capability-Filter (versteckt Buttons wenn das Backend "not_entitled" sagt) eingebaut hat. Wichtig in beiden Fällen: in der MyAudi-App muss "Standort teilen" aktiv sein, sonst antwortet die API mit 403.

---

## C) Competitor inventory

> Stars/last-release reflect public-search snapshots from May 2026; verify on GitHub before quoting in marketing.

| Project | Brand(s) | Status | Last release / activity | Verdict |
|---|---|---|---|---|
| [`mitch-dc/volkswagen_we_connect_id`](https://github.com/mitch-dc/volkswagen_we_connect_id) | VW ID (EU) | **Archived 2025-10-29** (read-only) | n/a | Dead. Many open issues for HA 2024.6+ compat, login failures, ID.4 sensors not updating. Primary migration target for our outreach. |
| [`robinostlund/homeassistant-volkswagencarnet`](https://github.com/robinostlund/homeassistant-volkswagencarnet) | VW non-ID (Carnet) | Maintained but bug-heavy (login + stale-state issues open in 2024–25) | Recent releases through 2025; not archived | Legacy ICE/PHEV niche. Still works for some, but new users typically hit login breakage. |
| [`audiconnect/audi_connect_ha`](https://github.com/audiconnect/audi_connect_ha) | Audi only | **Active** (commits + open issues into 2026) | Updated March 2026 | Best-of-breed for Audi-only owners. PPC/PPE 2025+ models still partially unsupported. Not US/CN compatible. |
| [`skodaconnect/homeassistant-myskoda`](https://github.com/skodaconnect/homeassistant-myskoda) | Škoda (MySkoda app) | **Active** | v1.31.x (March 2026); `myskoda` Python lib released 2026-04-28 | Best-of-breed for Škoda. Recent rate-limit / 429 lockout issues. Known pain: changing Skoda account email breaks integration with no recovery path. |
| [`skodaconnect/homeassistant-skodaconnect`](https://github.com/skodaconnect/homeassistant-skodaconnect) | Škoda (legacy Connect) | **DEPRECATED** (per repo title) | n/a | Migration target. Point users to either `homeassistant-myskoda` or our integration. |
| [`WulfgarW/homeassistant-pycupra`](https://github.com/WulfgarW/homeassistant-pycupra) + [`WulfgarW/pycupra`](https://github.com/WulfgarW/pycupra) | CUPRA + SEAT | **Active** | Recurring releases; entity-availability bugs reported in 2026 (issue #39) | Best-of-breed for CUPRA/SEAT today. Solo-maintainer risk. Author already exploring `EUDAConnection` for September 2026 EU Data Act deadline — same direction as our v2.0.0. |
| [`daernsinstantfortress/cupra_we_connect`](https://github.com/daernsinstantfortress/cupra_we_connect) + `WeConnect-Cupra-python` | CUPRA Born | Active but slower; recent issue 2026-03-31 | n/a | Predecessor to pycupra; many users still on it for Born. |
| [`tillsteinbach/CarConnectivity`](https://github.com/tillsteinbach/CarConnectivity) (+ `-connector-volkswagen`, `-plugin-mqtt`, `-plugin-mqtt_homeassistant`) | VW, Škoda, SEAT, Cupra (multi via connectors) | **Active**, declared successor to WeConnect-python which is **end-of-life** | Continuous through 2026 | Strongest direct competitor. Architecture: Python core → MQTT → HA auto-discovery. Requires Docker/MQTT broker. Our differentiator: native HACS, no middleware. |
| [`tillsteinbach/WeConnect-python`](https://github.com/tillsteinbach/WeConnect-python) (+ `-mqtt`, `-cli`) | VW (EU) | **End-of-life** (per author) | n/a | Migration to CarConnectivity. The Python lib that `mitch-dc` depended on is also sunsetting. |
| [`acdcnow/HA_audi_connect`](https://github.com/acdcnow/HA_audi_connect) | Audi PEV/BEV | Fork of audiconnect | Low activity | Niche fork; ignore unless asked. |
| [`jnxxx/homeassistant-connectedcars_io`](https://github.com/jnxxx/homeassistant-connectedcars_io) | "Min Volkswagen" (DK Connectedcars.io) | Region-specific | Sporadic | Out of scope (Denmark-only OBD service). |
| SmartCar HA integration ([thread #884848](https://community.home-assistant.io/t/smartcar-integration/884848)) | Multi-brand incl. VW US | Third-party SaaS, free tier 500 req/mo | n/a | The North-America fallback recommended in many threads. |

---

## D) Feature-gap discovery

What users keep asking for that no integration ships well today:

**Easy** (probably already in scope or 1–2 sprints out)
- Single climate-toggle button (one entity that maps to the cluster of `start_climate` / `set_temp` / `stop_climate` services). Asked in `#684572`, `#44172`.
- "Charging-since" derived odometer / kWh per trip helper exposed natively. Asked in `#27450`.
- `connection_state` (online/standby/offline) — already shipped in v1.8.12 of vag-connect-ha; competitors don't have it.
- Better "stale vs unavailable" handling so dashboards visually reflect "car asleep". Implicit in `#856617`/`#856613`.

**Medium** (1–2 minor releases)
- Writable weekly preheat schedule (day-of-week + time grid). Asked in `#999587` (MySkoda) and across forums.
- Trip-statistics surface (`tripstatistics/v1` for Audi, equivalents for VW/Škoda). Already on roadmap as v1.14.0; matches `#57444`.
- Vehicle render-image entity. Validated as a real ask in simon42 `#77892`. Confirmed no official CARIAD API → user-supplied URL pattern is the right answer.
- Standort-spezifische Ladeprofile (home vs away target SoC, current limit). Maps to v1.16.0.

**Hard** (architectural / API gaps)
- Real-time push instead of polling (mysmob MQTT for Škoda, Firebase FCM for CUPRA/SEAT). Roadmapped as v1.18.0.
- PPC/PPE Audi 2025+ (Q4, A5/S5, A6 e-tron, Q6 e-tron, RS e-tron GT facelift) — E³ 1.2 architecture not publicly reverse-engineered yet (also missing in `audi_connect_ha` and `CarConnectivity`).
- EU Data Act-compliant access path (deadline Sept 2026). pycupra's `EUDAConnection` is the reference; on roadmap as v2.0.0.
- ICE Remote Start (audi_connect_ha #717 pattern). Roadmapped v1.17.0.

**Out of scope**
- US/CN region for native APIs (use SmartCar). VAG Connect supports VW US/CA via the official VW US backend — keep that distinction.
- Non-VAG brands (Ford → `marq24/ha-fordpass`).
- OBD-dongle telemetry (covered by other projects, e.g., DATAPLUG thread `#437889`).

---

## E) SEO keyword harvest (DE + EN)

Use these phrases verbatim in `README.md`, HACS description, GitHub topics, and release notes:

- `VW Connect Home Assistant`, `WeConnect ID Home Assistant`, `Volkswagen WeConnect HACS`
- `Audi Connect Home Assistant`, `MyAudi Home Assistant`, `Audi Connect Standheizung`, `audi connect HACS`
- `MySkoda Home Assistant`, `Skoda Connect deprecated`, `Skoda HACS integration`
- `MyCupra Home Assistant`, `Cupra Born Home Assistant`, `Cupra WeConnect HACS`
- `MySeat Home Assistant`, `SEAT integration HACS`
- `Porsche Connect Home Assistant`, `My Porsche HACS`
- `VW ID3 Home Assistant`, `VW ID4 Home Assistant`, `VW ID5 Home Assistant`, `VW ID7 Home Assistant`, `ID Buzz Home Assistant`
- `VAG Home Assistant`, `multi brand VAG integration`, `VAG HACS integration`
- `Volkswagen Connect funktioniert nicht`, `WeConnect login failed`, `Form with ID emailPass`
- `Klimatisierung starten Home Assistant`, `Standheizung Auto Home Assistant`, `Auto vorheizen Home Assistant`
- `mitch-dc archived alternative`, `WeConnect-python end of life`, `CarConnectivity vs HACS`
- `Apple HomeKit VW`, `HomeKit Auto Batterie`, `Auto Reichweite HomeKit`

---

## F) Open questions

1. Should we proactively post on `#984692`, `#856617`, `#39633`, `#35037`? Recommendation: yes, in that order, with the drafts above. Spread posts across 1–2 weeks to avoid trip-wiring forum anti-spam.
2. Do we want a dedicated "Share your project" thread for `vag-connect-ha` on `community.home-assistant.io`? Strong yes — competitors all have one (Cupra Born `#580016`, WeConnect ID `#380933`); without it we are invisible to forum search.
3. Should the German simon42 outreach be done from a new dedicated forum account vs Prash's personal one? The forum etiquette favours a maintainer-named account ("PB Autowerx" or your own name) so users can verify the project owner; avoid generic-bot-looking handles.
4. CarConnectivity is the strongest direct competitor and shares the EU-Data-Act direction. Is a friendly upstream collaboration (e.g., contributing CUPRA fixes back) on the table, or do we stay strictly downstream / parallel?
5. We need a written stance on rate-limiting (the recurring 429/430 lockouts that hit MySkoda users). VAG Connect's wake-budget already addresses this, but the README doesn't sell it; worth a dedicated FAQ entry for forum drive-by readers.

---

*Sources: all cited inline as URLs. No usernames quoted. Generated 2026-05-03.*
