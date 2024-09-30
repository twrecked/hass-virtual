"""
This component provides support for a virtual sensor.

"""

import logging
import voluptuous as vol
from collections.abc import Callable

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import (
    DOMAIN as PLATFORM_DOMAIN,
    SensorDeviceClass
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

DEFAULT_SENSOR_VALUE = "0"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_SENSOR_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=""): cv.string,
}))
SENSOR_SCHEMA = vol.Schema(virtual_schema(DEFAULT_SENSOR_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=""): cv.string,
}))

SERVICE_SET = "set"
SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required(ATTR_VALUE): cv.string,
})

UNITS_OF_MEASUREMENT = {
    SensorDeviceClass.APPARENT_POWER: UnitOfApparentPower.VOLT_AMPERE,  # apparent power (VA)
    SensorDeviceClass.BATTERY: PERCENTAGE,  # % of battery that is left
    SensorDeviceClass.CO: CONCENTRATION_PARTS_PER_MILLION,  # ppm of CO concentration
    SensorDeviceClass.CO2: CONCENTRATION_PARTS_PER_MILLION,  # ppm of CO2 concentration
    SensorDeviceClass.HUMIDITY: PERCENTAGE,  # % of humidity in the air
    SensorDeviceClass.ILLUMINANCE: LIGHT_LUX,  # current light level (lx/lm)
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
    SensorDeviceClass.PRESSURE: UnitOfPressure.HPA,  # pressure (hPa/mbar)
    SensorDeviceClass.POWER: UnitOfPower.KILO_WATT,  # power (W/kW)
    SensorDeviceClass.CURRENT: UnitOfElectricCurrent.AMPERE,  # current (A)
    SensorDeviceClass.ENERGY: UnitOfEnergy.KILO_WATT_HOUR,  # energy (Wh/kWh/MWh)
    SensorDeviceClass.FREQUENCY: UnitOfFrequency.GIGAHERTZ,  # energy (Hz/kHz/MHz/GHz)
    SensorDeviceClass.POWER_FACTOR: PERCENTAGE,  # power factor (no unit, min: -1.0, max: 1.0)
    SensorDeviceClass.REACTIVE_POWER: UnitOfReactivePower.VOLT_AMPERE_REACTIVE,  # reactive power (var)
    SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,  # µg/m³ of vocs
    SensorDeviceClass.VOLTAGE: UnitOfElectricPotential.VOLT,  # voltage (V)
    SensorDeviceClass.GAS: UnitOfVolume.CUBIC_METERS,  # gas (m³)
}


def setup_services(hass: HomeAssistant) -> None:

    async def async_virtual_service(call):
        """Call virtual service handler."""
        _LOGGER.debug(f"{call.service} service called")
        await async_virtual_set_service(hass, call)

    # Build up services...
    if not hasattr(hass.data[COMPONENT_SERVICES], PLATFORM_DOMAIN):
        _LOGGER.debug("installing handlers")
        hass.data[COMPONENT_SERVICES][PLATFORM_DOMAIN] = "installed"
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_SET, async_virtual_service, schema=SERVICE_SCHEMA,
        )


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")

        sensors = [VirtualSensor(config, True)]
        async_add_entities(sensors, True)
        setup_services(hass)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the entries...")

    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = SENSOR_SCHEMA(entity)
        entities.append(VirtualSensor(entity, False))
    async_add_entities(entities)
    setup_services(hass)


class VirtualSensor(VirtualEntity, Entity):
    """An implementation of a Virtual Sensor."""

    def __init__(self, config, old_style: bool):
        """Initialize an Virtual Sensor."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_device_class = config.get(CONF_CLASS)

        # Set unit of measurement
        self._attr_unit_of_measurement = config.get(CONF_UNIT_OF_MEASUREMENT)
        if not self._attr_unit_of_measurement and self._attr_device_class in UNITS_OF_MEASUREMENT.keys():
            self._attr_unit_of_measurement = UNITS_OF_MEASUREMENT[self._attr_device_class]

        _LOGGER.info(f"VirtualSensor: {self.name} created")

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
            ) if value is not None
        })

    def set(self, value) -> None:
        _LOGGER.debug(f"set {self.name} to {value}")
        self._attr_state = value
        self.async_schedule_update_ha_state()


async def async_virtual_set_service(hass, call):
    for entity_id in call.data[ATTR_ENTITY_ID]:
        value = call.data[ATTR_VALUE]
        _LOGGER.debug(f"setting {entity_id} to {value})")
        get_entity_from_domain(hass, PLATFORM_DOMAIN, entity_id).set(value)
