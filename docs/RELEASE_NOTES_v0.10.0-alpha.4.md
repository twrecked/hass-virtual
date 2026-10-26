# 🚀 Virtual v0.10.0-alpha.4 — Appliance Load Simulation, Power Profiling & Duty Cycles

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

### 3. Virtual Device Editor Updates
- Added appliance load simulation settings directly to the Sensor card in the visual editor.
- Added a pre-configured **Water Heater** device template with scheduled 10-minute hourly heating cycles.
