"""
This component provides support for a virtual binary sensor.

"""

import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.binary_sensor import (BinarySensorEntity, DOMAIN)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA)
from . import COMPONENT_DOMAIN, COMPONENT_SERVICES, get_entity_from_domain
from .entity import VirtualEntity

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

CONF_NAME = "name"
CONF_CLASS = "class"
CONF_INITIAL_VALUE = "initial_value"
CONF_INITIAL_AVAILABILITY = "initial_availability"

DEFAULT_INITIAL_VALUE = "off"
DEFAULT_INITIAL_AVAILABILITY = True

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_INITIAL_VALUE, default=DEFAULT_INITIAL_VALUE): cv.string,
    vol.Optional(CONF_INITIAL_AVAILABILITY, default=DEFAULT_INITIAL_AVAILABILITY): cv.boolean,
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

    async def async_virtual_service(call):
        """Call virtual service handler."""
        _LOGGER.info("{} service called".format(call.service))
        if call.service == SERVICE_ON:
            await async_virtual_on_service(hass, call)
        if call.service == SERVICE_OFF:
            await async_virtual_off_service(hass, call)
        if call.service == SERVICE_TOGGLE:
            await async_virtual_toggle_service(hass, call)

    # Build up services...
    if not hasattr(hass.data[COMPONENT_SERVICES], DOMAIN):
        _LOGGER.info("installing handlers")
        hass.data[COMPONENT_SERVICES][DOMAIN] = 'installed'
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_ON, async_virtual_service, schema=SERVICE_SCHEMA,
        )
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_OFF, async_virtual_service, schema=SERVICE_SCHEMA,
        )
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_TOGGLE, async_virtual_service, schema=SERVICE_SCHEMA,
        )


class VirtualBinarySensor(VirtualEntity, BinarySensorEntity):
    """An implementation of a Virtual Binary Sensor."""

    def __init__(self, config):
        """Initialize a Virtual Binary Sensor."""
        super().__init__(config)
        # self._name = config.get(CONF_NAME)
        # self._class = config.get(CONF_CLASS)
        # self._state = config.get(CONF_INITIAL_VALUE)
        # self._available = config.get(CONF_INITIAL_AVAILABILITY)

        # Are we adding the domain or not?
        # self.no_domain_ = self._name.startswith("!")
        # if self.no_domain_:
        #     self._name = self.name[1:]
        # self._unique_id = self._name.lower().replace(' ', '_')

        _LOGGER.info('VirtualBinarySensor: %s created', self._name)

    # @property
    # def name(self):
    #     if self.no_domain_:
    #         return self._name
    #     else:
    #         return super().name
    #
    # @property
    # def unique_id(self):
    #     """Return a unique ID."""
    #     return self._unique_id
    #
    # @property
    # def device_class(self):
    #     """Return the device class of the sensor."""
    #     return self._class

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._state == 'on'

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available

    def set_available(self, value):
        self._available = value
        self.async_schedule_update_ha_state()

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
    def extra_state_attributes(self):
        """Return the device state attributes."""
        attrs = {
            'friendly_name': self._name,
            'unique_id': self._unique_id,
        }
        return attrs


async def async_virtual_on_service(hass, call):
    for entity_id in call.data['entity_id']:
        _LOGGER.info("{} turning on".format(entity_id))
        get_entity_from_domain(hass, DOMAIN, entity_id).turn_on()


async def async_virtual_off_service(hass, call):
    for entity_id in call.data['entity_id']:
        _LOGGER.info("{} turning off".format(entity_id))
        get_entity_from_domain(hass, DOMAIN, entity_id).turn_off()


async def async_virtual_toggle_service(hass, call):
    for entity_id in call.data['entity_id']:
        _LOGGER.info("{} toggling".format(entity_id))
        get_entity_from_domain(hass, DOMAIN, entity_id).toggle()
