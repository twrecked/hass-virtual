# AI Agent Instructions for Creating Virtual Configurations

These guidelines instruct AI agents on how to generate, validate, and structure YAML configuration files (`virtual.yaml`) for the Home Assistant **Virtual** integration.

---

## 1. File Structure & Root Schema

Every configuration file must follow this top-level layout:

```yaml
version: 1
devices:
  <Device Name 1>:
    - platform: <platform_1>
      name: <entity_name_1>
      ...
    - platform: <platform_2>
      name: <entity_name_2>
      ...
  <Device Name 2>:
    - platform: <platform_3>
      name: <entity_name_3>
      ...
```

- **`version`**: Must be integer `1`.
- **`devices`**: A dictionary mapping device friendly names to a list of entity configurations belonging to that device.
- Each device in the `devices` dictionary is created as a unified hardware device in Home Assistant's Device Registry.

---

## 2. Universal Entity Parameters

All virtual entities across all 16 platforms support these common parameters:

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `platform` | string | **Yes** | — | One of the 16 supported platforms listed below. |
| `name` | string | **Yes** | — | Friendly name of the entity. |
| `initial_value` | string / number | No | Platform default | Initial state or value when first created or when not persisting. |
| `persistent` | boolean | No | `true` | Whether state is saved across Home Assistant restarts. |
| `initial_availability` | boolean | No | `true` | Whether the entity starts in an available state. |

---

## 3. Platform Specifications (All 16 Platforms)

### 1. `binary_sensor`
Binary true/false sensors (motion, doors, presence, etc.).
- **`initial_value`**: `'on'` or `'off'` (default: `'off'`)
- **`class`**: Standard Home Assistant binary sensor class (`motion`, `door`, `window`, `moisture`, `smoke`, `occupancy`, `presence`, `plug`, `power`, `battery`, etc.).
```yaml
- platform: binary_sensor
  name: Front Motion
  class: motion
  initial_value: "off"
```

### 2. `sensor`
Read-only numeric or text sensors.
- **`initial_value`**: Starting value (default: `'0'`)
- **`class`**: Device class (`temperature`, `humidity`, `pressure`, `power`, `energy`, `battery`, `voltage`, `current`, etc.).
- **`unit_of_measurement`**: Standard unit string (e.g. `'°C'`, `'%'`, `'W'`, `'kWh'`, `'hPa'`, `'V'`, `'A'`).
```yaml
- platform: sensor
  name: Living Room Temperature
  class: temperature
  unit_of_measurement: "°C"
  initial_value: 21.5
```

### 3. `switch`
Standard controllable on/off switch or smart outlet.
- **`initial_value`**: `'on'` or `'off'` (default: `'off'`)
- **`class`**: `'switch'` or `'outlet'`.
```yaml
- platform: switch
  name: Coffee Maker Outlet
  class: outlet
  initial_value: "off"
```

### 4. `number`
Interactive slider or numeric input.
- **`initial_value`**: Numeric value (default: `0`)
- **`min`**: Minimum value (default: `0`)
- **`max`**: Maximum value (default: `100`)
- **`step`**: Increment step (default: `1`)
- **`unit_of_measurement`**: Unit string (optional)
- **`class`**: Sensor/number device class (optional)
```yaml
- platform: number
  name: Target Humidity
  min: 30
  max: 80
  step: 5
  unit_of_measurement: "%"
  initial_value: 50
```

### 5. `light`
Virtual lighting with dimming, RGB color, color temperature, and effects.
- **`initial_value`**: `'on'` or `'off'` (default: `'off'`)
- **`support_brightness`**: boolean (enable brightness slider, 0–255)
- **`initial_brightness`**: integer `0`–`255`
- **`support_color`**: boolean (enable full HS / RGB color picker)
- **`support_color_temp`**: boolean (enable Kelvin/mired color temperature slider)
- **`support_white_value`**: boolean (enable white channel)
- **`support_effect`**: boolean (enable lighting effects dropdown)
- **`initial_effect`**: string
```yaml
- platform: light
  name: Living Room Lamp
  initial_value: "off"
  support_brightness: true
  initial_brightness: 200
  support_color: true
  support_color_temp: true
```

### 6. `fan`
Multi-speed, oscillating, and reversible ceiling or desk fans.
- **`initial_value`**: `'on'` or `'off'` (default: `'off'`)
- **`speed`**: boolean (enable speed control, percentage-based)
- **`speed_count`**: integer (e.g. `3` or `4` speeds)
- **`direction`**: boolean (enable forward / reverse)
- **`oscillate`**: boolean (enable oscillation toggle)
```yaml
- platform: fan
  name: Master Bedroom Fan
  initial_value: "off"
  speed: true
  speed_count: 3
  oscillate: true
```

### 7. `cover`
Timed motorized blinds, garage doors, shutters, or shades.
- **`initial_value`**: `'open'` or `'closed'` (default: `'closed'`)
- **`class`**: `'blind'`, `'garage'`, `'shutter'`, `'shade'`, `'door'`, `'window'`, `'gate'`.
- **`open_close_duration`**: integer (seconds to travel from 0% to 100%, e.g. `15`)
- **`open_close_tick`**: integer (refresh interval in seconds during movement, e.g. `1`)
```yaml
- platform: cover
  name: Living Room Blinds
  class: blind
  initial_value: "closed"
  open_close_duration: 15
  open_close_tick: 1
```

### 8. `valve`
Timed motorized water or gas shutoff valves.
- **`initial_value`**: `'open'` or `'closed'` (default: `'closed'`)
- **`class`**: `'water'` or `'gas'`
- **`open_close_duration`**: integer travel duration in seconds
- **`open_close_tick`**: refresh tick interval
```yaml
- platform: valve
  name: Main Water Shutoff
  class: water
  initial_value: "open"
  open_close_duration: 5
  open_close_tick: 1
```

