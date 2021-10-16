# hass-virtual
### Virtual Components for Home Assistant
Virtual components for testing Home Assistant systems.

## Table Of Contents
1. [Notes](#Notes)
1. [Thanks](#Thanks)
1. [Installation](#Installation)
   1. [Manually](#Manually)
   1. [From Script](#From-Script)
1. [Component Configuration](#Component-Configuration)


## Notes
Wherever you see `/config` in this README it refers to your home-assistant
configuration directory. For me, for example, it's `/home/steve/ha` that is
mapped to `/config` inside my docker container.


## Thanks
Many thanks to:
* [JetBrains](https://www.jetbrains.com/?from=hass-aarlo) for the excellent
  **PyCharm IDE** and providing me with an open source license to speed up the
  project development.

  [![JetBrains](/images/jetbrains.svg)](https://www.jetbrains.com/?from=hass-aarlo)


## Installation

### HACS
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

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


### Switches

To add a virtual switch use the following:

```yaml
switch:
  - platform: virtual
    name: Switch 1
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
```

Use the `virtual.set` service to manipulate the binary sensors.


### Lights

To add a virtual light use the following:

```yaml
light:
  - platform: virtual
    name: 'Light 1'
    initial_value: 'on'
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


### Locks

To add a virtual lock use the following:

```yaml
lock:
  - platform: virtual
    name: Front Door Lock
```


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
