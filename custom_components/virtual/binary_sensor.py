"""
This component provides support for a virtual binary sensor.

"""

import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.binary_sensor import BinarySensorEntity, DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA

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

DEFAULT_INITIAL_VALUE = 'off'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_INITIAL_VALUE, default=DEFAULT_INITIAL_VALUE): cv.string,
    vol.Optional(CONF_INITIAL_AVAILABILITY, default=DEFAULT_INITIAL_AVAILABILITY): cv.boolean,
    vol.Optional(CONF_PERSISTENT, default=DEFAULT_PERSISTENT): cv.boolean,

    vol.Optional(CONF_CLASS): cv.string,
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
        super().__init__(config, DOMAIN)

        self._attr_device_class = config.get(CONF_CLASS)

        self._attr_extra_state_attributes = self._add_virtual_attributes({
            name: value for name, value in (
                ('device_class', self._attr_device_class),
            ) if value is not None
        })

        _LOGGER.info('VirtualBinarySensor: %s created', self.name)

    def _create_state(self, config):
        super()._create_state(config)
        self._attr_is_on = config.get(CONF_INITIAL_VALUE).lower() == "on"

    def _restore_state(self, state, config):
        super()._restore_state(state, config)
        self._attr_is_on = state.state.lower() == "on"

    def turn_on(self):
        self._attr_is_on = True
        self.async_schedule_update_ha_state()

    def turn_off(self):
        self._attr_is_on = False
        self.async_schedule_update_ha_state()

    def toggle(self):
        if self.is_on:
            self.turn_off()
        else:
            self.turn_on()


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
