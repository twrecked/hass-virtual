# 🚀 Virtual v0.10.0-alpha.1 — Visual Device Editor & Core Architecture Modernization

> ### ⚠️ Alpha Release & Community Testing Notice
> **Virtual v0.10 is a major modernization featuring a dedicated web-based Visual Device Editor, native Home Assistant entity models, and non-blocking asynchronous state storage.**
>
> **This is an active alpha pre-release — please expect evolving features, edge cases, and ongoing polish.**
>
> Community testing and feedback are essential! If you encounter any bugs, state restoration regressions, or configuration issues, please [open a GitHub issue](https://github.com/twrecked/hass-virtual/issues) with your configuration snippet and debug logs.
>
> *(Legacy v0.9 documentation is archived in [README_v9.md](README_v9.md)).*

---

## 🌟 Highlights

### 1. Interactive Web-Based Visual Device Editor
Configure your virtual devices with an intuitive visual tree interface instead of editing raw YAML files:
- **Hosted Cloud Builder:** Live on Google App Engine at **[https://virtual-dot-twrecked-tools.nn.r.appspot.com](https://virtual-dot-twrecked-tools.nn.r.appspot.com)**.
- **One-Click Sync via Home Assistant:** In Home Assistant, click **Configure** on any Virtual group to launch the editor with your existing devices preloaded. Click **Save & Return**, and the editor automatically updates your file on disk and reloads the integration via an authenticated webhook.
- **Preset Device Templates ("Quick Adds"):** One-click generation of common multi-entity devices:
  - *Motion Sensor* (`binary_sensor` + battery `sensor`)
  - *Contact Sensor* (`binary_sensor` + battery `sensor`)
  - *Dimmable & RGB Color Lights*
  - *Ceiling Fan* (speed count, direction, oscillation)
  - *Window Blind & Water Valve* (timed durations and tick intervals)
  - *Smart Power Outlet* (`switch` + power & energy `sensor`s)
  - *Weather Station* (temperature, humidity, atmospheric pressure)
- **Collapsible Device Cards:** Expand or collapse individual devices, or use the **Collapse All / Expand All** action when managing large configuration files.
- **Local & Offline Friendly:**
  - **Local LAN Mode:** Run the editor locally using `python main.py` in the `virtual-device-editor/` folder with zero data leaving your local network.
  - **Manual Copy-Paste Fallback:** No webhooks or network access required—edit visually, click **Copy** or **Download**, and paste into your `/config/virtual.yaml`.

---

### 2. Core Entity Architecture & Bug Squashing
- **Native Platform Inheritance:**
  - `VirtualNumber` refactored to inherit from `(VirtualEntity, NumberEntity)`, using native properties (`_attr_native_value`, `_attr_native_min_value`, `_attr_native_max_value`) and purely asynchronous state updates, eliminating threadpool worker overhead.
  - `VirtualSensor` refactored to inherit from `(VirtualEntity, SensorEntity)` using native properties (`_attr_native_value`, `_attr_native_unit_of_measurement`).
- **Fixed Lock Freezing:** Fixed a bug where configuring a `locking_time` left locks permanently stuck in a locking/unlocking transition due to a coroutine callback error. Added timer cleanup on entity removal.
- **Fixed Lock `async_open` Crash:** Resolved an `AttributeError` in `lock.open`.
- **Immediate State Writing:** Added missing `async_write_ha_state()` calls across `light`, `switch`, `fan`, and `number` service actions.
- **Fixed Service Registration Lookup:** Replaced dictionary `hasattr` checks across platforms with proper key lookups, preventing duplicate service registrations.
- **Cleaned Entity Attributes:** Removed redundant duplication of native Home Assistant properties (`device_class`, `unit_of_measurement`, `brightness`, `color_mode`, etc.) into `extra_state_attributes`.

---

### 3. Non-Blocking Storage & Asynchronous Core
- **Home Assistant Store for Trackers:** Replaced hardcoded storage file paths and synchronous blocking file writes in event listeners with Home Assistant's managed non-blocking `Store` helper and `async_delay_save`.
- **Zero Unmanaged Dependencies:** Replaced `aiofiles` with standard UTF-8 file operations running safely in the threadpool executor via `hass.async_add_executor_job`.
- **Eliminated Global Tracker State:** Removed mutable module-level `global tracker_states` in favor of scoped state.
- **Removed Startup Delays:** Eliminated arbitrary `asyncio.sleep(1)` delay during integration setup.
- **Resolved Tracker Deprecation Warning:** Replaced deprecated `location_name` property override on `VirtualDeviceTracker` with standard `@property def state`.

---

### 4. Global Units & Future HA Standards
- **Centralized Device Class Units:** Unified unit mappings under `DEVICE_CLASS_UNITS` using Home Assistant's global unit constants (`UnitOfTemperature.CELSIUS`, `UnitOfDensity`, `UnitOfRatio`).
- **Temperature Unit Auto-Healing:** Replaced hardcoded `"C"` defaults with `UnitOfTemperature.CELSIUS` (`'°C'`). Added automatic normalization so that any existing configuration or restored state with `"C"`, `"c"`, or `"Â°C"` automatically upgrades to `'°C'` without triggering Home Assistant warnings.
- **HACS & Manifest Modernization:**
  - Added `"render_readme": true` to `hacs.json` so modern HACS displays the full documentation directly in the HACS interface.
  - Added `"integration_type": "helper"` to `manifest.json`.
  - Added full Python 3.12 type annotations (`from __future__ import annotations`).
  - Eliminated all wildcard imports (`from .const import *`).

---

## 🛠️ Testing Checklist for Alpha Testers

1. **State Restoration**: Verify that entities (lights, fans, covers, sensors, numbers, switches) maintain their values across a Home Assistant restart with `persistent: true`.
2. **Visual Device Editor**: Test opening the editor via **Settings -> Devices & Services -> Virtual -> Configure**, adding a device or template, and verifying that clicking **Save & Return** updates your YAML file and reloads the devices automatically.
3. **Manual Fallback**: Test building devices in the editor, clicking **Copy**, pasting into `/config/virtual.yaml`, and reloading via **Developer Tools -> YAML -> Reload Virtual Components**.
4. **Lock & Cover Timers**: Test virtual covers and locks configured with duration/timing transitions to confirm smooth operation.
