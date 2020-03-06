"""
This component provides support for a virtual sensor.

"""

import logging
import pprint

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.components.sensor import DOMAIN
from homeassistant.helpers.entity import Entity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from . import COMPONENT_DOMAIN

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['virtual']

SENSOR_DOMAIN = COMPONENT_DOMAIN + '_SENSOR'

CONF_NAME = "name"
CONF_CLASS = "class"
CONF_INITIAL_VALUE = "initial_value"

DEFAULT_INITIAL_VALUE = 0

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_INITIAL_VALUE, default=DEFAULT_INITIAL_VALUE): cv.string,
})

SERVICE_SET = 'set'
SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
})

async def async_setup_platform(hass, config, async_add_entities, _discovery_info=None):

    sensors = [VirtualSensor(config)]
    async_add_entities(sensors, True)

    async def async_virtual_set(call):
        """Call virtual service handler."""
        _LOGGER.info("set: {}".format(pprint.pformat(call)))
        await async_virtual_set(hass, call)

    # Build up services...
    if hass.data.get(SENSOR_DOMAIN,None) is None:
        _LOGGER.info("installing handlers")
        hass.data[SENSOR_DOMAIN] = 'installed'
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_SET, async_virtual_set, schema=SERVICE_SCHEMA,
        )

class VirtualSensor(Entity):
    """An implementation of a Virtual Sensor."""

    def __init__(self, config):
        """Initialize an Virtual Sensor."""
        self._name = config.get(CONF_NAME)
        self._unique_id = self._name.lower().replace(' ', '_')
        self._class = config.get(CONF_CLASS)
        self._state = config.get(CONF_INITIAL_VALUE)
        _LOGGER.info('VirtualSensor: %s created', self._name)

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._class

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def set(self,value):
        self._state = value
        self.async_schedule_update_ha_state()

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        attrs = {
            'friendly_name': self._name,
            'unique_id': self._unique_id,
        }
        return attrs


def _get_sensor_from_entity_id(hass, entity_id):
    component = hass.data.get(DOMAIN)
    if component is None:
        raise HomeAssistantError('sensor component not set up')

    sensor = component.get_entity(entity_id)
    if sensor is None:
        raise HomeAssistantError('sensor not found')

    return sensor

async def async_virtual_on_service(hass, call):
    _LOGGER.info("{0} turning on".format(call.data['entity_id']))
    for entity_id in call.data['entity_id']:
        _get_sensor_from_entity_id(hass,entity_id).set(call.data['value'])

