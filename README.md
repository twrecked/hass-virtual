# **Virtual Devices for Home Assistant**

_Virtual_ is a custom integration for [Home Assistant](https://www.home-assistant.io/) that provides in-memory virtual entities and devices for testing, development, and complex automation prototyping.

![icon](images/virtual-icon.png)

_Virtual_ provides support for 17 distinct entity platforms:
- **Alarm Control Panels**: Virtual security panels with arming/trigger delays and PIN codes.
- **Binary Sensors**: Motion, presence, door, window, smoke, and moisture sensors.
- **Buttons**: Stateless push-buttons to trigger automations and actions.
- **Cameras**: Security and CCTV cameras with snapshot images, fallback test cards, and live HLS stream playback.
- **Climate**: Virtual thermostats and HVAC units with target setpoints, presets, and dynamic heating/cooling action calculation.
- **Covers**: Timed position-based blinds, garage doors, shutters, and shades.
- **Device Trackers**: GPS coordinates and named location zones.
- **Fans**: Multi-speed, oscillating, and reversible fans.
- **Lights**: Dimmable, RGB color (HS), color temperature, and animated effects.
- **Locks**: Lockable doors with optional locking duration and jamming tests.
- **Media Players**: Virtual TVs, speakers, and receivers for silent TTS announcement and automation testing.
- **Numbers**: Configurable sliders and numeric inputs with custom ranges and units.
- **Selects**: Dropdown selectors for modes, states, and presets.
- **Sensors**: Environmental (temperature, humidity, pressure), power, energy, and battery monitors.
- **Switches**: Simple on/off switches and power outlets.
- **Texts**: Configurable text input fields with string length and regex pattern constraints.
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
> Legacy `0.9.x` documentation is archived in [docs/README_v9.md](docs/README_v9.md), and `0.8.x` documentation is in [version-0.8.x](https://github.com/twrecked/hass-virtual/tree/version-0.8.x#readme).

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
  - [Alarm Control Panels](#alarm-control-panels)
  - [Climate](#climate)
  - [Switches](#switches)
  - [Binary Sensors](#binary-sensors)
  - [Buttons](#buttons)
  - [Sensors](#sensors)
  - [Numbers](#numbers)
  - [Selects](#selects)
  - [Texts](#texts)
  - [Lights](#lights)
  - [Locks](#locks)
  - [Cameras](#cameras)
  - [Media Players](#media-players)
  - [Fans](#fans)
  - [Covers](#covers)
  - [Valves](#valves)
  - [Device Trackers](#device-trackers)
- [Legacy YAML Configuration](#legacy-yaml-configuration)
- [Services](#services)
  - [virtual.set_available](#virtualset_available)
  - [virtual.turn_on](#virtualturn_on)
  - [virtual.turn_off](#virtualturn_off)
  - [virtual.toggle](#virtualtoggle)
  - [virtual.set](#virtualset)
  - [virtual.move](#virtualmove)
  - [virtual.set_current_temperature](#virtualset_current_temperature)
  - [virtual.set_sim_speed](#virtualset_sim_speed)
  - [virtual.set_image_url](#virtualset_image_url)
  - [virtual.set_stream_url](#virtualset_stream_url)
  - [virtual.set_load](#virtualset_load)
  - [virtual.run_cycle](#virtualrun_cycle)

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
3. **Major Platform Expansion (17 Supported Platforms)**:
   - Added native support for `alarm_control_panel`, `button`, `camera`, `climate`, `media_player`, `number`, `select`, `text`, and `valve` entities with standard Home Assistant device classes, units, and services.
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

### Alarm Control Panels

Simulates virtual alarm systems with customizable PIN codes and exit/entry delays.

```yaml
House Alarm:
  - platform: alarm_control_panel
    initial_value: disarmed
    code: "1234"
    code_arm_required: false
    arming_time: 10
    trigger_time: 10
```

* `code`: Optional PIN code (e.g. `"1234"`). When defined, entering the code is required to disarm.
* `code_arm_required`: Default `false`. If `true`, entering the code is also required to arm.
* `arming_time`: Optional exit delay in seconds (transitions through `arming` before becoming armed).
* `trigger_time`: Optional entry delay in seconds (transitions through `pending` before becoming `triggered`).
* *Controllable via native `alarm_control_panel.alarm_arm_home`, `alarm_control_panel.alarm_arm_away`, `alarm_control_panel.alarm_arm_night`, `alarm_control_panel.alarm_arm_vacation`, `alarm_control_panel.alarm_disarm`, and `alarm_control_panel.alarm_trigger` services.*

---

### Climate

Simulates virtual thermostats and HVAC units. Automatically computes `hvac_action` (`heating`, `cooling`, `idle`, `off`) dynamically based on ambient room temperature vs. target temperature setpoints.

```yaml
Living Room Thermostat:
  - platform: climate
    initial_value: heat
    initial_temperature: 21
    initial_current_temperature: 19.5
    min_temp: 10
    max_temp: 32
    target_temperature_step: 0.5
    hvac_modes:
      - off
      - heat
      - cool
      - auto
    preset_modes:
      - none
      - eco
      - comfort
      - away
```

* `initial_value`: Initial HVAC mode (`off`, `heat`, `cool`, `auto`).
* `initial_temperature`: Target temperature setpoint.
* `initial_current_temperature`: Initial ambient room temperature.
* `min_temp` / `max_temp`: Bounds for temperature adjustment.
* `target_temperature_step`: Temperature step increment (default `0.5`).
* *Controllable via native `climate.set_temperature`, `climate.set_hvac_mode`, `climate.set_preset_mode`, and `climate.set_fan_mode` services.*
* *Simulate ambient room temperature changes using the custom `virtual.set_current_temperature` service.*

#### Closed-Loop HVAC & House Thermal Simulation
Virtual climate entities can run an active, closed-loop thermal physics engine that models house insulation, outdoor weather leakage, and multi-stage heating/cooling with realistic electrical power draws:

```yaml
House HVAC:
  - platform: climate
    name: House Thermostat
    initial_value: "heat"
    initial_temperature: 21.0
    initial_current_temperature: 20.0
    indoor_sensor: "Indoor Temperature"   # Syncs indoor temperature in real-time
    outdoor_sensor: "Outdoor Temperature" # Reacts to changing outdoor weather
    power_sensor: "HVAC Power"           # Syncs active stage power wattage (W)
    sim_speed: 1.0                       # Simulation speed (e.g. 10.0 for 10x fast forward)
    house_leakage_rate: 0.3              # °C/hr drift per 10°C indoor/outdoor delta
  - platform: sensor
    name: Indoor Temperature
    class: temperature
    unit_of_measurement: "°C"
  - platform: sensor
    name: Outdoor Temperature
    class: temperature
    unit_of_measurement: "°C"
    initial_value: "5.0"
  - platform: sensor
    name: HVAC Power
    class: power
    unit_of_measurement: "W"
```

* **Passive Heat Transfer**: The house naturally gains or loses heat towards the `outdoor_sensor` temperature based on insulation (`house_leakage_rate`). Without active HVAC, indoor temperature will never drift past the outdoor ambient reading.
* **Intelligent Staging**:
  * **Stage 2 Heat** (3.0°C/hr, ~3800W): Activates when outdoor is freezing (<0°C) or indoor is >1.5°C below target setpoint.
  * **Stage 1 Heat** (1.5°C/hr, ~1800W): Activates during moderate cold or small setpoint deltas.
  * **Stage 2 Cool** (-3.0°C/hr, ~2800W): Activates during heatwaves (>30°C) or when indoor is >1.5°C above target setpoint.
  * **Stage 1 Cool** (-1.5°C/hr, ~1400W): Activates during mild cooling needs.
  * **Fan** (-0.2°C/hr, ~120W): Activates in `fan_only` mode.
  * **Idle/Standby** (~10W) / **Off** (0W).
* **Sensor Synchronization**: Automatically updates both the linked `indoor_sensor` and `power_sensor` in lockstep.
* *Control simulation acceleration via the `virtual.set_sim_speed` service.*

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

#### Auto-Off Timeouts & Device Gating
Binary sensors (such as motion, sound, or occupancy detectors) can automatically reset back to `off` after a configured duration, and optionally gate their activation to another device (such as a camera or power switch):

```yaml
Front Porch Camera:
  - platform: camera
    name: Porch Camera
    image_url: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=640"

  - platform: binary_sensor
    name: Porch Motion
    class: motion
    off_delay: 15                      # Automatically resets back to 'off' after 15 seconds
    linked_entity: Porch Camera        # Can only trigger when Porch Camera is powered on

  - platform: binary_sensor
    name: Porch Sound
    class: sound
    off_delay: 5
    linked_entity: Porch Camera
```

* `off_delay`: Duration in seconds before the sensor automatically turns back `off`. If triggered again while already active, the countdown timer resets and extends.
* `linked_entity`: Sibling entity name or entity ID (e.g. `camera.porch_camera`, `switch.plug`). The binary sensor can only turn on when the linked entity is energized/on. If the linked entity powers off while motion is active, the binary sensor immediately clears to `off`.
* *Controllable via `virtual.turn_on` (with optional `duration` override), `virtual.turn_off`, and `virtual.toggle`.*

---

### Buttons

Simulates push-button trigger entities (supporting device classes `identify`, `restart`, `update`). When pressed, fires the `virtual_button_pressed` event on the Home Assistant event bus for automations.

```yaml
System Controls:
  - platform: button
    class: restart
```

*Controllable via the native `button.press` service.*

---

### Sensors

Simulates numeric or string sensor entities. Standard device classes automatically assign appropriate units (`temperature` -> `°C`, `humidity` -> `%`, `power` -> `W`, `battery` -> `%`).

```yaml
Outdoor Weather:
  - platform: sensor
    class: temperature
    initial_value: 21.5
    unit_of_measurement: '°C'
```

#### Appliance Load Simulation & Power Profiling
Virtual sensors can simulate realistic appliance loads linked to a controlling switch (e.g. Sonoff smart plugs or relay-switched water heaters). The sensor automatically drops to `0 W` when the linked switch is turned `off`, and simulates `standby` vs `active` power draws with optional noise/jitter when the switch is energized.

**Example 1: Smart Plug with TV Load**
```yaml
Living Room TV Outlet:
  - platform: switch
    name: TV Plug
    class: outlet
    initial_value: "on"
  - platform: sensor
    name: TV Power
    class: power
    unit_of_measurement: "W"
    linked_switch: "TV Plug"
    standby_power: 3.5
    active_power: 140.0
    initial_load: "standby"
    variance: 1.5
```

**Example 2: Water Heater with Recurring Scheduled Duty Cycle**
```yaml
Utility Water Heater:
  - platform: switch
    name: Water Heater Switch
    initial_value: "on"
  - platform: sensor
    name: Water Heater Power
    class: power
    unit_of_measurement: "W"
    linked_switch: "Water Heater Switch"
    standby_power: 0.0
    active_power: 2400.0
    cycle_duration: 600      # 10 minutes active
    cycle_interval: 3600     # Repeats every 1 hour
    cycle_align: "hour"      # Aligned to :00 on the clock
```

* `linked_switch`: Name or entity ID of the switch supplying mains power.
* `standby_power`: Numeric wattage when switch is energized and appliance is idling.
* `active_power`: Numeric wattage when appliance is active/running.
* `initial_load`: Initial appliance state (`standby`, `active`, or `off`).
* `variance`: Optional random uniform jitter (`±W`) so power graphs look authentic.
* `cycle_duration`: Duration in seconds of the active load cycle.
* `cycle_interval`: Frequency in seconds for recurring cycles.
* `cycle_align`: `"hour"` (aligns active phase with `:00` past the hour) or `"interval"` (relative to startup).
* *Exposes `load_state`, `control_mode`, `cycle_active`, `cycle_remaining`, and `next_cycle_start` in attributes for automated testing in AppDaemon and automations.*
* *Controllable via `virtual.set`, `virtual.set_load`, and `virtual.run_cycle`.*

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

### Selects

Simulates multi-option dropdown selectors. Ideal for home modes, states, and automation presets.

```yaml
House Mode:
  - platform: select
    options: ["Home", "Away", "Night", "Vacation"]
    initial_value: "Home"
```

*Controllable via the native `select.select_option`, `select.select_first`, `select.select_last`, and `select.select_next` services.*

---

### Texts

Simulates text input fields with optional min/max lengths, regex validation patterns, and display mode (`text` or `password`).

```yaml
Announcement:
  - platform: text
    initial_value: "Welcome guests!"
    min: 0
    max: 255
    mode: text
```

*Controllable via the native `text.set_value` service.*

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

### Cameras

Simulates security and CCTV cameras for testing dashboard Picture Entity Cards, camera proxy streaming, and live feeds.

```yaml
Front Porch Camera:
  - platform: camera
    image_url: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=640"
    stream_url: "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
```

* `image_url`: Optional HTTP(S) image URL or local file path (e.g. `/local/camera.jpg` or `/config/www/camera.jpg`). Used by Picture Entity Cards and snapshot previews. When omitted, an embedded test placeholder image is served.
* `stream_url`: Optional stream source URL (HLS `.m3u8`, RTSP, or HTTP MP4). Defaults out-of-the-box to the public Mux Big Buck Bunny HLS test stream (`https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8`). Set to `none` or empty string `""` to disable live streaming and operate snapshot-only.
* `initial_value`: Optional initial state (`idle` by default, or `off`).
* *Controllable via native `camera.turn_on` and `camera.turn_off` services, as well as `virtual.set_image_url` and `virtual.set_stream_url`.*

---

### Media Players

Simulates TVs, speakers, and media players. Ideal for testing automations, volume sync, and silent TTS / announcement testing without sounding real speakers.

```yaml
Living Room TV:
  - platform: media_player
    class: tv
    initial_value: idle
    initial_volume: 0.4
    source_list:
      - TV
      - HDMI 1
      - HDMI 2
      - Netflix
      - YouTube
    sound_mode_list:
      - Standard
      - Cinema
      - Night
```

* `class`: Optional device class (`tv`, `speaker`, `receiver`).
* `initial_value`: Initial state (`off`, `on`, `idle`, `playing`, `paused`).
* `initial_volume`: Volume slider level from `0.0` to `1.0`.
* `source_list`: Optional list of selectable input sources.
* `sound_mode_list`: Optional list of selectable sound modes.
* *Controllable via native `media_player.turn_on`, `media_player.turn_off`, `media_player.media_play`, `media_player.media_pause`, `media_player.media_stop`, `media_player.volume_set`, `media_player.volume_mute`, `media_player.select_source`, `media_player.select_sound_mode`, and `media_player.play_media` services.*

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
Turns on a virtual binary sensor, with an optional duration parameter to pulse the sensor for a specific number of seconds before resetting to off.

* **Target**: Virtual binary sensor entities
* **Fields**:
  * `duration`: Optional seconds to stay on before resetting to off (overrides default `off_delay`).

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

### `virtual.set_current_temperature`
Sets the current ambient temperature of a virtual climate entity.

* **Target**: Virtual climate entities
* **Fields**:
  * `temperature`: Number representing the new ambient room temperature (e.g. `19.5`).

### `virtual.set_image_url`
Sets the still image URL or local file path for a virtual camera.

* **Target**: Virtual camera entities
* **Fields**:
  * `image_url`: HTTP(S) URL or local path to the still snapshot image.

### `virtual.set_stream_url`
Sets the live stream URL for a virtual camera.

* **Target**: Virtual camera entities
* **Fields**:
  * `stream_url`: HLS, RTSP, or HTTP stream URL (or `""` / `none` to disable streaming).

### `virtual.set_load`
Sets the load state (`active`, `standby`, `off`, or `auto` to resume scheduled duty cycles) or injects custom power into an appliance power sensor.

* **Target**: Virtual power sensor entities
* **Fields**:
  * `state`: Operating state (`active`, `standby`, `off`, `auto`).
  * `power`: Optional wattage override.

### `virtual.run_cycle`
Triggers an active appliance load cycle for a specified duration (in seconds), after which the sensor automatically returns to standby or resumes its background schedule.

* **Target**: Virtual power sensor entities
* **Fields**:
  * `duration`: Run duration in seconds (optional; defaults to `cycle_duration`).

### `virtual.set_sim_speed`
Sets the simulation speed multiplier for a virtual climate entity with thermal modeling.

* **Target**: Virtual climate entities
* **Fields**:
  * `speed`: Float multiplier (e.g. `1.0` for real-time, `10.0` for 10x speed).
