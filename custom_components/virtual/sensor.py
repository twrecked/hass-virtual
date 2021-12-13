"""
This component provides support for a virtual sensor.

"""

import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from . import COMPONENT_DOMAIN, COMPONENT_SERVICES, get_entity_from_domain

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

CONF_NAME = "name"
CONF_CLASS = "class"
CONF_INITIAL_VALUE = "initial_value"
CONF_INITIAL_AVAILABILITY = "initial_availability"

DEFAULT_INITIAL_VALUE = 0
DEFAULT_INITIAL_AVAILABILITY = True

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_INITIAL_VALUE, default=DEFAULT_INITIAL_VALUE): cv.string,
    vol.Optional(CONF_INITIAL_AVAILABILITY, default=DEFAULT_INITIAL_AVAILABILITY): cv.boolean,
})

SERVICE_SET = 'set'
SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required('value'): cv.string,
})


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


class VirtualSensor(Entity):
    """An implementation of a Virtual Sensor."""

    def __init__(self, config):
        """Initialize an Virtual Sensor."""
        self._name = config.get(CONF_NAME)

        # Are we adding the domain or not?
        self.no_domain_ = self._name.startswith("!")
        if self.no_domain_:
            self._name = self.name[1:]
        self._unique_id = self._name.lower().replace(' ', '_')

        self._class = config.get(CONF_CLASS)
        self._state = config.get(CONF_INITIAL_VALUE)
        self._available = config.get(CONF_INITIAL_AVAILABILITY)
        _LOGGER.info('VirtualSensor: %s created', self._name)

    @property
    def name(self):
        if self.no_domain_:
            return self._name
        else:
            return super().name

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

    def set(self, value):
        self._state = value
        self.async_schedule_update_ha_state()

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available

    def set_available(self, value):
        self._available = value
        self.async_schedule_update_ha_state()

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        attrs = {
            'friendly_name': self._name,
            'unique_id': self._unique_id,
        }
        return attrs


async def async_virtual_set_service(hass, call):
    for entity_id in call.data['entity_id']:
        value = call.data['value']
        _LOGGER.info("{} set(value={})".format(entity_id, value))
        get_entity_from_domain(hass, DOMAIN, entity_id).set(value)