### 9. `lock`
Lockable doors and gates with optional jam simulation.
- **`initial_value`**: `'locked'` or `'unlocked'` (default: `'locked'`)
- **`locking_time`**: integer (seconds to transition between locked and unlocked)
- **`jamming_test`**: integer (seconds to simulate jammed state, or `0` for none)
```yaml
- platform: lock
  name: Front Door Lock
  initial_value: "locked"
  locking_time: 2
```

### 10. `device_tracker`
GPS coordinates or named zone tracker.
- **`initial_location`**: Zone name (e.g. `'home'`, `'not_home'`, `'work'`)
- **`initial_latitude`**: float (e.g. `37.7749`)
- **`initial_longitude`**: float (e.g. `-122.4194`)
```yaml
- platform: device_tracker
  name: Commuter Vehicle
  initial_location: "home"
  initial_latitude: 37.7749
  initial_longitude: -122.4194
```

### 11. `climate`
Full HVAC thermostat with target temperature and modes.
- **`initial_value`**: Initial HVAC mode (`heat`, `cool`, `auto`, `'off'`)
- **`initial_temperature`**: Target temperature (float, e.g. `21.0`)
- **`initial_current_temperature`**: Ambient temperature (float, e.g. `19.5`)
- **`min_temp`**: Minimum setpoint (default: `10`)
- **`max_temp`**: Maximum setpoint (default: `32`)
- **`target_temperature_step`**: Setpoint resolution (default: `0.5`)
- **`hvac_modes`**: List of supported modes (`['off', 'heat', 'cool', 'auto']`)
- **`preset_modes`**: List of supported presets (`['none', 'eco', 'comfort', 'away']`)
- **`fan_modes`**: List of fan modes (`['auto', 'low', 'high']`)
```yaml
- platform: climate
  name: Home Thermostat
  initial_value: heat
  initial_temperature: 21.0
  initial_current_temperature: 19.5
  min_temp: 10
  max_temp: 32
  target_temperature_step: 0.5
  hvac_modes:
    - "off"
    - heat
    - cool
    - auto
```

### 12. `media_player`
Television, smart speaker, or AV receiver.
- **`initial_value`**: `'idle'`, `'playing'`, `'paused'`, or `'off'`
- **`class`**: `'tv'`, `'speaker'`, or `'receiver'`
- **`initial_volume`**: float `0.0`–`1.0` (e.g. `0.4`)
- **`source_list`**: List of selectable input sources
- **`sound_mode_list`**: List of selectable audio sound modes (optional)
```yaml
- platform: media_player
  name: Living Room TV
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

### 13. `alarm_control_panel`
Home security system with armed/disarmed states and passcode.
- **`initial_value`**: `'disarmed'`, `'armed_home'`, `'armed_away'`, `'armed_night'`
- **`code`**: string passcode (e.g. `"1234"`)
- **`code_arm_required`**: boolean (whether code is required to arm)
- **`arming_time`**: integer delay in seconds before arming takes effect
- **`trigger_time`**: integer duration in seconds alarm remains triggered
```yaml
- platform: alarm_control_panel
  name: House Alarm
  initial_value: disarmed
  code: "1234"
  code_arm_required: false
  arming_time: 10
  trigger_time: 30
```

### 14. `button`
Stateless trigger buttons.
- **`class`**: Button device class (`restart`, `update`, `identify`, etc.)
```yaml
- platform: button
  name: Reboot Router
  class: restart
```

### 15. `select`
Selectable options dropdown.
- **`options`**: List of available string options
- **`initial_value`**: Starting selection (must match one of the options)
```yaml
- platform: select
  name: House Mode
  options:
    - Home
    - Away
    - Guest
    - Vacation
  initial_value: Home
```

### 16. `text`
Text input fields for string configuration or test messages.
- **`initial_value`**: Starting text string
- **`min`**: Minimum character length (default: `0`)
- **`max`**: Maximum character length (default: `255`)
- **`mode`**: `'text'` or `'password'`
```yaml
- platform: text
  name: Notification Message
  initial_value: "System operational"
  min: 0
  max: 255
  mode: text
```

---

## 4. Multi-Entity Device Patterns

When grouping entities under a device in `devices`, combine related sensors, controls, and actuators into a cohesive hardware unit:

### Motion Detector with Battery
```yaml
Living Room Motion Sensor:
  - platform: binary_sensor
    name: Living Room Motion
    class: motion
    initial_value: "off"
  - platform: sensor
    name: Living Room Motion Battery
    class: battery
    unit_of_measurement: "%"
    initial_value: 100
```

### Smart Power Outlet
```yaml
Kitchen Air Fryer Outlet:
  - platform: switch
    name: Kitchen Air Fryer Outlet
    class: outlet
    initial_value: "off"
  - platform: sensor
    name: Kitchen Air Fryer Power
    class: power
    unit_of_measurement: "W"
    initial_value: 0
  - platform: sensor
    name: Kitchen Air Fryer Energy
    class: energy
    unit_of_measurement: "kWh"
    initial_value: 0
```

---

## 5. Agent Generation Checklist

When writing or editing Virtual configurations:
- [ ] Root contains `version: 1` and `devices:` dictionary.
- [ ] Device names are dictionary keys with 2-space indented list of entity objects.
- [ ] Every entity explicitly defines `platform` and `name`.
- [ ] Units of measurement use standard Unicode degrees for temperature (`"°C"`).
- [ ] Off states for binary entities (`binary_sensor`, `climate`, `light`, `switch`, `fan`) are quoted strings (`"off"` or `'off'`).
- [ ] Lists for `options`, `source_list`, and `hvac_modes` contain valid non-empty string entries.
