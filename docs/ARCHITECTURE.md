# 🏛️ `hass-virtual` System Architecture

This document describes the architectural design, lifecycle, and component interactions of `hass-virtual` (v0.10+).

---

## 1. High-Level Architecture Overview

```text
┌────────────────────────────────────────────────────────┐
│               virtual-*.yaml Files                     │
│    (Device groupings, entity configs, simulations)     │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                       BlendedCfg                       │
│       (In-memory virtual hardware coordinator)         │
│  - Parses YAML device definitions                      │
│  - Classifies ADR-0007 primary vs sub-entities         │
│  - Correlates with HA device_registry & entity_registry│
│  - Generates deterministic unique IDs                  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                   async_setup_entry                    │
│                  (__init__.py Lifecycle)               │
│  - Registers/updates devices in HA device_registry     │
│  - Automatically prunes unreferenced/orphaned devices  │
│  - Automatically prunes unreferenced/orphaned entities │
│  - Forwards entry setups to the 18 platform modules    │
│  - Boots background SimulationManager (Solar / HVAC)   │
│  - Hosts token-authenticated builder hot-reload webhook│
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                  18 Entity Platforms                   │
│   (switch, light, sensor, binary_sensor, lock, etc.)   │
│  - Subclasses VirtualEntity (RestoreEntity)            │
│  - Enforces _attr_has_entity_name = True               │
│  - Automatically restores states & availability        │
│  - Resolves sibling entity links (power, switch, etc.) │
└────────────────────────────────────────────────────────┘
```

---

## 2. Configuration & Virtual Hub Layer (`cfg.py`)

In traditional Home Assistant integrations (such as Philips Hue or Z-Wave JS), a physical hub or cloud API is queried during setup to discover available devices and their capabilities (`GET /devices`). 

Because `hass-virtual` is completely local and simulated, **`BlendedCfg` acts as that virtual hardware bridge**:

* **YAML Ingestion**: Ingests configuration files (`virtual.yaml`, `virtual-hue.yaml`, `virtual-zwave.yaml`, etc.) linked to an active Home Assistant config entry.
* **Registry Correlation**: Directly queries Home Assistant's `device_registry` and `entity_registry` for the current config entry to identify existing devices and entities.
* **Identity Resolution**:
  * For existing entities, it reuses their registered `unique_id` directly from `core.entity_registry`, preserving historical statistics, dashboard bindings, and area assignments.
  * For new entities, it calculates clean, deterministic unique IDs (`{device_slug}.virtual` for primary entities, `{device_slug}_{sub_slug}.virtual` for sub-entities).
  * Eliminates the need for external sidecar storage files (such as `.storage/virtual.meta.json`).

---

## 3. Integration Lifecycle & Self-Cleaning Registries (`__init__.py`)

The integration entry lifecycle is coordinated in `custom_components/virtual/__init__.py`:

### Entry Setup (`async_setup_entry`)
1. **Device Registration**:
   Registers all devices defined in the YAML file into Home Assistant's `device_registry` with `manufacturer="twrecked"` and `model="virtual"`.
2. **Self-Cleaning Orphan Cleanup**:
   Compares all devices and entities currently registered in Home Assistant under this `config_entry_id` against the active definitions in the YAML file:
   * **Orphaned Devices**: Any device belonging to this entry that is no longer in the YAML file (e.g. after a device rename or deletion) is automatically purged using `device_registry.async_remove_device()`.
   * **Orphaned Entities**: Any entity belonging to this entry that is no longer in the YAML file is automatically purged using `entity_registry.async_remove()`.
3. **Platform Forwarding**:
   Dispatches entity definitions to all 18 supported platform modules via `hass.config_entries.async_forward_entry_setups()`.
4. **Simulation Engine Initialization**:
   Instantiates and boots the `SimulationManager` to execute background simulations.
5. **Hot-Reload Builder Webhook**:
   Registers an authenticated webhook endpoint (`/api/webhook/virtual_<entry_id>`). When the companion **Virtual Device Editor** web application saves changes, it delivers the updated YAML to this webhook, triggering an instantaneous asynchronous reload of the config entry without requiring a full Home Assistant restart.

