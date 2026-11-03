# 🚀 Virtual v0.10.0-alpha.7 — Modern Entity Naming Architecture (ADR-0007)

> ### ⚠️ Alpha Release & Community Testing Notice
> **Virtual v0.10 is an active alpha pre-release.**
>
> If you encounter any bugs, regressions, or configuration issues, please [open a GitHub issue](https://github.com/twrecked/hass-virtual/issues) with your configuration snippet and debug logs.
>
> *(Legacy v0.9 documentation is archived in [README_v9.md](README_v9.md)).*

---

## 🌟 What's New in v0.10.0-alpha.7

### 1. Home Assistant ADR-0007 Entity Naming Architecture
`hass-virtual` now fully implements Home Assistant's standard entity naming model (`_attr_has_entity_name = True`). This eliminates repetitive device name concatenation and simplifies YAML device definitions:

* **Clean Single-Entity Devices (Primary Entity)**:
  - When a device represents a single primary feature (e.g. a light, switch, dimmer, or lock), the entity `name` parameter can now be omitted completely.
  - Home Assistant assigns the parent device's name as the entity's friendly name without repetition or stuttering.
  - The default entity ID resolves to `{domain}.{slugify(device_id)}`.
* **Concise Multi-Entity Devices (Sub-Entities)**:
  - For multi-entity devices (like smart locks, multi-sensors, or power outlets), child entities no longer need to repeat the device name in YAML.
  - Simply provide concise names like `Battery`, `Motion`, `Temperature`, `Power`, or `Energy`. Home Assistant automatically composes the display name as `<Device Name> <Entity Name>` (e.g., `Front Door Lock Battery`).
  - Default entity ID resolves cleanly to `{domain}.{slugify(device_id)}_{slugify(name)}`.
* **Seamless Backward Compatibility & Prefix Stripping**:
  - Legacy YAML configurations that still pass `name: "Front Door Lock Battery"` under `Front Door Lock` have the redundant device name prefix cleanly stripped before assigning `_attr_name`, preventing double-prefix stutter in the UI.
  - `BlendedCfg` performs candidate metadata lookups across existing entries so persistent states (`RestoreEntity`) and unique IDs in `.storage/virtual.meta.json` are preserved across upgrades.
  - Sibling entity resolution (`linked_switch`, `linked_power`, `linked_battery_sensor`, `linked_entity`) automatically searches both global and device-scoped entity IDs.

### 2. Virtual Device Editor Updates
* Multi-entity templates (`Water Heater`, `Thermal House HVAC`, and `Security Camera with Motion & Sound`) have been modernized to use concise sub-entity names and omit the name on primary entities.
* The web editor form now guides users to leave primary entity names empty and use short names for child entities without repeating the parent device name.

### 3. Example Configurations
* All example configurations (`virtual-examples.yaml`, `virtual-hue.yaml`, `virtual-sonoff.yaml`, and `virtual-zwave.yaml`) have been updated to showcase clean ADR-0007 naming.

---

### Example Configuration:

```yaml
version: 1
devices:
  # 1. Clean Single-Entity Dimmer Light
  Living Room Dimmer:
    - platform: light
      initial_value: "off"
      support_brightness: true

  # 2. Multi-Entity Smart Lock
  Front Door Lock:
    - platform: lock
      initial_value: "locked"
      locking_time: 2
    - platform: sensor
      name: Battery
      class: battery
      unit_of_measurement: "%"
      initial_value: "100"
    - platform: binary_sensor
      name: Low Battery
      class: battery
      linked_battery_sensor: "Battery"
      low_battery_threshold: 15
```
