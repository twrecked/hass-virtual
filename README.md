# **Virtual devices for Home Assistant**

_Virtual_ is a component that provides virtual entities for _Home Assistant_.

![icon](images/virtual-icon.png)


# !!!BREAKING CHANGES!!!

Version 0.9 supports adding virtual devices using _config flow_. By default it
will move your existing devices into a single file `virtual.yaml`. If you
**DO NOT** want this behaviour add this to your virtual configuration.

```yaml
virtual:
  yaml_config: True
```


# Table Of Contents

<!-- TOC -->
* [**Virtual devices for Home Assistant**](#virtual-devices-for-home-assistant)
* [!!!BREAKING CHANGES!!!](#breaking-changes)
* [Table Of Contents](#table-of-contents)
* [Introduction](#introduction)
  * [Notes](#notes)
  * [Version 0.8 Documentation](#version-08-documentation)
  * [New Features in 0.9.0](#new-features-in-090)
    * [Config Flow](#config-flow)
      * [What pieces are done](#what-pieces-are-done)
      * [What you need to be wary of](#what-you-need-to-be-wary-of)
      * [What pieces need doing](#what-pieces-need-doing)
      * [What if it goes wrong?](#what-if-it-goes-wrong)
  * [Thanks](#thanks)
* [Installation](#installation)
  * [HACS](#hacs)
* [Platform Configuration](#platform-configuration)
* [Component Configuration](#component-configuration)
  * [Availability](#availability)
  * [Persistence](#persistence)
* [Platforms](#platforms)
  * [Switches](#switches)
  * [Binary Sensors](#binary-sensors)
  * [Sensors](#sensors)
  * [Lights](#lights)
  * [Locks](#locks)
  * [Fans](#fans)
  * [Covers](#covers)
  * [Valves](#valves)
  * [Device Tracking](#device-tracking)
* [Services](#services)
<!-- TOC -->

# Introduction

Virtual provides virtual components for testing Home Assistant systems.

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

This means a lot of this documentation is now out of date, I will upgrade it
when all the changes have been finalized, for now I will just add a quick note
inline.

#### What pieces are done

- _upgrade_; the code will upgrade a _0.8_ build to the _config flow_ system.
  Your current configuration will be moved into 1 file, `virtual.yaml`. This
  file contains all your virtual devices. Edit this file to add any type of
  device.
- _configuration_; the settings are still available you only need to edit them
  in one place, `virtual.yaml`. The layout should be obvious after the
  upgrade.
- _multiple integration instances_; you can group virtual devices, each group
  will use a different configuration file
- _services_; they follow the _Home Assistant_ standard
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

#### What pieces need doing

- _reload/reconfigure_; this somewhat works, but I need to deal with orphans
  when devices are turned off
- _documentation_; the configuration is handled differently now

#### What if it goes wrong?

For now I recommend leaving your old configuration in place so you can revert
back to a _0.8_ release if you encounter an issue. _Home Assistant_ will
complain about the config but it's OK to ignore it.

If you do encounter and issue if you can turn on debug an create an issue that
would be great.

## Thanks
Many thanks to:
* [JetBrains](https://www.jetbrains.com/?from=hass-aarlo) for the excellent
  **PyCharm IDE** and providing me with an open source licence to speed up the
  project development.

  [![JetBrains](/images/jetbrains.svg)](https://www.jetbrains.com/?from=hass-aarlo)

* Icon from [iconscout](https://iconscout.com) by [twitter-inc](https://iconscout.com/contributors/twitter-inc)
 

# Installation

## HACS
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

Virtual is part of the default HACS store. If you're not interested in
development branches this is the easiest way to install.

# Component Configuration

- `yaml_config`; set to `True` to enable backwards compatability, set to `False`
  to disable it. The default is `False`.

For example, this enable backwards compatability.

```yaml
virtual:
  yaml_config: True
```

# Entity Configuration

All component configuration is done through a _yaml_ file. There is a single
file per integration instance. The default file, created on upgrade, is
`/config/virtual.yaml`. An empty file looks like this:

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

Supports `open`, `close`, `stop` and `set_position`. Opening and closing of
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

# Old Style Entity Configuration

For now; look at [the 0.8](https://github.com/twrecked/hass-virtual/tree/version-0.8.x?tab=readme-ov-file#component-configuration) documentation.

