"""
This component provides support for a virtual sensor.

This class adds persistence to an entity.
"""

import logging
import pprint
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import slugify

from .const import (
    COMPONENT_DOMAIN,
    CONF_INITIAL_AVAILABILITY,
    CONF_INITIAL_VALUE,
    CONF_NAME,
    CONF_PERSISTENT,
    DEFAULT_INITIAL_AVAILABILITY,
    DEFAULT_PERSISTENT,
)

_LOGGER = logging.getLogger(__name__)


def virtual_schema(default_initial_value: str, extra_attrs):
    schema = {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_INITIAL_VALUE, default=default_initial_value): cv.string,
        vol.Optional(CONF_INITIAL_AVAILABILITY, default=DEFAULT_INITIAL_AVAILABILITY): cv.boolean,
        vol.Optional(CONF_PERSISTENT, default=DEFAULT_PERSISTENT): cv.boolean,
    }
    schema.update(extra_attrs)
    return schema


class VirtualEntity(RestoreEntity):
    """A base class to add state restoring.
    """

    # Are we saving/restoring this entity
    _persistent: bool = True

    def __init__(self, config, domain):
        """Initialize an Virtual Sensor."""
        self._config = config
        self._persistent = config.get(CONF_PERSISTENT)

        # Build name, entity id and unique id. We do this because historically
        # the non-domain piece of the entity_id was prefixed with virtual_ so
        # we build the pieces manually to make sure.
        self._attr_name = config.get(CONF_NAME)
        if self._attr_name.startswith("!"):
            self._attr_name = self._attr_name[1:]
            self.entity_id = f'{domain}.{slugify(self._attr_name)}'
        else:
            self.entity_id = f'{domain}.{COMPONENT_DOMAIN}_{slugify(self._attr_name)}'
        self._attr_unique_id = slugify(self._attr_name)

        # We are virtual, we don't change unless we do it.
        self._attr_should_poll = False

        _LOGGER.info(f'VirtualEntity {self._attr_name} created')

    def _create_state(self, config):
        _LOGGER.info(f'VirtualEntity {self.unique_id}: creating initial state')
        self._available = config.get(CONF_INITIAL_AVAILABILITY)

    def _restore_state(self, state, config):
        _LOGGER.info(f'VirtualEntity {self.unique_id}: restoring state')
        _LOGGER.debug(f'VirtualEntity:: {pprint.pformat(state.state)}')
        _LOGGER.debug(f'VirtualEntity:: {pprint.pformat(state.attributes)}')
        self._attr_available = state.attributes.get('availibilty', config.get(CONF_INITIAL_AVAILABILITY))

    def _add_virtual_attributes(self, attrs):
        attrs.update({
            'persistent': self._persistent,
            'available': self._attr_available,
        })
        if _LOGGER.isEnabledFor(logging.DEBUG):
            attrs.update({
                'entity_id': self.entity_id,
                'unique_id': self.unique_id,
            })
        return attrs

    async def async_added_to_hass(self) -> None:
        _LOGGER.info(f'VirtualEntity {self._attr_unique_id}: async_added_to_hass')
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if not self._persistent or not state:
            self._create_state(self._config)
        else:
            self._restore_state(state, self._config)

    def set_available(self, value):
        self._attr_available = value
        self.async_schedule_update_ha_state()
