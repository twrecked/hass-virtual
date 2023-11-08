"""
This component provides support for a virtual sensor.

This class adds persistence to an entity.
"""

import logging
import pprint
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import slugify

from .const import *


_LOGGER = logging.getLogger(__name__)


def virtual_schema(default_initial_value: str, extra_attrs):
    schema = {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_INITIAL_VALUE, default=default_initial_value): cv.string,
        vol.Optional(CONF_INITIAL_AVAILABILITY, default=DEFAULT_AVAILABILITY): cv.boolean,
        vol.Optional(CONF_PERSISTENT, default=DEFAULT_PERSISTENT): cv.boolean,
        vol.Optional(ATTR_DEVICE_ID, default="NOTYET"): cv.string,
        vol.Optional(ATTR_ENTITY_ID, default="NOTYET"): cv.string,
        vol.Optional(ATTR_UNIQUE_ID, default="NOTYET"): cv.string,
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
        _LOGGER.debug(f"creating-virtual-{domain}={config}")
        self._config = config
        self._persistent = config.get(CONF_PERSISTENT)

        # Build name, entity id and unique id. We do this because historically
        # the non-domain piece of the entity_id was prefixed with virtual_ so
        # we build the pieces manually to make sure.
        self._attr_name = config.get(CONF_NAME)

        self.entity_id = config.get(ATTR_ENTITY_ID)
        if self.entity_id == "NOTYET":
            if self._attr_name.startswith("+"):
                self._attr_name = self._attr_name[1:]
                self.entity_id = f'{domain}.{COMPONENT_DOMAIN}_{slugify(self._attr_name)}'
            else:
                self.entity_id = f'{domain}.{slugify(self._attr_name)}'

        self._attr_unique_id = config.get(ATTR_UNIQUE_ID, None)
        if self._attr_unique_id == "NOTYET":
            self._attr_unique_id = slugify(self._attr_name)

        if config.get(ATTR_DEVICE_ID) != "NOTYET":
            _LOGGER.debug("setting up device info")
            self._attr_device_info = DeviceInfo(
                identifiers={(COMPONENT_DOMAIN, config.get(ATTR_DEVICE_ID))},
                manufacturer=COMPONENT_MANUFACTURER,
                model=COMPONENT_MODEL,
            )

        _LOGGER.info(f'VirtualEntity {self._attr_name} created')

    def _create_state(self, config):
        _LOGGER.info(f'VirtualEntity {self.unique_id}: creating initial state')
        self._attr_available = config.get(CONF_INITIAL_AVAILABILITY)

    def _restore_state(self, state, config):
        _LOGGER.info(f'VirtualEntity {self.unique_id}: restoring state')
        _LOGGER.debug(f'VirtualEntity:: state={pprint.pformat(state.state)}')
        _LOGGER.debug(f'VirtualEntity:: attr={pprint.pformat(state.attributes)}')
        self._attr_available = state.attributes.get(ATTR_AVAILABLE)

    def _update_attributes(self):
        self._attr_extra_state_attributes = {
            ATTR_PERSISTENT: self._persistent,
            ATTR_AVAILABLE: self._attr_available,
        }
        if _LOGGER.isEnabledFor(logging.DEBUG):
            self._attr_extra_state_attributes.update({
                ATTR_ENTITY_ID: self.entity_id,
                ATTR_UNIQUE_ID: self.unique_id,
            })

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if not self._persistent or not state:
            self._create_state(self._config)
        else:
            self._restore_state(state, self._config)
        self._update_attributes()

    async def async_will_remove_from_hass(self) -> None:
        """Call when entity is being removed from hass."""
        await super().async_will_remove_from_hass()

    def set_available(self, value):
        self._attr_available = value
        self._update_attributes()
        self.async_schedule_update_ha_state()
