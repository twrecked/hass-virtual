"""
This component provides support for a virtual switch.

"""

import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.switch import SwitchDevice
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA)

_LOGGER = logging.getLogger(__name__)


CONF_NAME = "name"
CONF_INITIAL_VALUE = "initial_value"

DEFAULT_INITIAL_VALUE = "off"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_INITIAL_VALUE, default=DEFAULT_INITIAL_VALUE): cv.string,
})


async def async_setup_platform(_hass, config, async_add_entities, _discovery_info=None):
    switches = [VirtualSwitch(config)]
    async_add_entities(switches, True)


class VirtualSwitch(SwitchDevice):
    """Representation of a Virtual switch."""

    def __init__(self, config):
        """Initialize the Virtual switch device."""
        self._name = config.get(CONF_NAME)
        self._unique_id = self._name.lower().replace(' ', '_')
        self._state = config.get(CONF_INITIAL_VALUE)
        _LOGGER.info('VirtualSwitch: {} created'.format(self._name))

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the switch."""
        return self._state

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self.state == "on"

    @property
    def is_off(self):
        """Return true if switch is on."""
        return not self.is_on

    def turn_on(self, **kwargs):
        self._state = 'on'

    def turn_off(self, **kwargs):
        self._state = 'off'

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        attrs = {
            'friendly_name': self._name,
            'unique_id': self._unique_id,
        }
        return attrs

