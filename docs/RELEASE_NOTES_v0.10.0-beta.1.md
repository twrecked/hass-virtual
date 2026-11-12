# 🚀 Virtual v0.10.0-beta.1 — Beta Stabilization & Linked Entity Fixes

> ### ⚠️ Beta Release & Community Testing Notice
> **Virtual v0.10 has entered beta!**
>
> If you encounter any bugs, regressions, or configuration issues, please [open a GitHub issue](https://github.com/twrecked/hass-virtual/issues).
>
> *(Legacy v0.9 documentation is archived in [docs/README_v9.md](docs/README_v9.md)).*

---

## 🌟 What's New in v0.10.0-beta.1

### 1. Linked Entity Candidate Resolution Fix
* Fixed an issue in `_resolve_switch_id` and `_resolve_sensor_id` where referencing a parent device as a linked switch or power sensor generated a duplicated slug candidate (e.g. `switch.<device>_<device>`) before entities finished registering during startup.
* Sibling entity lookups now cleanly check `if dev_slug != slug` before inserting compound prefixes, allowing direct binding to primary entities like `switch.living_room_tv_outlet`.

### 2. Standardized Appliance Configurations
* Modernized `examples/virtual-sonoff.yaml` so that appliance outlet devices cleanly use concise sub-entity names (`name: Power` and `name: Energy` with `linked_power: "Power"`).
* Updated `examples/virtual-solark.yaml` to reference the standardized power sensor entity IDs in its `linked_loads`.

### 3. Virtual Siren Platform (`siren`)
* Added full virtual `siren` platform support (`VirtualSiren`), expanding `hass-virtual` to **18 Home Assistant entity platforms**.
* **Operational Modes**:
  * **Manual Control (`duration: 0` or omitted)**: Turns on and stays on indefinitely until explicitly turned off via `siren.turn_off`.
  * **Automatic Timed Auto-Off (`duration: N > 0`)**: Automatically shuts off after `N` seconds when triggered via UI toggle or `siren.turn_on`.
  * **Dynamic Duration Overrides**: Respects one-off durations when invoked via `siren.turn_on(duration=X)`.
* **Tone & Volume Features**: Dynamically supports `SirenEntityFeature.TONES` when `available_tones` are provided, and `SirenEntityFeature.VOLUME_SET` when `support_volume_set: true`.
* **Virtual Device Editor Integration**: Fully integrated into the web UI builder with form controls, feature toggles, and a "Security Siren" template.

### 4. Transition to Beta
* Virtual v0.10 core architecture (18 platforms, ADR-0007 entity naming model, simulation engines, and async persistence) is now feature-frozen and entering beta stabilization.
