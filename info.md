### Virtual Components for Home Assistant
Virtual devices, mock hardware, and physics simulation engines (HVAC, Solar, Energy Dashboard) for Home Assistant.


## Features
It provides 18 distinct virtual device platforms:
* Virtual alarm control panels
* Virtual binary sensors (with auto-off timeout and entity gating)
* Virtual buttons
* Virtual cameras (still snapshot images and live HLS stream playback)
* Virtual climates (thermostats)
* Virtual covers (timed positioning)
* Virtual device trackers
* Virtual fans
* Virtual lights (dimming, color, Kelvin color temp, and pre-staged settings)
* Virtual locks (motorized transit duration & jamming tests)
* Virtual media players
* Virtual numbers
* Virtual selects
* Virtual sensors (with simulated appliance power loads and auto-accumulating energy)
* Virtual sirens (manual alarm sirens and automatic timed chimes)
* Virtual switches
* Virtual texts
* Virtual valves

Plus physical simulation engines:
* Solar Inverter & Energy Hub (solar diurnal curve, battery storage, and grid flow balancing)
* Closed-Loop Thermal HVAC (insulation leakage, ambient weather sync, electric and gas furnace heating)


## Configuration & Management
Supports UI configuration via Config Flow, YAML device definitions, state persistence across restarts, and an interactive web-based Visual Device Editor with one-click webhook sync.


## Documentation
See [here](https://github.com/twrecked/hass-virtual/blob/main/README.md) for full documentation.
