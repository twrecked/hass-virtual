"""
This component provides support for a virtual binary sensor.

"""

import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.binary_sensor import BinarySensorEntity, DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, ATTR_DEVICE_CLASS
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.const import STATE_ON

from . import get_entity_from_domain
from .const import (
    COMPONENT_DOMAIN,
    COMPONENT_SERVICES,
    CONF_CLASS,
    CONF_INITIAL_VALUE,
)
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_INITIAL_VALUE = 'off'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_INITIAL_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
}))

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
        _LOGGER.debug(f"{call.service} service called")
        if call.service == SERVICE_ON:
            await async_virtual_on_service(hass, call)
        if call.service == SERVICE_OFF:
            await async_virtual_off_service(hass, call)
        if call.service == SERVICE_TOGGLE:
            await async_virtual_toggle_service(hass, call)

    # Build up services...
    if not hasattr(hass.data[COMPONENT_SERVICES], DOMAIN):
        _LOGGER.debug("installing handlers")
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

        _LOGGER.info('VirtualBinarySensor: %s created', self.name)

    def _create_state(self, config):
        super()._create_state(config)

        self._attr_is_on = config.get(CONF_INITIAL_VALUE).lower() == STATE_ON

    def _restore_state(self, state, config):
        super()._restore_state(state, config)

        self._attr_is_on = state.state.lower() == STATE_ON

    def _update_attributes(self):
        super()._update_attributes();
        self._attr_extra_state_attributes.update({
            name: value for name, value in (
                (ATTR_DEVICE_CLASS, self._attr_device_class),
            ) if value is not None
        })

    def turn_on(self) -> None:
        _LOGGER.debug(f"turning {self.name} on")
        self._attr_is_on = True
        self.async_schedule_update_ha_state()

    def turn_off(self) -> None:
        _LOGGER.debug(f"turning {self.name} off")
        self._attr_is_on = False
        self.async_schedule_update_ha_state()

    def toggle(self) -> None:
        if self.is_on:
            self.turn_off()
        else:
            self.turn_on()


async def async_virtual_on_service(hass, call):
    for entity_id in call.data['entity_id']:
        _LOGGER.debug(f"turning on {entity_id}")
        get_entity_from_domain(hass, DOMAIN, entity_id).turn_on()


async def async_virtual_off_service(hass, call):
    for entity_id in call.data['entity_id']:
        _LOGGER.debug(f"turning off {entity_id}")
        get_entity_from_domain(hass, DOMAIN, entity_id).turn_off()


async def async_virtual_toggle_service(hass, call):
    for entity_id in call.data['entity_id']:
        _LOGGER.debug(f"toggling {entity_id}")
        get_entity_from_domain(hass, DOMAIN, entity_id).toggle()
