# **Virtual devices for Home Assistant**

_Virtual_ is a component that provides virtual entities for _Home Assistant_.

![icon](images/virtual-icon.png)


# !!!BREAKING CHANGES!!!

Version 0.9 supports adding virtual devices using _config flow_. By default it
will move your existing devices into a single file `virtual.yaml`. If you **DO
NOT** want this behaviour add this to your current `virtual` configuration.

```yaml
virtual:
  yaml_config: True
```


# Table Of Contents


<!--toc:start-->
- [**Virtual devices for Home Assistant**](#virtual-devices-for-home-assistant)
- [!!!BREAKING CHANGES!!!](#breaking-changes)
- [Table Of Contents](#table-of-contents)
- [Introduction](#introduction)
  - [Notes](#notes)
  - [Version 0.8 Documentation](#version-08-documentation)
  - [New Features in 0.9.0](#new-features-in-090)
    - [Config Flow](#config-flow)
      - [What pieces are done](#what-pieces-are-done)
      - [What you need to be wary of](#what-you-need-to-be-wary-of)
      - [What if it goes wrong?](#what-if-it-goes-wrong)
  - [Thanks](#thanks)
- [Installation](#installation)
  - [Getting the Software](#getting-the-software)
    - [HACS](#hacs)
  - [Adding the Integration](#adding-the-integration)
    - [After a Fresh Install](#after-a-fresh-install)
    - [After an Upgrade](#after-an-upgrade)
  - [I don't want the New Behaviour!!!](#i-dont-want-the-new-behaviour)
  - [Adding More Entries](#adding-more-entries)
- [Component Configuration](#component-configuration)
- [Entity Configuration](#entity-configuration)
  - [File Layout](#file-layout)
  - [Common Attributes](#common-attributes)
    - [Availability](#availability)
    - [Persistence](#persistence)
  - [Switches](#switches)
  - [Binary Sensors](#binary-sensors)
  - [Sensors](#sensors)
  - [Lights](#lights)
  - [Locks](#locks)
  - [Fans](#fans)
  - [Climate](#climate)
  - [Covers](#covers)
  - [Valves](#valves)
  - [Device Tracking](#device-tracking)
- [Old Style Entity Configuration](#old-style-entity-configuration)
- [Services](#services)
<!--toc:end-->


# Introduction

Virtual provides virtual components for testing Home Assistant systems, including switches, sensors, lights, locks, fans, climate devices, covers, valves, and device trackers.

## Notes
Wherever you see `/config` in this README it refers to your home-assistant
configuration directory. For me, for example, it's `/home/steve/ha` that is
mapped to `/config` inside my docker container.

## Version 0.8 Documentation

**This documentation is for the 0.9.x version, you can find the
0.8.x version** [here](https://github.com/twrecked/hass-virtual/tree/version-0.8.x#readme).

## New Features in 0.9.0

### Config Flow

Finally. After sitting on it for far too long I decided to do the work I
needed to, this integration now acts much like every integration, splitting
down by entity, device and integration.

#### What pieces are done

- _upgrade_; the code will upgrade a _0.8_ build to the _config flow_ system.
  Your current configuration will be moved into 1 file, `virtual.yaml`. This
  file contains all your virtual devices. Edit this file to add any type of
  device.
- _services_; they follow the _Home Assistant_ standard
- _multiple integrations_; the integration can be added several times and you
  can spread your devices across several files
- _device groupings_; for example, a motion detector can have a motion
  detection entity and a battery entity, upgraded devices will have a one to
  one relationship. For example, the following will create a motion device
  with 2 entities. If you don't provide a name for an entity the system will
  provide a default.

```yaml
  Mezzanine Motion:
    - platform: binary_sensor
      initial_value: 'off'
      class: motion
    - platform: sensor
      initial_value: '98'
      class: battery
```

#### What you need to be wary of

- _device trackers_; the upgrade process is a little more complicated if you
  have device trackers, because of the way _virtual_ created the old devices
  you will end up with duplicates entries, you can fix it by running the
  following steps
  1. do the upgrade
  2. comment out device virtual device trackers from `device_trackers.yaml`
     and `known_devices.yaml`
  3. restart _Home Assistant_
  4. delete the virtual integration
  5. add back the virtual integration in accepting the defaults

#### What if it goes wrong?

For now I recommend leaving your old configuration in place so you can revert
back to a _0.8_ release if you encounter an issue. _Home Assistant_ will
complain about the config but it's OK to ignore it.

If you do encounter and issue if you can turn on debug an create an issue that
would be great.

## Thanks
Many thanks to:
* Icon from [iconscout](https://iconscout.com) by [twitter-inc](https://iconscout.com/contributors/twitter-inc)
 

# Installation

## Getting the Software

### HACS
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

Virtual is part of the default HACS store. If you're not interested in
development branches this is the easiest way to install.

## Adding the Integration 

### After a Fresh Install

When you have created your initial configuration file do the following:

- go to `Settings` -> `Devices and Integrations` -> `+ ADD INTEGRATION`
- search for _virtual_ and choose the integration
- give your configuration a name and point it at your newly created file

Then you click OK 

**Warning:** Check your /config/ folder if a virtual.yml file has been added. If not, make this file yourself.

### After an Upgrade

All your devices will be moved to a group called _import_ and put into
`/config/virtual.yaml`. The system will create a single _virtual_ integration.

## I don't want the New Behaviour!!!

If you want to keep your existing behaviour change your current `virtual`
entry in `configuration.yaml` to this:

```yaml
virtual:
  yaml_config: True
```

## Adding More Entries

You can add more than one integration by selecting `Add Entry` on the
_virtual_ integration page. You will need to give this new entity group a name
and point it to the new file.


# Component Configuration

You set this to enable backwards compatibility. 

- `yaml_config`; set to `True` to enable backwards compatibility, set to `False`
  to disable it. The default is `False`.

For example, this enable backwards compatibility.

```yaml
virtual:
  yaml_config: True
```


# Entity Configuration

All component configuration is done through _yaml_ files. You can put all of
your virtual devices into a single _yaml_ file or you can group devices
together in multiple file.

If this is a fresh install you will need to install a _virtual_ integration
instance and tell it about your file. If you are upgrading from _0.8_ the system will
create a single instance and copy all your current devices into a
`/config/virtual.yaml`.

## File Layout

An empty file looks like this:
```yaml
version: 1
devices: {}
```

- _version_; this is currently 1
- _devices_; this is a list of devices and entities associated with that
  device

These two entries are optional. If you remove them then remove the indentation
from the following device entries.

This is a small example of an imported file: 

```yaml
version: 1
devices: 
 Living Room Sensor:
  - platform: binary_sensor
    name: Living Room Motion
    initial_value: 'off'
    class: motion
 Back Door Sensor:
  - platform: binary_sensor
    name: Back Door
    initial_value: 'off'
    class: door
```

This is an example of a file without the preamble.

```yaml
Living Room Sensor:
- platform: binary_sensor
  name: Living Room Motion
  initial_value: 'off'
  class: motion
Back Door Sensor:
- platform: binary_sensor
  name: Back Door
  initial_value: 'off'
  class: door
```

Note that these entities have explicit names, this is because these entities
were imported and the integration will re-create the same entity and
unique IDs as previous version. You do not need to assign a name on new
entries, the system will provide a default suffix based on device class. But,
you can also choose to provide names if you wish.

This is the same file without the names:

```yaml
version: 1
devices: 
  Living Room Sensor:
  - platform: binary_sensor
    initial_value: 'off'
    class: motion
  Back Door Sensor:
  - platform: binary_sensor
    initial_value: 'off'
    class: door
```

In this case it will create 2 entities, one called `Living Room Sensor motion`
and `Back Door Sensor door`. The default naming can get a little hairy but you
can alter it from the _Integration_ settings.

You can also define virtual multi sensors. In this example a multi sensor
devices provides 2 entities.

```yaml
Living Room Multi Sensor:
- platform: binary_sensor
  initial_value: 'off'
  class: motion
- platform: sensor
  initial_value: '20'
  class: temperature
```

## Common Attributes

### Availability

By default, all devices are market as available. As shown below in each domain,
adding `initial_availability: false` to configuration can override default and
set as unavailable on HA start. Availability can by set by using
the `virtual.set_available` with value `true` or `false`.

This is fully optional and `initial_availability` is not required to be set.

### Persistence
By default, all device states are persistent. You can change this behaviour with
the `persistent` configuration option.

If you have set an `initial_value` it will only be used if the device state is
not restored. The following switch will always start _on_.

```yaml
Test Switch:
- platform: virtual
  name: Switch 1
  persistent: False
  initial_value: on
```

## Switches

To add a virtual switch use the following:

```yaml
Test Switch:
- platform: switch
```

## Binary Sensors
To add a virtual binary_sensor use the following. It supports all standard
classes.

```yaml
Test Binary Sensor:
- platform: binary_sensor
  initial_value: 'on'
  class: presence
```

Use the `virtual.turn_on`, `virtual.turn_off` and `virtual.toggle` services to
manipulate the binary sensors.

## Sensors

To add a virtual sensor use the following:

```yaml
Test Sensor:
- platform: sensor
  class: temperature
  initial_value: 37
  unit_of_measurement: 'F'
```

Use the `virtual.set` service to manipulate the sensor value.

Setting `unit_of_measurement` can override default unit for selected sensor
class. This is optional ans any string is accepted. List of standard units can
be found here:
[Sensor Entity](https://developers.home-assistant.io/docs/core/entity/sensor/)

## Lights

To add a virtual light use the following:

```yaml
Test Lights:
- platform: light
  initial_value: 'on'
  support_brightness: true
  initial_brightness: 100
  support_color: true
  initial_color: [0,255]
  support_color_temp: true
  initial_color_temp: 255
  support_white_value: true
  initial_white_value: 240
```

Only `name` is required.
- `support_*`; this allows the light to have colour and temperature properties
- `initial_*`; this is to set the initial values. `initial_color` is `[hue
  (0-360), saturation (0-100)]`

_Note; *white_value is deprecated and will be removed in future releases._

## Locks

To add a virtual lock use the following:

```yaml
Test Lock:
- platform: lock
  name: Front Door Lock
  initial_value: locked
  locking_time: 5
  jamming_test: 5
```

- Persistent Configuration
  - `initial_value`: optional, default `locked`; any other value will result in the lock
    being unlocked at start up
- Per Run Configuration
  - `locking_time`: optional, default `0` seconds; any positive value will result in a
    locking or unlocking phase that lasts `locking_time` seconds
  - `jamming_test`: optional, default `0` tries; any positive value will result in a
    jamming failure approximately once per `jamming_test` tries

## Fans

To add a virtual fan use the following:

```yaml
Test Fan:
- platform: fan
  speed: True
  speed_count: 5
  direction: True
  oscillate: True
```

## Climate

To add a virtual climate device (HVAC system, air conditioner, etc.) use the following:

```yaml
Living Room AC:
- platform: climate
  name: Living Room Air Conditioner
  initial_value: 'off'
  hvac_modes: ['heat', 'cool', 'heat_cool', 'dry', 'fan_only', 'off']
  fan_modes: ['auto', 'low', 'medium', 'high']
  preset_modes: ['none', 'eco', 'boost']
  swing_modes: ['off', 'vertical', 'horizontal', 'both']
  min_temp: 16.0
  max_temp: 30.0
  target_temp_step: 0.5
  current_temperature: 22.0
  current_humidity: 45
  target_temperature: 24.0
  target_temperature_high: 26.0
  target_temperature_low: 18.0
  humidity: 50
  fan_mode: 'auto'
  preset_mode: 'none'
  swing_mode: 'off'
  hvac_action: 'idle'
```

**Required Parameters:**
- `platform`: Must be set to `climate`

**Optional Parameters (all have sensible defaults):**

**Mode Support:**
- `hvac_modes`: List of supported HVAC modes. Default: `['heat', 'cool', 'heat_cool', 'dry', 'fan_only', 'off']`
- `fan_modes`: List of supported fan modes. Default: `['auto', 'low', 'medium', 'high']`
- `preset_modes`: List of supported preset modes. Default: `['none', 'eco', 'boost']`
- `swing_modes`: List of supported swing modes. Default: `['off', 'vertical', 'horizontal', 'both']`

**Temperature Control:**
- `min_temp`: Minimum temperature limit (°C). Default: `7.0`
- `max_temp`: Maximum temperature limit (°C). Default: `35.0`
- `target_temp_step`: Temperature adjustment step size. Default: `0.5`
- `current_temperature`: Current room temperature (°C). Default: `20.0`
- `target_temperature`: Target temperature for single mode (°C). Default: `20.0`
- `target_temperature_high`: High temperature for heat_cool mode (°C). Default: `26.0`
- `target_temperature_low`: Low temperature for heat_cool mode (°C). Default: `16.0`

**Humidity Control:**
- `current_humidity`: Current room humidity (%). Default: `50`
- `humidity`: Target humidity (%). Default: `50`

**Initial State:**
- `initial_value`: Initial power state. Default: `'off'`
- `fan_mode`: Initial fan mode. Default: `'auto'`
- `preset_mode`: Initial preset mode. Default: `'none'`
- `swing_mode`: Initial swing mode. Default: `'off'`
- `hvac_action`: Initial HVAC action. Default: `'idle'`

**Example Use Cases:**
- **Simple AC**: Use `hvac_modes: ['cool', 'off']` for basic air conditioning
- **Heat Pump**: Use `hvac_modes: ['heat', 'cool', 'heat_cool', 'off']` for full HVAC control
- **Fan Only**: Use `hvac_modes: ['fan_only', 'off']` for ventilation systems
- **Dehumidifier**: Use `hvac_modes: ['dry', 'off']` for moisture control

**Supported Operations:**
- Temperature control (single or range mode)
- Mode switching (heat, cool, heat_cool, dry, fan_only)
- Fan speed control
- Preset mode selection
- Swing mode control
- Humidity monitoring and control

You only need one of `speed` or `speed_count`.
- `speed`; if `True` then fan can be set to low, medium and high speeds
- `speed_count`; number of speeds to allow, these will be broken down into
  percentages. 4 speeds = 25, 50, 75 and 100%.
- `direction`; if `True` then fan can run in 2 directions
- `oscillate`; if `True` then fan can be set to oscillate

## Covers

To add a virtual cover use the following:

```yaml
Test Cover:
- platform: cover
  initial_value: 'closed'
  open_close_duration: 10
  open_close_tick: 1
```

Supports `open`, `close`, `stop` and `set_position`. Opening and closing of
the cover is emulated with timed events, and the timing can be controlled with
- `open_close_duration`: The time it take to go from fully open to fully closed, or back
- `open_close_tick`: The update interval when opening and closing

## Valves

To add a virtual valve use the following:

```yaml
Test Valve:
- platform: valve
  initial_value: 'closed'
  open_close_duration: 10
  open_close_tick: 1
```

Supports `open_valve`, `close_valve`, `stop_valve` and `set_valve_position`. Opening and closing of
the valve is emulated with timed events, and the timing can be controlled with
- `open_close_duration`: The time it take to go from fully open to fully closed, or back
- `open_close_tick`: The update interval when opening and closing

## Device Tracking

To add a virtual device tracker use the following:

```yaml
Test Device_Tracker:
- platform: device_tracker
  initial_value: home
```

- `persistent`: default `True`; if `True` then entity location is remembered
  across restarts otherwise entity always starts at `location`
- `location`: default `home`; this sets the device location when it is created
  or if the device is not `persistent`

Use the `virtual.move` service to change device locations.


# Old Style Entity Configuration

For now; look at [the 0.8](https://github.com/twrecked/hass-virtual/tree/version-0.8.x?tab=readme-ov-file#component-configuration) documentation.


# Services

The component provides the following services:

**Name: `virtual.set_availability`**

*Parameters:*
- `entity_id`; The entity id of the binary sensor to turn on.

This will change the availability setting of any virtual device.

---

**Name: `virtual.turn_on`**

*Parameters:*
- `entity_id`; The entity id of the binary sensor to turn on.

This service will turn on a binary sensor.

---

**Name: `virtual.turn_off`**

*Parameters:*
- `entity_id`; The entity id of the binary sensor to turn off.

This service will turn off a binary sensor.

---

**Name: `virtual.toggle`**

*Parameters:*
- `entity_id`; The entity id of the binary sensor to toggle.

- This service will toggle a binary sensor.

---

**Name: `virtual.move`**

*Parameters:*

- `location`; a named location
- `gps`; GPS coordinates

Move a device tracker. You use one of the parameters.

---

**Name: `virtual.set_climate_temperature`**

*Parameters:*
- `entity_id`; The entity id of the climate device
- `temperature`; The target temperature to set

This service sets the target temperature for a virtual climate device.

---

**Name: `virtual.set_climate_hvac_mode`**

*Parameters:*
- `entity_id`; The entity id of the climate device
- `hvac_mode`; The HVAC mode to set (heat, cool, heat_cool, dry, fan_only, off)

This service changes the HVAC mode of a virtual climate device.

---

**Name: `virtual.set_climate_fan_mode`**

*Parameters:*
- `entity_id`; The entity id of the climate device
- `fan_mode`; The fan mode to set (auto, low, medium, high)

This service changes the fan mode of a virtual climate device.

