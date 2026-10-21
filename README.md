# **Virtual Devices for Home Assistant**

_Virtual_ is a custom integration for [Home Assistant](https://www.home-assistant.io/) that provides in-memory virtual entities and devices for testing, development, and complex automation prototyping.

![icon](images/virtual-icon.png)

_Virtual_ provides support for 10 distinct entity platforms:
- **Binary Sensors**: Motion, presence, door, window, smoke, and moisture sensors.
- **Covers**: Timed position-based blinds, garage doors, shutters, and shades.
- **Device Trackers**: GPS coordinates and named location zones.
- **Fans**: Multi-speed, oscillating, and reversible fans.
- **Lights**: Dimmable, RGB color (HS), color temperature, and animated effects.
- **Locks**: Lockable doors with optional locking duration and jamming tests.
- **Numbers**: Configurable sliders and numeric inputs with custom ranges and units.
- **Sensors**: Environmental (temperature, humidity, pressure), power, energy, and battery monitors.
- **Switches**: Simple on/off switches and power outlets.
- **Valves**: Timed water and gas valves with position reporting.

---

> ### ⚠️ Virtual `v0.10.0-alpha` Notice
>
> **Virtual v0.10 modernizes the integration with native Home Assistant entity models, an interactive web-based Visual Device Editor, and non-blocking asynchronous state storage.**
>
> **This is an active alpha release — community testing and feedback are welcome!**
>
> If you encounter issues, regressions, or unexpected behavior, please [open a GitHub issue](https://github.com/twrecked/hass-virtual/issues).
>
> Legacy `0.9.x` documentation is archived in [README_v9.md](README_v9.md), and `0.8.x` documentation is in [version-0.8.x](https://github.com/twrecked/hass-virtual/tree/version-0.8.x#readme).

---

# Table Of Contents

- [Introduction](#introduction)
- [What's New in v0.10](#whats-new-in-v010)
- [Installing the Integration](#installing-the-integration)
  - [HACS (Recommended)](#hacs-recommended)
  - [Manual Installation](#manual-installation)
- [Adding the Integration](#adding-the-integration)
- [Visual Device Editor](#visual-device-editor)
  - [One-Click Sync via Home Assistant](#1-one-click-sync-via-home-assistant-recommended)
  - [Manual Copy-Paste / Offline Fallback](#2-manual-copy-paste--offline-fallback-no-webhooks-needed)
  - [Running the Editor Locally on Your LAN](#3-running-the-editor-locally-on-your-lan)
  - [Device Templates & Collapsible Cards](#4-device-templates--collapsible-cards)
- [Entity Configuration & File Layout](#entity-configuration--file-layout)
  - [File Structure](#file-structure)
  - [Common Attributes](#common-attributes)
  - [Switches](#switches)
  - [Binary Sensors](#binary-sensors)
  - [Sensors](#sensors)
  - [Numbers](#numbers)
  - [Lights](#lights)
  - [Locks](#locks)
  - [Fans](#fans)
  - [Covers](#covers)
  - [Valves](#valves)
  - [Device Trackers](#device-trackers)
- [Legacy YAML Configuration](#legacy-yaml-configuration)
- [Services](#services)

---

# Introduction

Virtual devices act like real physical devices in Home Assistant, allowing you to test automations, simulate presence and sensor triggers, mock complex devices, and verify dashboard setups without physical hardware.

All entity states are maintained in-memory and can persist cleanly across Home Assistant restarts.

---

# What's New in v0.10

1. **Visual Device Editor**:
   - A dedicated web application for building and managing your virtual devices and entities visually.
   - Hosted in the cloud at **[https://virtual-dot-twrecked-tools.nn.r.appspot.com](https://virtual-dot-twrecked-tools.nn.r.appspot.com)** or runnable locally on your home network.
2. **Options Flow & Webhook Sync**:
   - Clicking **Configure** on any Virtual group in Home Assistant launches the visual editor preloaded with your YAML.
   * Clicking **Save & Return** in the editor writes your changes to disk and reloads the integration automatically via an authenticated webhook.
3. **Number and Valve Platforms**:
   - Native support for `number` and `valve` entities with standard Home Assistant device classes and units.
4. **Strict Home Assistant & Python Modernization**:
   - Entities now directly inherit from core entity classes (`NumberEntity`, `SensorEntity`), eliminating threadpool worker overhead.
   - State persistence and storage use Home Assistant's managed non-blocking `Store` helper and async executor, eliminating the external `aiofiles` dependency.
   - Full modern typing (`from __future__ import annotations`), unified global device-class units, and hardened state restoration against null or invalid values across restarts.

---

# Installing the Integration

### HACS (Recommended)

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

_Virtual_ is available in the default HACS store. Search for "Virtual Components" under Integrations and download the latest release.

### Manual Installation

Copy the `custom_components/virtual` directory into your Home Assistant `/config/custom_components/` directory and restart Home Assistant.

---

# Adding the Integration

1. In Home Assistant, navigate to **Settings -> Devices & Services**.
2. Click **Add Integration** and search for **Virtual Components**.
3. Enter a **Group Name** (e.g. `Main Virtual Devices`) and the path to your YAML file (defaults to `/config/virtual.yaml`).
4. Click **Submit**. If the file does not exist, an initial file will be created automatically.

You can add multiple integration entries to separate different groups of devices into different files (e.g., `lighting.yaml`, `sensors.yaml`).

---

# Visual Device Editor

The **Virtual Device Editor** provides a visual tree interface for adding, configuring, and organizing devices and child entities without editing YAML by hand.

Hosted version: **[https://virtual-dot-twrecked-tools.nn.r.appspot.com](https://virtual-dot-twrecked-tools.nn.r.appspot.com)**

```
┌────────────────────────────────────────────────────────────────────────┐
│ Virtual Device Editor                      [Templates] [Save & Return] │
├────────────────────────────────────────────────────────────────────────┤
│ ▼ Living Room Motion                              2 entities   [Delete]│
│   ├── [BINARY_SENSOR] Motion Detector (class: motion, initial: off)    │
│   └── [SENSOR]        Battery Level   (class: battery, unit: %)        │
│                                                                        │
│ ▶ Ceiling Fan                                     1 entity     [Delete]│
└────────────────────────────────────────────────────────────────────────┘
```

### 1. One-Click Sync via Home Assistant (Recommended)

1. In Home Assistant, go to **Settings -> Devices & Services -> Virtual**.
2. Click **Configure** on any virtual group.
3. Click the **Open Virtual Device Editor** link to open your devices in the editor.
4. Make your changes visually (add devices, apply templates, tweak attributes).
5. Click **Save & Return** in the editor. The editor POSTs your updated configuration to Home Assistant, updates your file on disk, and automatically reloads the integration.
6. Click **Submit** in Home Assistant to close the options dialog.

### 2. Manual Copy-Paste / Offline Fallback (No Webhooks Needed)

If your Home Assistant instance is not accessible from the browser or you prefer not to use webhooks:

1. Open the editor: **[https://virtual-dot-twrecked-tools.nn.r.appspot.com](https://virtual-dot-twrecked-tools.nn.r.appspot.com)**.
2. Click **Import YAML** and paste your current `virtual.yaml` content (or start fresh with templates).
3. Edit your devices visually with real-time schema validation.
4. Click **Copy** in the top bar to copy the generated YAML to your clipboard (or click **Download** to save `virtual.yaml`).
5. Open your `/config/virtual.yaml` file in Home Assistant (using File Editor, Studio Code Server, Samba, or SSH) and paste the updated content.
6. In Home Assistant, go to **Settings -> Devices & Services -> Virtual**, click the three dots, and select **Reload**.

### 3. Running the Editor Locally on Your LAN

If you want the convenience of one-click sync without any cloud traffic:

1. Start the editor locally on your machine or home server:
   ```bash
   cd virtual-device-editor
   pip install -r requirements.txt
   python main.py
   ```
   *The editor starts at `http://localhost:8080` (and on your local network IP).*
2. In Home Assistant, click **Configure** on your Virtual group.
3. Change **Editor URL** to your local address (e.g. `http://127.0.0.1:8080` or `http://192.168.1.X:8080`) and click **Submit**.
4. Click the link to open your local editor with one-click local webhook sync.

### 4. Device Templates & Collapsible Cards

* **Collapsible Cards**: Click the chevron next to any device title to collapse or expand it. Use the **Collapse All / Expand All** button in the top bar when working with large device lists.
* **Quick-Add Templates**:
  * *Motion Sensor* (`binary_sensor` motion + `sensor` battery)
  * *Contact Sensor* (`binary_sensor` door + `sensor` battery)
  * *Dimmable Light* & *RGB Color Light*
  * *Ceiling Fan* (multi-speed, direction, oscillation)
  * *Window Blind* (timed position cover)
  * *Water Valve* (timed position valve)
  * *Power Outlet* (`switch` + power & energy sensors)
  * *Weather Station* (temperature, humidity, atmospheric pressure)

---

# Entity Configuration & File Layout

### File Structure

A standard `virtual.yaml` file defines devices, each containing one or more entity platforms:

```yaml
version: 1
devices:
  Living Room Multi Sensor:
    - platform: binary_sensor
      name: Living Room Motion
      initial_value: 'off'
      class: motion
    - platform: sensor
      name: Living Room Temperature
      initial_value: 21
      class: temperature
      unit_of_measurement: '°C'
    - platform: sensor
      name: Living Room Battery
      initial_value: 100
      class: battery
      unit_of_measurement: '%'
```

* **Device Groupings**: Entities listed under a device name share the same parent device in Home Assistant's Device Registry.
* **Entity Names**: The `name` parameter on an entity is optional. If omitted, Home Assistant creates a clean entity name combining the device name and the entity type/class (e.g. `Living Room Multi Sensor Motion`).

---

### Common Attributes

All entity types support the following common configuration options:

| Attribute | Type | Default | Description |
|---|---|---|---|
| `name` | string | Optional | Friendly name for the entity. |
| `initial_value` | any | *Platform default* | Value assigned on first creation or if state is not restored. |
| `persistent` | boolean | `true` | When `true`, the entity state is saved across Home Assistant restarts. |
| `initial_availability` | boolean | `true` | When `false`, the entity starts in an `unavailable` state. |

---

### Switches

Simulates standard power switches or outlets.

```yaml
Coffee Maker:
  - platform: switch
    initial_value: 'off'
    class: outlet
```

---

### Binary Sensors

Simulates on/off state sensors supporting all standard Home Assistant device classes (`motion`, `door`, `window`, `presence`, `smoke`, `moisture`, `occupancy`, etc.).

```yaml
Front Door:
  - platform: binary_sensor
    initial_value: 'off'
    class: door
```

*Controllable via the `virtual.turn_on`, `virtual.turn_off`, and `virtual.toggle` services.*

---

### Sensors

Simulates numeric or string sensor entities. Standard device classes automatically assign appropriate units (`temperature` -> `°C`, `humidity` -> `%`, `power` -> `kW`, `battery` -> `%`).

```yaml
Outdoor Weather:
  - platform: sensor
    class: temperature
    initial_value: 21.5
    unit_of_measurement: '°C'
```

*Controllable via the `virtual.set` service.*

---

### Numbers

Simulates numeric inputs and sliders with custom bounds.

```yaml
Target Temperature:
  - platform: number
    min: 15
    max: 30
    initial_value: 21
    class: temperature
    unit_of_measurement: '°C'
```

*Controllable via the native `number.set_value` service.*

---

### Lights

Simulates virtual lights with brightness, color temperature, and full RGB/HS color support.

```yaml
Living Room Accent:
  - platform: light
    initial_value: 'off'
    support_brightness: true
    initial_brightness: 255
    support_color: true
    initial_color: [0, 100]
    support_color_temp: true
    initial_color_temp: 3000
    support_effect: true
    initial_effect: "none"
```

*Controllable via native `light.turn_on` and `light.turn_off` services.*

---

### Locks

Simulates door locks with optional realistic lock movement duration and jamming tests.

```yaml
Front Door Lock:
  - platform: lock
    initial_value: locked
    locking_time: 2
    jamming_test: 10
```

* `locking_time`: Optional duration in seconds for the locking/unlocking transition phase.
* `jamming_test`: Positive integer; triggers a random jamming failure approximately 1 out of every X attempts.
* *Controllable via native `lock.lock`, `lock.unlock`, and `lock.open` services.*

---

### Fans

Simulates multi-speed, reversible, and oscillating fans.

```yaml
Living Room Ceiling Fan:
  - platform: fan
    initial_value: 'off'
    speed_count: 4
    direction: true
    oscillate: true
```

* `speed_count`: Number of speed tiers (e.g. 4 tiers = 25%, 50%, 75%, 100%).
* *Controllable via native `fan.turn_on`, `fan.turn_off`, `fan.set_percentage`, `fan.set_direction`, and `fan.oscillate` services.*

---

### Covers

Simulates blinds, shutters, garage doors, and shades with realistic opening and closing travel times.

```yaml
Patio Blind:
  - platform: cover
    initial_value: closed
    class: blind
    open_close_duration: 15
    open_close_tick: 1
```

* `open_close_duration`: Travel time in seconds from fully open to fully closed.
* `open_close_tick`: Time interval in seconds between simulated position update events.
* *Controllable via native `cover.open_cover`, `cover.close_cover`, `cover.stop_cover`, and `cover.set_cover_position` services.*

---

### Valves

Simulates water and gas valves with travel durations and position reporting.

```yaml
Garden Irrigation Valve:
  - platform: valve
    initial_value: closed
    class: water
    open_close_duration: 5
    open_close_tick: 1
```

*Controllable via native `valve.open_valve`, `valve.close_valve`, `valve.stop_valve`, and `valve.set_valve_position` services.*

---

### Device Trackers

Simulates GPS coordinates or named zones for presence testing.

```yaml
Family Member:
  - platform: device_tracker
    initial_value: home
```

*Controllable via the `virtual.move` service.*

---

# Legacy YAML Configuration

For backward compatibility with older configurations, you can continue managing entities directly under platform keys in `configuration.yaml` by setting:

```yaml
virtual:
  yaml_config: true
```

When `yaml_config: false` (the default), Home Assistant automatically uses the modern Config Flow and `virtual.yaml` device files.

---

# Services

The integration provides the following custom services:

### `virtual.set_available`
Sets the availability state of any virtual entity.

* **Target**: Any virtual entity
* **Fields**:
  * `value`: Boolean (`true` or `false`)

### `virtual.turn_on`
Turns on a virtual binary sensor.

* **Target**: Virtual binary sensor entities

### `virtual.turn_off`
Turns off a virtual binary sensor.

* **Target**: Virtual binary sensor entities

### `virtual.toggle`
Toggles a virtual binary sensor.

* **Target**: Virtual binary sensor entities

### `virtual.set`
Sets the state value of a virtual sensor.

* **Target**: Virtual sensor entities
* **Fields**:
  * `value`: String or number representing the new sensor value.

### `virtual.move`
Moves a virtual device tracker to a new zone or GPS coordinates.

* **Target**: Virtual device tracker entities
* **Fields**:
  * `location`: Named zone or location string (e.g. `home`, `work`, `away`).
  * `gps`: Object containing `latitude` and `longitude`.
  * `gps_accuracy`: Optional accuracy radius in meters.
