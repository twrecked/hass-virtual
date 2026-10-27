# 🚀 Virtual v0.10.0-alpha.5 — Modular Hardware Ecosystem Configurations & Examples Reorganization

> ### ⚠️ Alpha Release & Community Testing Notice
> **Virtual v0.10 is an active alpha pre-release.**
>
> If you encounter any bugs, regressions, or configuration issues, please [open a GitHub issue](https://github.com/twrecked/hass-virtual/issues) with your configuration snippet and debug logs.
>
> *(Legacy v0.9 documentation is archived in [README_v9.md](README_v9.md)).*

---

## 🌟 What's New in v0.10.0-alpha.5

### 1. Modular Hardware Ecosystem Configurations (`examples/`)
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

### 2. Dedicated Climate & Multi-Platform Example Files
- **`examples/virtual-climate.yaml`**:
  - Dedicated configuration file containing the closed-loop thermal HVAC system (Thermostat + Indoor Temp + Outdoor Weather Sync + Power Meter) and a standalone basic thermostat.
- **`examples/virtual-examples.yaml`**:
  - Renamed from `virtual-umbrella.yaml` and streamlined to showcase diverse multi-platform devices (Security Alarm Panel, Action Button, Dropdown Select, Text Input, Media Player Speaker, Camera with HLS Streaming, TV Power Socket, and Gated Driveway Security Camera).
