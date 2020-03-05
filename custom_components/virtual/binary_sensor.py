"""
This component provides support for a virtual binary sensor.

"""

import logging
import pprint

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.components.binary_sensor import (BinarySensorDevice,
        DOMAIN )
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA)
from . import COMPONENT_DOMAIN

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['virtual']

BINARY_SENSOR_DOMAIN = COMPONENT_DOMAIN + '_BINARY_SENSOR'

CONF_NAME = "name"
CONF_CLASS = "class"
CONF_INITIAL_VALUE = "initial_value"

DEFAULT_INITIAL_VALUE = "off"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_INITIAL_VALUE, default=DEFAULT_INITIAL_VALUE): cv.string,
})

SERVICE_ON = 'turn_on'
SERVICE_OFF = 'turn_off'
SERVICE_TOGGLE = 'toggle'
SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
})


async def async_setup_platform(hass, config, async_add_entities, _discovery_info=None):

    sensors = [VirtualBinarySensor(config)]
    async_add_entities(sensors, True)

    async def async_virtual_on(call):
        """Call virtual service handler."""
        _LOGGER.info("turn_on: {}".format(pprint.pformat(call)))
        await async_virtual_on_service(hass, call)

    async def async_virtual_off(call):
        """Call virtual service handler."""
        await async_virtual_off_service(hass, call)

    async def async_virtual_toggle(call):
        """Call virtual service handler."""
        await async_virtual_toggle_service(hass, call)

    # Build up services...
    if hass.data.get(BINARY_SENSOR_DOMAIN,None) is None:
        _LOGGER.info("installing handlers")
        hass.data[BINARY_SENSOR_DOMAIN] = 'installed'
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_ON, async_virtual_on, schema=SERVICE_SCHEMA,
        )
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_OFF, async_virtual_off, schema=SERVICE_SCHEMA,
        )
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_TOGGLE, async_virtual_toggle, schema=SERVICE_SCHEMA,
        )


class VirtualBinarySensor(BinarySensorDevice):
    """An implementation of a Virtual Binary Sensor."""

    def __init__(self, config):
        """Initialize an Virtual Binary Sensor."""
        self._name = config.get(CONF_NAME)
        self._unique_id = self._name.lower().replace(' ', '_')
        self._class = config.get(CONF_CLASS)
        self._state = config.get(CONF_INITIAL_VALUE)
        _LOGGER.info('VirtualBinarySensor: %s created', self._name)

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._class

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._state == 'on'

    def turn_on(self):
        self._state = 'on'
        self.async_schedule_update_ha_state()

    def turn_off(self):
        self._state = 'off'
        self.async_schedule_update_ha_state()

    def toggle(self):
        if self.is_on:
            self.turn_off()
        else:
            self.turn_on()

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        attrs = {
            'friendly_name': self._name,
            'unique_id': self._unique_id,
        }
        return attrs


def _get_binary_sensor_from_entity_id(hass, entity_id):
    component = hass.data.get(DOMAIN)
    if component is None:
        raise HomeAssistantError('binary_sensor component not set up')

    binary_sensor = component.get_entity(entity_id)
    if binary_sensor is None:
        raise HomeAssistantError('binary_sensor not found')

    return binary_sensor

async def async_virtual_on_service(hass, call):
    _LOGGER.info("{0} turning on".format(call.data['entity_id']))
    binary_sensor = _get_binary_sensor_from_entity_id(hass,call.data['entity_id'][0])
    binary_sensor.turn_on()

async def async_virtual_off_service(hass, call):
    _LOGGER.info("{0} turning off".format(call.data['entity_id']))
    binary_sensor = _get_binary_sensor_from_entity_id(hass,call.data['entity_id'][0])
    binary_sensor.turn_off()

async def async_virtual_toggle_service(hass, call):
    _LOGGER.info("{0} turning off".format(call.data['entity_id']))
    binary_sensor = _get_binary_sensor_from_entity_id(hass,call.data['entity_id'][0])
    binary_sensor.toggle()

