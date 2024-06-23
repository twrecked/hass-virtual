"""
This component provides support for a virtual cover.

"""

import logging
import voluptuous as vol
from typing import Any
from collections.abc import Callable
from datetime import datetime

import homeassistant.helpers.config_validation as cv
from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
    DOMAIN as PLATFORM_DOMAIN
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    STATE_CLOSED,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.event import async_call_later

from . import get_entity_configs
from .const import *
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_COVER_VALUE = "open"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_COVER_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_OPEN_CLOSE_DURATION, default=10): cv.positive_int,
    vol.Optional(CONF_OPEN_CLOSE_TICK, default=1): cv.positive_int,
}))
COVER_SCHEMA = vol.Schema(virtual_schema(DEFAULT_COVER_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_OPEN_CLOSE_DURATION, default=10): cv.positive_int,
    vol.Optional(CONF_OPEN_CLOSE_TICK, default=1): cv.positive_int,
}))


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the entries...")

    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = COVER_SCHEMA(entity)
        entities.append(VirtualCover(entity))
    async_add_entities(entities)


class VirtualCover(VirtualEntity, CoverEntity):
    """Representation of a Virtual cover."""

    def __init__(self, config):
        """Initialize the Virtual cover device."""
        super().__init__(config, PLATFORM_DOMAIN)

        self._attr_device_class = config.get(CONF_CLASS)
        self._attr_supported_features = CoverEntityFeature(
            CoverEntityFeature.OPEN |
            CoverEntityFeature.CLOSE |
            CoverEntityFeature.STOP |
            CoverEntityFeature.SET_POSITION
        )
        self._attr_current_cover_position = 0
        self._virtual_duration = config.get(CONF_OPEN_CLOSE_DURATION)
        self._virtual_tick = config.get(CONF_OPEN_CLOSE_TICK)
        self._virtual_operation_started = None
        self._target_cover_position = None

        _LOGGER.info(f"VirtualCover: {self.name} created")

    def _create_state(self, config):
        super()._create_state(config)

        self._attr_is_closed = config.get(CONF_INITIAL_VALUE).lower() == STATE_CLOSED
        if self._attr_is_closed:
            self._attr_current_cover_position = 0
        else:
            self._attr_current_cover_position = 100

    def _restore_state(self, state, config):
        super()._restore_state(state, config)

        self._attr_is_closed = state.state.lower() == STATE_CLOSED

    def _update_attributes(self):
        super()._update_attributes();
        self._attr_extra_state_attributes.update({
            name: value for name, value in (
                (ATTR_DEVICE_CLASS, self._attr_device_class),
            ) if value is not None
        })

    def open_cover(self, **kwargs: Any) -> None:
        _LOGGER.info(f"opening {self.name}")
        self._attr_is_opening = True
        self._attr_is_closing = False
        self._target_cover_position = 100
        self._tick()

    def close_cover(self, **kwargs: Any) -> None:
        _LOGGER.info(f"closing {self.name}")
        self._attr_is_opening = False
        self._attr_is_closing = True
        self._target_cover_position = 0
        self._tick()

    def stop_cover(self, **kwargs: Any) -> None:
        _LOGGER.info(f"stopping {self.name}")
        self._virtual_operation_started = None
        self._target_cover_position = None
        self._attr_is_opening = False
        self._attr_is_closing = False

        if self._attr_current_cover_position > 0:
            self._attr_is_closed = False
        else:
            self._attr_is_closed = True
            
        self.schedule_update_ha_state()
        
    def set_cover_position(self, **kwargs: Any) -> None:
        _LOGGER.info(f"setting {self.name} position {kwargs['position']}")
        self._target_cover_position = kwargs['position']
        if self._target_cover_position == self._attr_current_cover_position:
            return
        elif self._target_cover_position < self._attr_current_cover_position:
            self.close_cover()
        elif self._target_cover_position > self._attr_current_cover_position:
            self.open_cover()

    async def _update_cover_position(self, *args: Any) -> None:
        if self._target_cover_position is not None:
            if self._attr_is_closing and self._attr_current_cover_position <= self._target_cover_position :
                self.stop_cover()
            elif self._attr_is_opening and self._attr_current_cover_position >= self._target_cover_position:
                self.stop_cover()

        if self._virtual_operation_started is None:
            return
        
        running_time_delta = datetime.now() - self._virtual_operation_started
        percent_moved = int((running_time_delta.total_seconds() / self._virtual_duration)*100)

        if self._attr_is_closing:
            self._attr_current_cover_position = max(0, self._attr_current_cover_position - percent_moved)
        elif self._attr_is_opening:
            self._attr_current_cover_position = min(100, self._attr_current_cover_position + percent_moved)

        self.async_write_ha_state()
        self._tick()

    def _tick(self):
        self._virtual_operation_started = datetime.now()
        async_call_later(self.hass, self._virtual_tick, self._update_cover_position)
