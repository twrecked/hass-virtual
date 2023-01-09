"""
This component provides support for a virtual lock.

"""

import logging
import voluptuous as vol
from typing import Any

import homeassistant.helpers.config_validation as cv
from homeassistant.components.lock import LockEntity, DOMAIN
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.const import STATE_LOCKED

from .const import (
    COMPONENT_DOMAIN,
    CONF_INITIAL_VALUE,
)
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_INITIAL_VALUE = "locked"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_INITIAL_VALUE, {}))


async def async_setup_platform(_hass, config, async_add_entities, _discovery_info=None):
    locks = [VirtualLock(config)]
    async_add_entities(locks, True)


class VirtualLock(VirtualEntity, LockEntity):
    """Representation of a Virtual lock."""

    def __init__(self, config):
        """Initialize the Virtual lock device."""
        super().__init__(config, DOMAIN)

        self._attr_extra_state_attributes = self._add_virtual_attributes({})

        _LOGGER.info('VirtualLock: {} created'.format(self.name))

    def _create_state(self, config):
        super()._create_state(config)
        self._attr_is_locked = config.get(CONF_INITIAL_VALUE).lower() == STATE_LOCKED

    def _restore_state(self, state, config):
        super()._restore_state(state, config)
        self._attr_is_locked = state.state == STATE_LOCKED

    def lock(self, **kwargs: Any) -> None:
        self._attr_is_locked = True

    def unlock(self, **kwargs: Any) -> None:
        self._attr_is_locked = False

    def open(self, **kwargs: Any) -> None:
        pass
