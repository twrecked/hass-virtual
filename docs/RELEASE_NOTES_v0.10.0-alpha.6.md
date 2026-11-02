# 🚀 Virtual v0.10.0-alpha.6 — Battery Drain Simulation & Companion Low-Battery Warnings

> ### ⚠️ Alpha Release & Community Testing Notice
> **Virtual v0.10 is an active alpha pre-release.**
>
> If you encounter any bugs, regressions, or configuration issues, please [open a GitHub issue](https://github.com/twrecked/hass-virtual/issues) with your configuration snippet and debug logs.
>
> *(Legacy v0.9 documentation is archived in [README_v9.md](README_v9.md)).*

---

## 🌟 What's New in v0.10.0-alpha.6

### 1. Battery Percentage Drain Simulation (`class: battery`)
Virtual battery sensors can now simulate natural battery discharge over months, complete with acceleration controls for testing low-battery automations:

- **Configurable Lifespan (`battery_life_days`)**:
  - Specify the battery lifespan in days (e.g. `battery_life_days: 90` for ~3 months, `battery_life_days: 180` for 6 months).
  - Alternatively, specify a direct daily percentage drop with `drain_rate: 1.1` (% per day).
- **Time Acceleration (`sim_speed`)**:
  - Test low-battery notifications in minutes rather than months using `sim_speed: 1000` or the `virtual.set_sim_speed` service.
- **Unrounded Precision Accumulator**:
  - Continuous integration prevents mathematical truncation across 30-second ticks.
- **State Persistence**:
  - Battery level is maintained across Home Assistant restarts.
- **Immediate Testing (`virtual.set`)**:
  - Instantly inject any battery percentage (e.g. `virtual.set sensor.door_sensor_battery 12`) to verify alerts immediately.

```yaml
Living Room Motion Sensor:
  - platform: binary_sensor
    name: Living Room Motion
    class: motion
    off_delay: 20

  - platform: sensor
    name: Living Room Motion Battery
    class: battery
    unit_of_measurement: "%"
    initial_value: "100"
    battery_life_days: 90        # Drains from 100% to 0% over ~3 months
    sim_speed: 1.0               # Speed multiplier (e.g. 1000 for fast testing)
```

---

### 2. Companion Low-Battery Binary Sensor (`binary_sensor`)
Many real-world Z-Wave and Zigbee sensors provide a binary low-battery warning alongside their battery percentage:

- Pair a `binary_sensor` with `class: battery` to any battery percentage sensor using `linked_battery_sensor`.
- Automatically monitors the percentage and flips:
  - **`is_on = True`** (Warning / Problem) when `battery_level <= low_battery_threshold` (default 15%).
  - **`is_on = False`** (Normal / Healthy) when `battery_level > low_battery_threshold`.

```yaml
Living Room Motion Sensor:
  # Companion Low-Battery Warning
  - platform: binary_sensor
    name: Living Room Motion Low Battery
    class: battery
    linked_battery_sensor: "Living Room Motion Battery"
    low_battery_threshold: 15    # Flips to on when battery drops <= 15%
```
