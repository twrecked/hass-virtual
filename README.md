# hass-virtual
![icon](images/virtual-icon.png)

## Virtual Components for Home Assistant

Virtual components for testing Home Assistant systems.

## Version 0.8?

**This documentation is for the 0.9.x version, you can find the
0.8.x version** [here](https://github.com/twrecked/hass-virtual/tree/version-0.8.x#readme).

## New Features in 0.9.0

### Config Flow

Finally. After sitting on it for far too long I decided to do the work I
needed to, this integration now acts much like every integration, splitting
down by entity, device and integration.

This means a lot of this documentation is now out of date, I will upgrade it
when all the changes have been finalised, for now I will just add a quick note
inline.

#### What pieces are done

- _upgrade_; the code will upgrade a _0.8_ build to the _config flow_ system.
  Your current configuration will be moved into 1 file, `virtual.yaml`. This
  file contains all your virtual devices. Edit this file to add any type of
  device.
- _configuration_; the settings are still available you only need to edit them
  in one place, `virtual.yaml`. The layout should be obvious after the
  upgrade.
- _device groupings_; for example, a motion detector can have a motion
  detection entity and a battery entity, upgraded devices will have a one to
  one relationship. For example, the following will create a motion device
  with 2 entities. If you don't provide a name for an entity the system will
  provide a default.
- _multiple integration instances_; you can group virtual devices, each group
  will use a different configuration file

```yaml
  Mezzaine Motion:
    - platform: binary_sensor
      initial_value: 'off'
      class: motion
    - platform: sensor
      initial_value: 98
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
- _documentation; the configuration is handled differently now

#### What if it goes wrong?

For now I recommend leaving your old configuration in place so you can revert
back to a _0.8_ release if you encounter an issue. _Home Assistant_ will
complain about the config but it's ok to ignore it.

If you do encounter and issue if you can turn on debug an create an issue that
would be great.


## Version 0.9

## Table Of Contents
1. [Notes](#Notes)
2. [Thanks](#Thanks)
3. [Installation](#Installation)
4. [Component Configuration](#Component-Configuration)
   1. [Naming](#Naming)
   2. [Availability](#Availability)
   3. [Peristence](#Persistence)
   4. [The Components...](#Switches)


## Notes
Wherever you see `/config` in this README it refers to your home-assistant
configuration directory. For me, for example, it's `/home/steve/ha` that is
mapped to `/config` inside my docker container.


## Thanks
Many thanks to:
* [JetBrains](https://www.jetbrains.com/?from=hass-aarlo) for the excellent
  **PyCharm IDE** and providing me with an open source licence to speed up the
  project development.

  [![JetBrains](/images/jetbrains.svg)](https://www.jetbrains.com/?from=hass-aarlo)

* Icon from [iconscout](https://iconscout.com) by [twitter-inc](https://iconscout.com/contributors/twitter-inc)
 

## Installation

### HACS
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

Virtual is part of the default HACS store. If you're not interested in
development branches this is the easiest way to install.


## Component Configuration

**This is no longer valid, all config is in `virtual.yaml`.**

Add the following to your `configuration.yaml` to enable the component:

```yaml
virtual:
```

To add multiple components repeat the platform.

```yaml
switch:
  - platform: virtual
    name: Switch 1
  - platform: virtual
    name: Switch 2
```

### Naming

By default, the code creates entities with `virtual` as part of their name.
`Switch 1` in the previous example will give an entity of
`switch.virtual_switch_1`. If you don't want the `virtual_` prefix add a `!`
to the device name. For example:

```yaml
switch:
  - platform: virtual
    name: !Switch 1
```


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
switch:
  - platform: virtual
    name: Switch 1
    persistent: False
    initial_value: on
```

### Switches

To add a virtual switch use the following:

```yaml
switch:
  - platform: virtual
    name: Switch 1
    initial_availability: True
```


### Binary Sensors
To add a virtual binary_sensor use the following. It supports all standard
classes.

```yaml
binary_sensor:
  - platform: virtual
    name: 'Binary Sensor 1'
    initial_value: 'on'
    class: presence
    initial_availability: True
```

Use the `virtual.turn_on`, `virtual.turn_off` and `virtual.toggle` services to
manipulate the binary sensors.


### Sensors

To add a virtual sensor use the following:

```yaml
- platform: virtual
  name: 'Temperature 1'
  class: temperature
  initial_value: 37
  initial_availability: true
  unit_of_measurement: 'F'
```

Use the `virtual.set` service to manipulate the sensor value.

Setting `unit_of_measurement` can override default unit for selected sensor
class. This is optional ans any string is accepted. List of standard units can
be found here:
[Sensor Entity](https://developers.home-assistant.io/docs/core/entity/sensor/)

### Lights

To add a virtual light use the following:

```yaml
light:
  - platform: virtual
    name: 'Light 1'
    initial_value: 'on'
    support_brightness: true
    initial_brightness: 100
    support_color: true
    initial_color: [0,255]
    support_color_temp: true
    initial_color_temp: 255
    support_white_value: true
    initial_white_value: 240
    initial_availability: true
```

Only `name` is required.
- `support_*`; this allows the light to have colour and temperature properties
- `initial_*`; this is to set the initial values. `initial_color` is `[hue
  (0-360), saturation (0-100)]`

_Note; *white_value is deprecated and will be removed in future releases._

### Locks

To add a virtual lock use the following:

```yaml
lock:
  - platform: virtual
    name: Front Door Lock
    initial_availability: true
    initial_value: locked
    locking_time: 5
    jamming_test: 5
```

- Persistent Configuration
  - `initial_availibilty`: optional, default `True`; is device available at start up
  - `initial_value`: optional, default `locked`; any other value will result in the lock
    being unlocked at start up
- Per Run Configuration
  - `name`: _required_; device name
  - `locking_time`: optional, default `0` seconds; any positive value will result in a
    locking or unlocking phase that lasts `locking_time` seconds
  - `jamming_test`: optional, default `0` tries; any positive value will result in a
    jamming failure approximately once per `jamming_test` tries

### Fans

To add a virtual fan use the following:

```yaml
fan:
  - platform: virtual
    name: Office Fan
    speed: True
    speed_count: 5
    direction: True
    oscillate: True
    initial_availability: true
```

Only `name` is required. You only need one of `speed` or `speed_count`.
- `speed`; if `True` then fan can be set to low, medium and high speeds
- `speed_count`; number of speeds to allow, these will be broken down into
  percentages. 4 speeds = 25, 50, 75 and 100%.
- `direction`; if `True` then fan can run in 2 directions
- `oscillate`; if `True` then fan can be set to oscillate

### Covers _(in development)_

To add a virtual cover use the following:

```yaml
cover:
  - platform: virtual
    name: Window cover
    initial_value: 'closed'
    initial_availability: true
    persistent: false
```

`name` is required. By the moment, only `open` (default `initial_value`)
and `closed` states are supported and, therefore, only `cover.cover_open`
and `cover.cover_close` services are available.

### Device Tracking

To add a virtual device tracker use the following:

```yaml
device_tracker:
  - platform: virtual
    devices:
      - name: virtual_user1
        peristent: True
        location: home
      - name: virtual_user2
        peristent: False
        location: not_home
```

Only `name` is required.
- `persistent`: default `True`; if `True` then entity location is remembered
  across restarts otherwise entity always starts at `location`
- `location`: default `home`; this sets the device location when it is created
  or if the device is not `persistent`

Use the `device_tracker.see` service to change device locations.


#### Old Style Configuration
The old style configuration will still work. They will be moved to home on
initial creation and their location will survive restarts.

```yaml
device_tracker:
  - platform: virtual
    devices:
      - virtual_user1
      - virtual_user2
```
