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

### From Script
Run the install script. Run it once to make sure the operations look sane and
run it a second time with the `go` parameter to do the actual work. If you
update just rerun the script, it will overwrite all installed files.

```sh
install /config
# check output looks good
install go /config
```

## Component Configuration
Add the following to your `configuration.yaml` to enable the component:

```yaml
virtual:
```

To add a virtual switch use the following:

```yaml
switch:
  - platform: virtual
    name: Switch 1
```

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

To add a virtual sensor use the following:

```yaml
- platform: virtual
  name: 'Temperature 1'
  class: temperature
  initial_value: 37
```

Use the `virtual.set` service to manipulate the binary sensors.

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

Only `name` is required. Use the `support_*` options to allow the light to have color and temperature properties. Use `initial_*` to set the default values. `initial_color` is `[hue (0-360), saturation (0-100)]`

To add multiple components repeat the platform.

```yaml
switch:
  - platform: virtual
    name: Switch 1
  - platform: virtual
    name: Switch 2
```

To add a virtual lock use the following:

```yaml
lock:
  - platform: virtual
    name: Front Door Lock
```

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
