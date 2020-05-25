"""
This component provides support for a virtual lock.

"""

import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.lock import LockEntity
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA)

_LOGGER = logging.getLogger(__name__)

CONF_NAME = "name"
CONF_INITIAL_VALUE = "initial_value"

DEFAULT_INITIAL_VALUE = "locked"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_INITIAL_VALUE, default=DEFAULT_INITIAL_VALUE): cv.string,
})


async def async_setup_platform(_hass, config, async_add_entities, _discovery_info=None):
    locks = [VirtualLock(config)]
    async_add_entities(locks, True)


class VirtualLock(LockEntity):
    """Representation of a Virtual lock."""

    def __init__(self, config):
        """Initialize the Virtual lock device."""
        self._name = config.get(CONF_NAME)
        self._unique_id = self._name.lower().replace(' ', '_')
        self._state = config.get(CONF_INITIAL_VALUE)
        _LOGGER.info('VirtualLock: {} created'.format(self._name))

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the lock."""
        return self._state

    @property
    def is_locked(self):
        """Return true if lock is on."""
        return self.state == "locked"

    def lock(self, **kwargs):
        self._state = 'locked'

    def unlock(self, **kwargs):
        self._state = 'unlocked'

    def open(self, **kwargs):
        pass

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        attrs = {
            'friendly_name': self._name,
            'unique_id': self._unique_id,
        }
        return attrs
