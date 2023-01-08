"""
This component provides support for a virtual sensor.

This class adds persistant to an entity. 
"""

import logging
import pprint

from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_CLASS,
    CONF_INITIAL_AVAILABILITY,
    CONF_INITIAL_VALUE,
    CONF_NAME,
    CONF_PERSISTENT,
)

_LOGGER = logging.getLogger(__name__)


class VirtualEntity(RestoreEntity):
    """A base class to add state restoring.
    """
    def __init__(self, config):
        """Initialize an Virtual Sensor."""
        self._name = config.get(CONF_NAME)
        self._class = config.get(CONF_CLASS)
        self._state = None
        self._persistent = config.get(CONF_PERSISTENT)
        self._initial_value = config.get(CONF_INITIAL_VALUE)
        self._available = config.get(CONF_INITIAL_AVAILABILITY)

        # Are we adding the domain or not?
        self.no_domain_ = self._name.startswith("!")
        if self.no_domain_:
            self._name = self.name[1:]
        self._unique_id = self._name.lower().replace(' ', '_')

        _LOGGER.info(f'VirtualEntity {self._name} created')
        _LOGGER.info(f'VirtualEntity {self._unique_id} created')

    def _restore_state(self, state):
        _LOGGER.info(f'VirtualEntity {self._unique_id}: restoring state')
        _LOGGER.info(f'VirtualEntity: {pprint.pformat(state.state)}')
        self._state = state.state

    async def async_added_to_hass(self) -> None:
        _LOGGER.info('VirtualEntity {self._unique_id}: async_added_to_hass')
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if not self._persistent or not state:
            _LOGGER.info(f'VirtualEntity {self._unique_id}: using initial value')
            self._state = self._initial_value
            return
        self._restore_state(state)

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
