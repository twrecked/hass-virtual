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
Wherever you see `/config` in this README it refers to your home-assistant configuration directory. For me, for example, it's `/home/steve/ha` that is mapped to `/config` inside my docker container.

## Thanks
Many thanks to:
* [![JetBrains](/images/jetbrains.svg)](https://www.jetbrains.com/?from=hass-aarlo) for the excellent **PyCharm IDE** and providing me with an open source license to speed up the project development.

## Installation

### HACS [COMING SOON!]
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
Virtual is going to be part of the default HACS store. If you're not interested in development branches this is the easiest way to install.

### From Script
Run the install script. Run it once to make sure the operations look sane and run it a second time with the `go` parameter to do the actual work. If you update just rerun the script, it will overwrite all installed files.

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

To add a virtual binary_sensor use the following. It supports all standard classes.

```yaml
binary_sensor:
  - platform: virtual
    name: 'Binary Sensor 1'
    initial_value: 'on'
    class: presence
```

Use the `virtual.turn_on`, `virtual.turn_off` and `virtual.toggle` services to manipulate the binary sensors.

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
```

To add multiple components repeat the platform.

```yaml
switch:
  - platform: virtual
    name: Switch 1
  - platform: virtual
    name: Switch 2
```

