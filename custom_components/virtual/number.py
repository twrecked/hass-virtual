"""
This component provides support for a virtual number.

"""

import logging
import voluptuous as vol
from collections.abc import Callable

import homeassistant.helpers.config_validation as cv
from homeassistant.components.number import (
    ATTR_MAX, ATTR_MIN, DOMAIN as PLATFORM_DOMAIN,
    NumberDeviceClass
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
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
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import get_entity_from_domain, get_entity_configs
from .const import *
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


class VirtualNumber(VirtualEntity, Entity):
    """An implementation of a Virtual Number."""

    def __init__(self, config, old_style: bool):
        """Initialize an Virtual Number."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_device_class = config.get(CONF_CLASS)

        self.min_value = config.get(CONF_MIN)
        self.max_value = config.get(CONF_MAX)

        # Set unit of measurement
        self._attr_unit_of_measurement = config.get(CONF_UNIT_OF_MEASUREMENT)
        if not self._attr_unit_of_measurement and self._attr_device_class in UNITS_OF_MEASUREMENT.keys():
            self._attr_unit_of_measurement = UNITS_OF_MEASUREMENT[self._attr_device_class]

        _LOGGER.info(f"VirtualSensor: {self.name} created")

    def convert_to_native_value(self, value: float) -> float:
        return value

    @property
    def native_min_value(self):
        return self.min_value

    @property
    def native_max_value(self):
        return self.max_value

    def _create_state(self, config):
        super()._create_state(config)

        self._attr_state = config.get(CONF_INITIAL_VALUE)

    def _restore_state(self, state, config):
        super()._restore_state(state, config)

        self._attr_state = state.state

    def _update_attributes(self):
        super()._update_attributes()
        self._attr_extra_state_attributes.update({
            name: value for name, value in (
                (ATTR_DEVICE_CLASS, self._attr_device_class),
                (ATTR_UNIT_OF_MEASUREMENT, self._attr_unit_of_measurement),
                (ATTR_MIN, self.min_value),
                (ATTR_MAX, self.max_value)
            ) if value is not None
        })

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self.hass.async_add_executor_job(self.set, value)

    def set(self, value) -> None:
        _LOGGER.debug(f"set {self.name} to {value}")
        self._attr_state = value
        #self.async_schedule_update_ha_state()