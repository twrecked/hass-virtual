"""
This component provides support for a virtual sensor.

This class adds persistant to an entity. 
"""

import logging
import pprint

from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import slugify

from .const import (
    CONF_INITIAL_AVAILABILITY,
    CONF_NAME,
    CONF_PERSISTENT,
    COMPONENT_DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class VirtualEntity(RestoreEntity):
    """A base class to add state restoring.
    """

    # Are we saving/restoring this entity
    _persistant: bool = True

    def __init__(self, config, domain):
        """Initialize an Virtual Sensor."""
        self._config = config
        self._persistent = config.get(CONF_PERSISTENT)

        # Build the name. Are we adding the domain or not?
        # XXX I'm sort of stuck with this naming...
        # self.name is None to force the domain
        # self.unique_id is name, always
        # self._name = config.get(CONF_NAME)
        # self.no_domain_ = self._name.startswith("!")
        # if self.no_domain_:
        #     self._name = self._name[1:]
        # self._attr_unique_id = self._name.lower().replace(' ', '_')

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

        _LOGGER.info(f'VirtualEntity {self._attr_name} created')
        _LOGGER.info(f'VirtualEntity {self.unique_id} created')
        _LOGGER.info(f'VirtualEntity {self._config}')

    def _create_state(self, config):
        _LOGGER.info(f'VirtualEntity {self.unique_id}: creating initial state')
        self._available = config.get(CONF_INITIAL_AVAILABILITY)

    def _restore_state(self, state, config):
        _LOGGER.info(f'VirtualEntity {self.unique_id}: restoring state')
        _LOGGER.info(f'VirtualEntity:: {pprint.pformat(state.state)}')
        _LOGGER.info(f'VirtualEntity:: {pprint.pformat(state.attributes)}')
        self._attr_available = state.attributes.get('availibilty', config.get(CONF_INITIAL_AVAILABILITY))

    def _add_virtual_attributes(self, attrs):
        attrs.update({
            'persistant': self._persistent,
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

    # @property
    # def name(self) -> str:
    #     """Get entity name."""
    #     if self.no_domain_:
    #         return self._name
    #     else:
    #         return super().name

    def set_available(self, value):
        self._attr_available = value
        self.async_schedule_update_ha_state()
