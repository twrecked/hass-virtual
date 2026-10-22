# 🚀 Virtual v0.10.0-alpha.2 — Alarm Control Panel, Button, Select, and Text Platform Expansion

> ### ⚠️ Alpha Release & Community Testing Notice
> **Virtual v0.10 is an active alpha pre-release.**
>
> If you encounter any bugs, regressions, or configuration issues, please [open a GitHub issue](https://github.com/twrecked/hass-virtual/issues) with your configuration snippet and debug logs.
>
> *(Legacy v0.9 documentation is archived in [README_v9.md](README_v9.md)).*

---

## 🌟 What's New in v0.10.0-alpha.2

### 1. Four New Virtual Platforms
Expanded the virtual device platform lineup from 10 to **14 supported platforms**:

1. **`alarm_control_panel` (`AlarmControlPanelEntity`)**:
   - Virtual security alarm panel with configurable PIN codes (`code`), arming exit delays (`arming_time`), and trigger entry delays (`trigger_time`).
   - Supports states: `disarmed`, `armed_home`, `armed_away`, `armed_night`, `armed_vacation`, `arming`, `pending`, and `triggered`.
   - Controllable via native services: `alarm_arm_home`, `alarm_arm_away`, `alarm_arm_night`, `alarm_arm_vacation`, `alarm_disarm`, and `alarm_trigger`.
2. **`button` (`ButtonEntity`)**:
   - Push-button entities to trigger automations and actions.
   - Supports standard device classes (`identify`, `restart`, `update`).
   - Fires a `virtual_button_pressed` event on the Home Assistant event bus with `entity_id` and `name` when pressed.
   - Controllable via the native `button.press` service.
3. **`select` (`SelectEntity`)**:
   - Multi-option dropdown selectors.
   - Configure custom option lists (`options: ["Home", "Away", "Night", "Vacation"]`).
   - Remembers current option across restarts with `persistent: true`.
   - Controllable via the native `select.select_option`, `select.select_first`, `select.select_last`, and `select.select_next` services.
4. **`text` (`TextEntity`)**:
   - Text input entities with customizable string constraints.
   - Supports `min` and `max` character limits.
   - Supports input display modes (`text` or `password`).
   - Supports optional regex validation pattern (`pattern`).
   - Controllable via the native `text.set_value` service.

### 2. Virtual Device Editor Updates
- Added `alarm_control_panel`, `button`, `select`, and `text` platform support to the Visual Device Editor.
- Added new preset templates:
  - **Security Alarm Panel**: Alarm panel with PIN code `1234` and 10s entry/exit delays.
  - **Mode Selector**: Preset dropdown with *Home, Away, Night, Vacation*.
  - **Action Button**: Push-button configured to trigger automations.
  - **Text Input**: Configurable text message field.
- Added options string inputs, text constraints, and alarm PIN/delay fields directly in entity cards.
