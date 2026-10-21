"""This component provides support for a virtual number."""
from __future__ import annotations

import logging
from collections.abc import Callable

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.number import (
    DOMAIN as PLATFORM_DOMAIN,
    NumberDeviceClass,
    NumberEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_UNIT_OF_MEASUREMENT,
    LIGHT_LUX,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS,
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfPressure,
    UnitOfReactivePower,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import get_entity_configs
from .const import (
    ATTR_GROUP_NAME,
    COMPONENT_CONFIG,
    COMPONENT_DOMAIN,
    CONF_CLASS,
    CONF_INITIAL_VALUE,
    CONF_MAX,
    CONF_MIN,
    CONF_YAML_CONFIG,
)
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_NUMBER_VALUE = "0"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_NUMBER_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Required(CONF_MIN): vol.Coerce(float),
    vol.Required(CONF_MAX): vol.Coerce(float),
    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=""): cv.string,
}))
NUMBER_SCHEMA = vol.Schema(virtual_schema(DEFAULT_NUMBER_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Required(CONF_MIN): vol.Coerce(float),
    vol.Required(CONF_MAX): vol.Coerce(float),
    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=""): cv.string,
}))

UNITS_OF_MEASUREMENT = {
    NumberDeviceClass.APPARENT_POWER: UnitOfApparentPower.VOLT_AMPERE,  # apparent power (VA)
    NumberDeviceClass.BATTERY: PERCENTAGE,  # % of battery that is left
    NumberDeviceClass.CO: CONCENTRATION_PARTS_PER_MILLION,  # ppm of CO concentration
    NumberDeviceClass.CO2: CONCENTRATION_PARTS_PER_MILLION,  # ppm of CO2 concentration
    NumberDeviceClass.HUMIDITY: PERCENTAGE,  # % of humidity in the air
    NumberDeviceClass.ILLUMINANCE: LIGHT_LUX,  # current light level (lx/lm)
    NumberDeviceClass.NITROGEN_DIOXIDE: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of nitrogen dioxide
    NumberDeviceClass.NITROGEN_MONOXIDE: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of nitrogen monoxide
    NumberDeviceClass.NITROUS_OXIDE: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of nitrogen oxide
    NumberDeviceClass.OZONE: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of ozone
    NumberDeviceClass.PM1: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of PM1
    NumberDeviceClass.PM10: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of PM10
    NumberDeviceClass.PM25: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of PM2.5
    NumberDeviceClass.SIGNAL_STRENGTH: SIGNAL_STRENGTH_DECIBELS,  # signal strength (dB/dBm)
    NumberDeviceClass.SULPHUR_DIOXIDE: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of sulphur dioxide
    NumberDeviceClass.TEMPERATURE: "C",  # temperature (C/F)
    NumberDeviceClass.PRESSURE: UnitOfPressure.HPA,  # pressure (hPa/mbar)
    NumberDeviceClass.POWER: UnitOfPower.KILO_WATT,  # power (W/kW)
    NumberDeviceClass.CURRENT: UnitOfElectricCurrent.AMPERE,  # current (A)
    NumberDeviceClass.ENERGY: UnitOfEnergy.KILO_WATT_HOUR,  # energy (Wh/kWh/MWh)
    NumberDeviceClass.FREQUENCY: UnitOfFrequency.GIGAHERTZ,  # energy (Hz/kHz/MHz/GHz)
    NumberDeviceClass.POWER_FACTOR: PERCENTAGE,  # power factor (no unit, min: -1.0, max: 1.0)
    NumberDeviceClass.REACTIVE_POWER: UnitOfReactivePower.VOLT_AMPERE_REACTIVE,  # reactive power (var)
    NumberDeviceClass.VOLATILE_ORGANIC_COMPOUNDS: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of vocs
    NumberDeviceClass.VOLTAGE: UnitOfElectricPotential.VOLT,  # voltage (V)
    NumberDeviceClass.GAS: UnitOfVolume.CUBIC_METERS,  # gas (m³)
}


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")

        sensors = [VirtualNumber(config, True)]
        async_add_entities(sensors, True)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the entries...")

    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = NUMBER_SCHEMA(entity)
        entities.append(VirtualNumber(entity, False))
    async_add_entities(entities)


class VirtualNumber(VirtualEntity, NumberEntity):
    """An implementation of a Virtual Number."""

    def __init__(self, config, old_style: bool):
        """Initialize a Virtual Number."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_device_class = config.get(CONF_CLASS)
        self._attr_native_min_value = float(config.get(CONF_MIN))
        self._attr_native_max_value = float(config.get(CONF_MAX))

        # Set unit of measurement
        self._attr_native_unit_of_measurement = config.get(CONF_UNIT_OF_MEASUREMENT)
        if not self._attr_native_unit_of_measurement and self._attr_device_class in UNITS_OF_MEASUREMENT:
            self._attr_native_unit_of_measurement = UNITS_OF_MEASUREMENT[self._attr_device_class]

        _LOGGER.info(f"VirtualNumber: {self.name} created")

    def _create_state(self, config):
        super()._create_state(config)

        init_val = config.get(CONF_INITIAL_VALUE, DEFAULT_NUMBER_VALUE)
        try:
            val = float(init_val)
            self._attr_native_value = max(self._attr_native_min_value, min(self._attr_native_max_value, val))
        except (ValueError, TypeError):
            self._attr_native_value = self._attr_native_min_value

    def _restore_state(self, state, config):
        super()._restore_state(state, config)

        try:
            val = float(state.state)
            if self._attr_native_min_value <= val <= self._attr_native_max_value:
                self._attr_native_value = val
            else:
                self._attr_native_value = self._attr_native_min_value
        except (ValueError, TypeError):
            self._create_state(config)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        _LOGGER.debug(f"set {self.name} to {value}")
        self._attr_native_value = value
        self._update_attributes()
        self.async_write_ha_state()