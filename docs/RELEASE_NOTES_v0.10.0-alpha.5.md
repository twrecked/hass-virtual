# 🚀 Virtual v0.10.0-alpha.5 — Modular Hardware Ecosystem Configurations & Examples Reorganization

> ### ⚠️ Alpha Release & Community Testing Notice
> **Virtual v0.10 is an active alpha pre-release.**
>
> If you encounter any bugs, regressions, or configuration issues, please [open a GitHub issue](https://github.com/twrecked/hass-virtual/issues) with your configuration snippet and debug logs.
>
> *(Legacy v0.9 documentation is archived in [README_v9.md](README_v9.md)).*

---

## 🌟 What's New in v0.10.0-alpha.5

### 1. Home Assistant Energy Dashboard Support (Sensor `state_class`)
- `VirtualSensor` now automatically assigns appropriate `state_class` attributes required by Home Assistant's native **Energy Dashboard** and long-term statistics:
  - `class: energy` and `class: gas`: automatically declare `state_class: total_increasing`.
  - `class: power`, `temperature`, `humidity`, `voltage`, `battery`, etc.: automatically declare `state_class: measurement`.
  - Supports manual `state_class:` overrides in YAML.
- Added `Sol-Ark Battery Energy In` and `Sol-Ark Battery Energy Out` sensors to complete Home Assistant's Energy Dashboard battery tracking.
- Added `linked_power` configuration option to `sensor.py`:
  - Virtual energy sensors now automatically integrate companion power sensors into cumulative `kWh` without requiring Riemann sum helpers in Home Assistant.
  - Added companion energy sensors to all sockets in `virtual-sonoff.yaml`, `virtual-climate.yaml` (HVAC energy), and `virtual-examples.yaml` (Water Heater energy).
- Added `deadband` hysteresis (default 0.4°C) to `ThermalHvacSimulation` to run authentic heating and cooling cycles and eliminate rapid 10-second short-cycling.
- Added `battery_strategy` option (`backup` vs `self_consumption`):
  - In `backup` mode (default), the battery is held at 100% float charge for emergencies while grid power is healthy. Deficits pull from cheap grid power.
  - When grid voltage drops (<= 25 V), the inverter automatically enters island mode, powering the home from solar and battery.
- Added reactive grid voltage tracking (`grid_voltage_sensor`) allowing seamless blackout testing using standard `virtual.set`.

### 2. Inverter Baseload Tracking & Battery Polarity
- **Base Load Power & Energy Sensors**: The Sol-Ark simulation now exposes `base_load_power_sensor` and `base_load_energy_sensor`, allowing you to add baseline home draw to *Individual Devices* and eliminate "unaccounted for energy" on the Energy tab.
- **Simulation State Persistence**: The simulation engines now restore their exact battery State of Charge, cumulative energy meters (`kWh`), and gas consumption (`m³`) across Home Assistant restarts, ensuring seamless continuity on Energy Dashboard charts without resetting counters to zero.
- **Battery Power Polarity Fix**: Corrected single-sensor battery polarity in `solar_inverter.py` to match Home Assistant's standard convention (`negative = charging`, `positive = discharging`), ensuring charging power is properly shown entering the battery.

### 3. Modular Hardware Ecosystem Configurations (`examples/`)
Added ready-to-import virtual device configuration files partitioned by simulated hardware brand:

- **`examples/virtual-sonoff.yaml`** (6 devices):
  - 5 power-monitoring smart sockets: TV (with dynamic jitter), Audio Amplifier, Chest Freezer (15m/45m cyclic compressor), Washing Machine, and Heat Pump Tumble Dryer.
  - Master Bedroom 3-speed ceiling fan controller & on/off light kit.
- **`examples/virtual-hue.yaml`** (6 devices):
  - Dimmable warm white bulbs for bedrooms and closet.
  - Multi-colored ambiance lights for front porch and back deck (supporting HS color, Kelvin color temp, and dynamic effects).
- **`examples/virtual-zwave.yaml`** (25 standalone devices):
  - Motorized Schlage deadbolt with battery reporting and 2s transit delay.
  - 5 Standalone door contact sensors (front, back, garage, shed, basement).
  - 8 In-wall light switches.
  - 11 PIR motion sensors with auto-clearing `off_delay: 20` countdown timers.

---

### 4. Dedicated Climate & Multi-Platform Example Files
- **`examples/virtual-climate.yaml`**:
  - Dedicated configuration file containing the closed-loop thermal HVAC system (Thermostat + Indoor Temp + Outdoor Weather Sync + Power Meter) and a standalone basic thermostat.
- **`examples/virtual-examples.yaml`**:
  - Renamed from `virtual-umbrella.yaml` and streamlined to showcase diverse multi-platform devices (Security Alarm Panel, Action Button, Dropdown Select, Text Input, Media Player Speaker, Camera with HLS Streaming, TV Power Socket, and Gated Driveway Security Camera).
