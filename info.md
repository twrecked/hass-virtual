### Virtual Components for Home Assistant
Virtual components for testing Home Assistant systems.


## Version 0.8

### **Breaking Changes**

I've added persistent support to `binary_sensor`, `fan`, `light`, `lock`,
`sensor` and `switch`. The persistent saving of state is turned *on* by default.
If you do not want this set `persistent: False` in the entity configuration.


## Features
It provides:
* Virtual binary sensors
* Virtual device trackers
* Virtual fans
* Virtual lights
* Virtual locks
* Virtual senors
* Virtual switches


## Documentation
See [here](https://github.com/twrecked/hass-virtual/blob/master/README.md) for full documentation.
