# 🚀 Virtual v0.10.0-alpha.4 — Appliance Loads, Thermal HVAC Engine & Binary Sensor Brains

> ### ⚠️ Alpha Release & Community Testing Notice
> **Virtual v0.10 is an active alpha pre-release.**
>
> If you encounter any bugs, regressions, or configuration issues, please [open a GitHub issue](https://github.com/twrecked/hass-virtual/issues) with your configuration snippet and debug logs.
>
> *(Legacy v0.9 documentation is archived in [README_v9.md](README_v9.md)).*

---

## 🌟 What's New in v0.10.0-alpha.4

### 1. Appliance Load Simulation & Power Profiling
Virtual power sensors can now simulate realistic appliance loads coupled to a controlling smart plug or relay switch:

- **Switch Coupling & Power Invariants**:
  - The power sensor monitors its `linked_switch`.
  - When the switch is turned `off`, power immediately drops to `0.0 W`.
  - When the switch is turned `on`, power immediately restores to the current appliance state (`standby_power` vs `active_power`).
- **Recurring Scheduled Duty Cycles (Water Heaters, Compressors, Heat Pumps)**:
  - Configure `cycle_duration` (e.g. `600` for 10 minutes) and `cycle_interval` (e.g. `3600` for 1 hour).
  - Configure `cycle_align: "hour"` to synchronize with the clock (e.g. heating for the first 10 minutes past every hour).
- **Realistic Jitter / Variance**:
  - Optional `variance` parameter (e.g. `±1.5 W`) introduces small fluctuations so energy dashboard graphs look natural.
- **Rich Introspection for AppDaemon & Automation Testing**:
  - Exposes `load_state` (`active`, `standby`, `off`), `control_mode` (`auto`, `override`), `cycle_active`, `cycle_remaining`, and `next_cycle_start` in `extra_state_attributes`.

### 2. New Services
- **`virtual.set_load`**: Set the operating state (`active`, `standby`, `off`, or `auto` to resume schedule) or inject custom power wattage.
- **`virtual.run_cycle`**: Trigger an active appliance cycle for a specified duration in seconds, automatically reverting to standby or scheduled mode when complete.

### 3. Closed-Loop Thermal HVAC & House Simulation Engine
Added physical thermal modeling to `climate` entities:

- **House Thermal Dynamics & Weather Sync**:
  - Links to an `outdoor_sensor` to track ambient weather.
  - Models passive heat leakage (`house_leakage_rate`): the house naturally loses or gains heat towards outdoor ambient temperature.
  - Physical boundary: Without active heating/cooling, the house cannot drift past outdoor ambient temperature.
- **Intelligent Staging & Electrical Power Draw**:
  - **Stage 2 Heat** (3.0°C/hr, ~3800W) in freezing conditions (<0°C) or large setpoint gaps (>1.5°C).
  - **Stage 1 Heat** (1.5°C/hr, ~1800W) in moderate cold.
  - **Stage 2 Cool** (-3.0°C/hr, ~2800W) in heatwaves (>30°C) or large setpoint gaps (>1.5°C).
  - **Stage 1 Cool** (-1.5°C/hr, ~1400W) in mild heat.
  - **Fan** (-0.2°C/hr, ~120W) in `fan_only` mode.
  - **Idle/Standby** (~10W) and **Off** (0W).
- **Automatic Sensor Synchronization**:
  - Updates `indoor_sensor` with the computed room temperature in real-time.
  - Updates `power_sensor` with active electrical wattage.
- **Simulation Speed Control**:
  - Configurable `sim_speed` multiplier and `virtual.set_sim_speed` service (e.g. `sim_speed: 10.0` for 10x fast forward during testing).

### 4. Binary Sensor Brains: Auto-Off Timeouts & Device Gating
Added intelligent simulation capabilities to `binary_sensor` (motion, sound, occupancy, etc.):

- **Auto-Off Timeouts (`off_delay`)**:
  - Automatically resets the sensor back to `off` after `off_delay` seconds.
  - Re-triggering the sensor while active resets and extends the countdown timer.
  - Enhanced `virtual.turn_on` service with an optional `duration` field (e.g. `duration: 10`) to pulse the sensor for testing.
- **Device Gating (`linked_entity`)**:
  - Link motion or sound sensors to cameras, switches, or other devices.
  - Sensors can only trigger when the linked device is powered on.
  - If the linked camera/device powers off while motion is active, the binary sensor immediately clears to `off`.
- **Introspection**:
  - Exposes `off_delay`, `linked_entity`, and `time_remaining` in `extra_state_attributes`.

### 5. Virtual Device Editor Updates
- Added appliance load simulation settings directly to the Sensor card in the visual editor.
- Added a pre-configured **Water Heater** device template with scheduled 10-minute hourly heating cycles.
