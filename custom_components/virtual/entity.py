"""
This component provides support for a virtual sensor.

This class adds persistence to an entity.
"""

import logging
import pprint
from datetime import datetime
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.cover import ATTR_CURRENT_POSITION
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    STATE_CLOSED,
)
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_call_later
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

    def __init__(self, config, domain, old_style : bool = False):
        """Initialize an Virtual Sensor."""
        _LOGGER.debug(f"creating-virtual-{domain}={config}")
        self._config = config
        self._persistent = config.get(CONF_PERSISTENT)

        if old_style:
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

        else:
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


class VirtualOpenableEntity(VirtualEntity):
    """Representation of a Virtual openable.

    This can handle cover and valve devices. If they diverge too much in the
    future we will need to rethink this.
    """

    def __init__(self, config, domain, old_style: bool):
        """Initialize the Virtual openable device."""
        _LOGGER.debug(f"creating-virtual-openable-{domain}={config}")
        super().__init__(config, domain, old_style)

        self._attr_device_class = config.get(CONF_CLASS)
        self._open_close_duration = config.get(CONF_OPEN_CLOSE_DURATION)
        self._open_close_tick = config.get(CONF_OPEN_CLOSE_TICK)

        self._open_close_operation_started = None
        self._current_position = 0
        self._target_position = None

        _LOGGER.info(f"VirtualOpenable: {self.name} created")

    def _create_state(self, config):
        super()._create_state(config)

        self._attr_is_closed = config.get(CONF_INITIAL_VALUE).lower() == STATE_CLOSED
        if self._attr_is_closed:
            self._current_position = 0
        else:
            self._current_position = 100

    def _restore_state(self, state, config):
        super()._restore_state(state, config)

        # Cover and valve use the same position state. If this changes we will
        # need to add this into the derived class.
        if ATTR_CURRENT_POSITION in state.attributes:
            self._current_position = state.attributes[ATTR_CURRENT_POSITION]
        self._attr_is_closed = state.state.lower() == STATE_CLOSED

    def _update_attributes(self):
        super()._update_attributes()
        self._attr_extra_state_attributes.update({
            name: value for name, value in (
                (ATTR_DEVICE_CLASS, self._attr_device_class),
            ) if value is not None
        })

    def _stop(self) -> None:
        _LOGGER.info(f"stopping {self.name}")
        self._open_close_operation_started = None
        self._target_position = None
        self._attr_is_opening = False
        self._attr_is_closing = False

        if self._current_position > 0:
            self._attr_is_closed = False
        else:
            self._attr_is_closed = True

        self.async_write_ha_state()

    def _set_position(self, position) -> None:
        _LOGGER.info(f"setting {self.name} position {position}")

        self._target_position = position
        if self._target_position == self._current_position:
            return
        elif self._target_position < self._current_position:
            self._attr_is_opening = False
            self._attr_is_closing = True
        else:
            self._attr_is_opening = True
            self._attr_is_closing = False

        self.async_write_ha_state()
        self._open_close_operation_started = datetime.now()
        async_call_later(self.hass, self._open_close_tick, self._update_position)

    @callback
    def _update_position(self, _now) -> None:
        _LOGGER.info(f"updating {self.name} position {self._current_position}")
        if self._target_position is not None:
            if self._attr_is_closing and self._current_position <= self._target_position :
                self._stop()
            elif self._attr_is_opening and self._current_position >= self._target_position:
                self._stop()

        if self._target_position is None:
            return

        running_time_delta = datetime.now() - self._open_close_operation_started
        percent_moved = int((running_time_delta.total_seconds() / self._open_close_duration)*100)

        if self._attr_is_closing:
            self._current_position = max(0, self._current_position - percent_moved)
        elif self._attr_is_opening:
            self._current_position = min(100, self._current_position + percent_moved)

        self.async_write_ha_state()
        self._open_close_operation_started = datetime.now()
        async_call_later(self.hass, self._open_close_tick, self._update_position)
