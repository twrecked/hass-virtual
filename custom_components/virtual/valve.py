"""
This component provides support for a virtual valve.

"""

import logging
import voluptuous as vol
from typing import Any
from collections.abc import Callable

import homeassistant.helpers.config_validation as cv
from homeassistant.components.valve import (
    ValveEntity,
    ValveEntityFeature,
    DOMAIN as PLATFORM_DOMAIN
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA

from . import get_entity_configs
from .const import *
from .entity import (
    VirtualOpenableEntity,
    virtual_schema,
)


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_VALVE_VALUE = "open"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_VALVE_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_OPEN_CLOSE_DURATION, default=10): cv.positive_int,
    vol.Optional(CONF_OPEN_CLOSE_TICK, default=1): cv.positive_int,
}))
VALVE_SCHEMA = vol.Schema(virtual_schema(DEFAULT_VALVE_VALUE, {
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
        entity = VALVE_SCHEMA(entity)
        entities.append(VirtualValve(entity))
    async_add_entities(entities)


class VirtualValve(VirtualOpenableEntity, ValveEntity):

    def __init__(self, config):
        """Initialize the Virtual valve device."""
        super().__init__(config, PLATFORM_DOMAIN)

        self._attr_supported_features = ValveEntityFeature(
            ValveEntityFeature.OPEN |
            ValveEntityFeature.CLOSE |
            ValveEntityFeature.STOP |
            ValveEntityFeature.SET_POSITION
        )
        self._attr_reports_position = True

        _LOGGER.info(f"VirtualValve: {self.name} created")

    @property
    def current_valve_position(self) -> int | None:
        return self._current_position

    def open_valve(self, **kwargs: Any) -> None:
        _LOGGER.info(f"opening {self.name}")
        self._set_position(100)

    def close_valve(self, **kwargs: Any) -> None:
        _LOGGER.info(f"closing {self.name}")
        self._set_position(0)

    def stop_valve(self, **kwargs: Any) -> None:
        _LOGGER.info(f"stopping {self.name}")
        self._stop()

    def set_valve_position(self, position: int) -> None:
        _LOGGER.info(f"setting {self.name} position {position}")
        self._set_position(position)
