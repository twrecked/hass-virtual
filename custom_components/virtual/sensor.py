"""
This component provides support for a virtual sensor.

"""

import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import DOMAIN, SensorDeviceClass
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
    CONF_UNIT_OF_MEASUREMENT,
    FREQUENCY_GIGAHERTZ,
    PERCENTAGE,
    POWER_VOLT_AMPERE,
    POWER_VOLT_AMPERE_REACTIVE,
    PRESSURE_HPA,
    SIGNAL_STRENGTH_DECIBELS,
    VOLUME_CUBIC_METERS,
)
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity

from . import get_entity_from_domain
from .const import (
    COMPONENT_DOMAIN,
    COMPONENT_SERVICES,
    CONF_CLASS,
    CONF_INITIAL_AVAILABILITY,
    CONF_INITIAL_VALUE,
    CONF_NAME,
    CONF_PERSISTENT,
    DEFAULT_INITIAL_AVAILABILITY,
    DEFAULT_PERSISTENT,
)
from .entity import VirtualEntity

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_INITIAL_VALUE = '0'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_INITIAL_VALUE, default=DEFAULT_INITIAL_VALUE): cv.string,
    vol.Optional(CONF_INITIAL_AVAILABILITY, default=DEFAULT_INITIAL_AVAILABILITY): cv.boolean,
    vol.Optional(CONF_PERSISTENT, default=DEFAULT_PERSISTENT): cv.boolean,

    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=""): cv.string,
})

SERVICE_SET = 'set'
SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required('value'): cv.string,
})

UNITS_OF_MEASUREMENT = {
    SensorDeviceClass.APPARENT_POWER: POWER_VOLT_AMPERE,  # apparent power (VA)
    SensorDeviceClass.BATTERY: PERCENTAGE,  # % of battery that is left
    SensorDeviceClass.CO: CONCENTRATION_PARTS_PER_MILLION,  # ppm of CO concentration
    SensorDeviceClass.CO2: CONCENTRATION_PARTS_PER_MILLION,  # ppm of CO2 concentration
    SensorDeviceClass.HUMIDITY: PERCENTAGE,  # % of humidity in the air
    SensorDeviceClass.ILLUMINANCE: "lm",  # current light level (lx/lm)
    SensorDeviceClass.NITROGEN_DIOXIDE: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of nitrogen dioxide
    SensorDeviceClass.NITROGEN_MONOXIDE: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of nitrogen monoxide
    SensorDeviceClass.NITROUS_OXIDE: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of nitrogen oxide
    SensorDeviceClass.OZONE: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of ozone
    SensorDeviceClass.PM1: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of PM1
    SensorDeviceClass.PM10: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of PM10
    SensorDeviceClass.PM25: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of PM2.5
    SensorDeviceClass.SIGNAL_STRENGTH: SIGNAL_STRENGTH_DECIBELS,  # signal strength (dB/dBm)
    SensorDeviceClass.SULPHUR_DIOXIDE: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of sulphur dioxide
    SensorDeviceClass.TEMPERATURE: "C",  # temperature (C/F)
    SensorDeviceClass.PRESSURE: PRESSURE_HPA,  # pressure (hPa/mbar)
    SensorDeviceClass.POWER: "kW",  # power (W/kW)
    SensorDeviceClass.CURRENT: "A",  # current (A)
    SensorDeviceClass.ENERGY: "kWh",  # energy (Wh/kWh/MWh)
    SensorDeviceClass.FREQUENCY: FREQUENCY_GIGAHERTZ,  # energy (Hz/kHz/MHz/GHz)
    SensorDeviceClass.POWER_FACTOR: PERCENTAGE,  # power factor (no unit, min: -1.0, max: 1.0)
    SensorDeviceClass.REACTIVE_POWER: POWER_VOLT_AMPERE_REACTIVE,  # reactive power (var)
    SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of vocs
    SensorDeviceClass.VOLTAGE: "V",  # voltage (V)
    SensorDeviceClass.GAS: VOLUME_CUBIC_METERS,  # gas (m³)
}


async def async_setup_platform(hass, config, async_add_entities, _discovery_info=None):
    sensors = [VirtualSensor(config)]
    async_add_entities(sensors, True)

    async def async_virtual_service(call):
        """Call virtual service handler."""
        _LOGGER.info("{} service called".format(call.service))
        await async_virtual_set_service(hass, call)

    # Build up services...
    if not hasattr(hass.data[COMPONENT_SERVICES], DOMAIN):
        _LOGGER.info("installing handlers")
        hass.data[COMPONENT_SERVICES][DOMAIN] = 'installed'
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_SET, async_virtual_service, schema=SERVICE_SCHEMA,
        )


class VirtualSensor(VirtualEntity, Entity):
    """An implementation of a Virtual Sensor."""

    def __init__(self, config):
        """Initialize an Virtual Sensor."""
        super().__init__(config, DOMAIN)

        self._attr_device_class = config.get(CONF_CLASS)

        # Set unit of measurement
        self._attr_unit_of_measurement = config.get(CONF_UNIT_OF_MEASUREMENT)
        if not self._attr_unit_of_measurement and self._attr_device_class in UNITS_OF_MEASUREMENT.keys():
            self._attr_unit_of_measurement = UNITS_OF_MEASUREMENT[self._attr_device_class]

        self._attr_extra_state_attributes = self._add_virtual_attributes({
            name: value for name, value in (
                ('device_class', self._attr_device_class),
                ('unite_of_measurement', self._attr_unit_of_measurement),
            ) if value is not None
        })

        _LOGGER.info('VirtualSensor: %s created', self.name)

    def _create_state(self, config):
        super()._create_state(config)
        self._attr_state = config.get(CONF_INITIAL_VALUE)

    def _restore_state(self, state, config):
        super()._restore_state(state, config)
        self._attr_state = state.state

    def set(self, value) -> None:
        self._attr_state = value
        self.async_schedule_update_ha_state()


async def async_virtual_set_service(hass, call):
    for entity_id in call.data['entity_id']:
        value = call.data['value']
        _LOGGER.info("{} set(value={})".format(entity_id, value))
        get_entity_from_domain(hass, DOMAIN, entity_id).set(value)
