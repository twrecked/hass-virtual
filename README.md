# hass-virtual
### Virtual Components for Home Assistant
Virtual components for testing Home Assistant systems.

## Version 0.8

### **Breaking Changes**

I've added persistent support to `binary_sensor`, `fan`, `light`, `lock`,
`sensor` and `switch`. The persistent saving of state is turned *on* by default.
If you do not want this set `persistent: False` in the entity configuration.


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


## Installation

### HACS
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

Virtual is part of the default HACS store. If you're not interested in
development branches this is the easiest way to install.


## Component Configuration

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


### Device Tracking

To add a virtual device tracker use the following:

```yaml
device_tracker:
  - platform: virtual
    devices:
      - virtual_user1
      - virtual_user2
```

They will be moved to home on reboot. Use the `device_tracker.see` service to
change device locations.
