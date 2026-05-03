# browser_mod Integration Assessment

**Date:** 2026-05-03
**Upstream:** [thomasloven/hass-browser_mod](https://github.com/thomasloven/hass-browser_mod) (`browser_mod` v2)
**Scope:** Evaluate fit with `vag-connect-ha` integration + planned "Ultimate VAG Vehicle Card" custom Lovelace card.

---

## A) browser_mod overview

- **Stars:** 1727 (forks 212, watchers 18) — top-tier HA frontend ecosystem project.
- **Last activity:** push 2026-04-29; updated 2026-05-01 — actively maintained.
- **License:** MIT. **HACS:** Default repo (no manual add). **Status:** v2 stable, v1 deprecated.
- **Primary purpose:** Turns each connected browser tab into an HA-controllable entity (media_player, light, sensors) and exposes services that act on the frontend (popups, navigation, theme, notifications).
- **Mental model:** Browser → registers via the Browser Mod sidebar panel → gets a Browser ID → backend can target it by `browser_id`/`user_id`. Service calls are either *Server* calls (broadcast to all registered browsers if untargeted) or *Browser* calls via `fire-dom-event` (only the calling browser).

---

## B) Service catalog

| Service | Key params | Purpose |
|---|---|---|
| `browser_mod.popup` | `title`, `content` (text/HTML/card-config/ha-form), `popup_card_id`, `right_button(_action/_close)`, `left_button(_action)`, `dismissable`, `timeout(_action)`, `tag`, `initial_style` (`normal`/`wide`/`fullscreen`/`classic`), `popup_styles` | Modal dialog with arbitrary Lovelace card / form / HTML content. |
| `browser_mod.close_popup` | `all`, `tag` | Close active popup(s). |
| `browser_mod.set_popup_style` | `style`, `direction`, `tag`, `all` | Cycle/set popup display style. |
| `browser_mod.notification` | `message`, `duration`, `action_text`, `action` | Toast notification. |
| `browser_mod.navigate` | `path` | Navigate browser to HA path. |
| `browser_mod.refresh` | — | Reload current page. |
| `browser_mod.more_info` | `entity`, `view` (`info`/`history`/`settings`/`related`), `large`, `ignore_popup_card`, `close` | Open more-info dialog. |
| `browser_mod.set_theme` | `theme`, `dark` (`auto`/`dark`/`light`), `primaryColor`, `accentColor` | Per-browser theme override. |
| `browser_mod.sequence` | `sequence: [<service call>...]` | Run multiple services as one targeted block. |
| `browser_mod.delay` | `time` (ms) | Wait inside a `sequence`. |
| `browser_mod.console` | `message` | Log to browser dev console. |
| `browser_mod.change_browser_id` | `current_browser_id`, `new_browser_id`, `register`, `refresh` | Rename a browser. |

All services accept `browser_id` / `user_id` targeting. `THIS` placeholder available in *Browser* calls for `browser_id`, `user_id`, and `browser_entities`.

---

## C) Entity surface (per registered browser)

| Entity type | Example `entity_id` | Notes |
|---|---|---|
| `sensor` Browser ID | `sensor.<bid>` | |
| `sensor` path | `sensor.<bid>_browser_path` | Current dashboard path. |
| `sensor` visibility | `sensor.<bid>_browser_visibility` | Tab visible/hidden. |
| `sensor` user agent | `sensor.<bid>_browser_useragent` | |
| `sensor` user | `sensor.<bid>_browser_user` | Logged-in HA user. |
| `sensor` width / height | `sensor.<bid>_browser_width|height` | |
| `sensor` dark mode | `sensor.<bid>_browser_dark_mode` | |
| `sensor` panel | `sensor.<bid>_panel` | viewTitle attr. |
| `binary_sensor` activity | `binary_sensor.<bid>_browser` | User active vs idle. |
| `binary_sensor` FullyKiosk | `binary_sensor.<bid>_browser_fullykiosk` | |
| `light` screen | `light.<bid>_browser_screen` | Brightness overlay. |
| `media_player` | `media_player.<bid>` | |
| `binary_sensor` charging + `sensor` battery | DYNAMIC (mobile only) | |
| `camera` | DYNAMIC (cam-equipped browsers) | |

Plus a `browser_entities` template var for dynamic entity-id resolution.

---

## D) Use-case-fit assessment for vag-connect-ha

| # | Use case | Feasibility | Value | Sketch | Target |
|---|---|---|---|---|---|
| **a** | 12V-low / wake-budget popup alert | **Easy** | ★★★★☆ | HA automation: trigger on `sensor.battery_12v < 11.5` OR `sensor.requests_remaining_today < 50` → `browser_mod.popup` with `tag: vag_alert`, `right_button_action: vag_connect.refresh_now`, `user_id: person.prash`. | **Doc/example** in v1.18.0 README, no code change. |
| **b** | NFC tap → quick-command sheet | **Easy** | ★★★★★ | `tag.scanned` automation → `browser_mod.popup` with `content:` set to a `vertical-stack` card hosting our (planned) compact card variant + lock/unlock/climate buttons. | **Lovelace card session** — ship as `examples/nfc-popup.yaml`. |
| **c** | Charging-session "screensaver" auto-open | **Medium** | ★★★☆☆ | Trigger on `binary_sensor.charging_active` ON → `browser_mod.sequence` ⇒ `set_theme dark` → `navigate /vehicle-dashboard/charging` → optional fullscreen popup with vehicle card. Need to scope `browser_id` to garage tablet only (avoid hijacking phones). | **Doc-mention** + cookbook entry. |
| **d** | Per-browser theme switching (driver tablet vs home tablet) | **Easy** | ★★★☆☆ | `browser_mod.set_theme` per `browser_id`. Pure browser_mod feature, our integration just exposes recommended theme names in a script template. | **Doc-mention** only. |
| **e** | Confirm-before-send popup for `vag_connect.send_destination` (#36) | **Medium** | ★★★★★ | `fire-dom-event` *Browser* call → `browser_mod.popup` with ha-form `content:` (POI fields) + `right_button_action: vag_connect.send_destination` using form `data` injection. Confirms destructive action before hitting Cariad backend. | **v1.18.0** as optional script + doc snippet (lowers #36 misfire risk). |

Cumulative: 4× easy/medium adds, all opt-in, no Python code in the integration required for any of (a)–(e).

---

## E) Cross-pollination ideas with our planned custom card

1. **Card-config example** in card README under `## Browser Mod recipes`:
   - `tap_action: { action: fire-dom-event, browser_mod: { service: browser_mod.popup, data: { popup_card_id: vag-detailed-status } } }` — opens a fullscreen detail variant when the compact tile is tapped.
2. **Built-in `ultimate_vag_card` "popup mode"**: card config flag `compact_with_detail_popup: true` auto-wires the `tap_action` above and ships a default `popup-card` template the user pastes into their dashboard.
3. **Action-shortcuts panel inside popup**: the card emits a `vertical-stack` slot specifically sized for `initial_style: wide`, so `popup_card_id`-based reuse "just works".
4. **Form-driven destination popup recipe** (couples with use-case e): example `popup` with `content: !input { schema: [name, address] }` and a `right_button_action` calling our service.
5. **Optional dependency note** in card README: "Browser Mod is **not required** but unlocks the popup/quick-action recipes below."
6. **Joint demo dashboard YAML** in `docs/lovelace-example.yaml` (already exists) — add a "with browser_mod" section gated behind a YAML comment block.

---

## F) Recommended depth

**Doc-mention + opt-in recipes.** Specifically:
- **NOT** a hard dependency of `vag-connect-ha` (would scare off users who run HA on a single browser).
- **NOT** a soft dependency in `manifest.json` either — there is no API call from our Python code into browser_mod. The interaction is purely automation/dashboard wiring.
- **Doc-mention** in the integration README ("Optional: enhanced UX with Browser Mod") + a `docs/recipes/browser-mod.md` cookbook (use cases a–e as copy-paste YAML).
- **Optional dependency note** in the future card README (separate repo) once that ships.

Effort for v1.18.0: ~1–2 hours to write the cookbook page + 5-line README mention. Zero Python.

---

## G) Open questions

1. Does the planned card need `popup_card_id` registration logic baked into card-config — or do we expect users to define their `popup-card` in dashboard YAML manually? (UX vs. simplicity trade-off.)
2. For use-case (e): is `send_destination` payload simple enough (POI fields) to fit a clean `ha-form` schema, or do we need a card-based form for lat/lon picker?
3. Should we ship the cookbook with `tag:` namespacing (`tag: vag_alert_<vin>`) so multi-vehicle users don't get popups stomping on each other?
4. Tablet-targeted browsers often run as kiosks with persistent Browser IDs — do we want a `vag_connect.assign_primary_browser` script template, or leave that to user wiring?
5. v1 vs v2 wording in our docs — confirm we only document v2 (v1 is end-of-life per upstream README).
