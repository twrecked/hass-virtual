"""
This component provides support for a virtual switch.

"""

import logging
import voluptuous as vol
from typing import Any

import homeassistant.helpers.config_validation as cv
from homeassistant.components.switch import SwitchEntity, DOMAIN
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    STATE_ON,
)

from .const import (
    COMPONENT_DOMAIN,
    CONF_INITIAL_VALUE,
    CONF_CLASS,
)
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEFAULT_INITIAL_VALUE = "off"

DEPENDENCIES = [COMPONENT_DOMAIN]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_INITIAL_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
}))


async def async_setup_platform(_hass, config, async_add_entities, _discovery_info=None):
    switches = [VirtualSwitch(config)]
    async_add_entities(switches, True)


class VirtualSwitch(VirtualEntity, SwitchEntity):
    """Representation of a Virtual switch."""

    def __init__(self, config):
        """Initialize the Virtual switch device."""
        super().__init__(config, DOMAIN)

        self._attr_device_class = config.get(CONF_CLASS)

        _LOGGER.info('VirtualSwitch: {} created'.format(self.name))

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

    def turn_on(self, **kwargs: Any) -> None:
        _LOGGER.debug(f"turning {self.name} on")
        self._attr_is_on = True

    def turn_off(self, **kwargs: Any) -> None:
        _LOGGER.debug(f"turning {self.name} off")
        self._attr_is_on = False