---

## 4. Entity Architecture & ADR-0007 (`entity.py`)

All virtual entities inherit from `VirtualEntity`, which derives from Home Assistant's `RestoreEntity`.

### A. Home Assistant ADR-0007 Entity Naming Architecture
`VirtualEntity` declares `_attr_has_entity_name = True`. Home Assistant uses this flag to compose entity display names dynamically based on context:

* **Primary Entities (`_attr_name = None`)**:
  * When an entity represents the main function of a device (e.g. the light on a dimmer, the switch on an outlet, or the lock on a smart lock), `name` is omitted in YAML.
  * `VirtualEntity` sets `self._attr_name = None`.
  * Home Assistant uses the parent device name as the entity's friendly name without stuttering or repetitive labels.
  * Default entity ID: `{domain}.{slugify(device_id)}`.
* **Sub-Entities (`_attr_name = sub_name`)**:
  * For multi-entity devices, child entities specify concise names (e.g., `Battery`, `Low Battery`, `Motion`, `Power`).
  * Home Assistant automatically formats the UI display name as `<Device Name> <Entity Name>` (e.g., `Front Door Lock Battery`).
  * Default entity ID: `{domain}.{slugify(device_id)}_{slugify(name)}`.
* **Legacy Prefix Stripping**:
  * If an older configuration supplies `name: "Front Door Lock Battery"` on device `Front Door Lock`, `VirtualEntity` cleanly strips the leading device name prefix before assigning `_attr_name`, preventing double-prefix stutter in the UI.

### B. State Persistence & Availability
* **`_create_state`**: Initializes defaults when an entity is created for the first time or when state persistence is disabled (`persistent: false`).
* **`_restore_state`**: Recovers last known states, attributes, brightness levels, positions, and battery percentages from Home Assistant's restore state database across restarts.
* **Safe Null-Guarding**: All state restoration explicitly guards against `None` values to avoid overwriting defaults with stale uninitialized data.

---

## 5. Supported Platforms & Simulation Engines

`hass-virtual` supports **17 Home Assistant entity platforms**:
* **Actuators & Controls**: `switch`, `light`, `cover`, `valve`, `fan`, `lock`, `climate`
* **Sensors & Trackers**: `sensor`, `binary_sensor`, `device_tracker`
* **User Inputs & Media**: `button`, `number`, `select`, `text`, `media_player`, `camera`, `alarm_control_panel`

### Advanced Simulation Engines
1. **Closed-Loop HVAC Physics (`simulations/thermal_hvac.py`)**:
   * Continuous thermal model simulating house heat loss/gain based on outdoor temperature and wall leakage rates (`house_leakage_rate`).
   * Supports both **electric** heating (drawing Watts on electrical power sensors) and **gas** heating (consuming fuel in `m³/h` with cumulative volume meters for the Energy Dashboard).
2. **Solar Inverter & Battery Storage (`simulations/solar_inverter.py`)**:
   * Mathematical solar generation curve tracking sun position and peak capacity (`peak_solar_power`).
   * Battery storage manager supporting `backup` and `self_consumption` strategies, charge/discharge rates, and reactive grid voltage tracking.
   * Real-time house load aggregation summing base standby load plus all active linked appliances.
3. **Appliance Duty Cycles & Power Simulation (`sensor.py`)**:
   * Clock-aligned recurring duty cycles (e.g., a water heater operating for 10 minutes every hour).
   * Standby vs. active load states with customizable random variance.
   * Integrated energy sensors (`linked_power`) that accumulate real-time kWh from power sensors without requiring external Home Assistant helper entities.
4. **Natural Battery Discharge & Warnings (`sensor.py`, `binary_sensor.py`)**:
   * Simulates long-term battery drainage over months (`battery_life_days` or `drain_rate`).
   * Companion low-battery binary sensors (`linked_battery_sensor`) with automatic threshold triggering (`low_battery_threshold`).
   * Time acceleration support (`virtual.set_sim_speed`) allowing months of discharge to be simulated in minutes for testing automations.
