"""Concentration units with compatibility for older Home Assistant releases."""

try:
    from homeassistant.const import UnitOfDensity
except ImportError:
    MICROGRAMS_PER_CUBIC_METER = "µg/m³"
else:
    MICROGRAMS_PER_CUBIC_METER = UnitOfDensity.MICROGRAMS_PER_CUBIC_METER

try:
    from homeassistant.const import UnitOfRatio
except ImportError:
    PARTS_PER_MILLION = "ppm"
else:
    PARTS_PER_MILLION = UnitOfRatio.PARTS_PER_MILLION
