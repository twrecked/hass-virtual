"""
This component provides support for a virtual cover.

"""

import logging
import voluptuous as vol
from typing import Any
from collections.abc import Callable

import homeassistant.helpers.config_validation as cv
from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
    DOMAIN as PLATFORM_DOMAIN
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA

from . import get_entity_configs
from .const import *
from .entity import (
    VirtualOpenableEntity,
    virtual_schema
)


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


async def async_setup_platform(hass, config, async_add_entities, _discovery_info=None):
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")

        sensors = [VirtualCover(config, True)]
        async_add_entities(sensors, True)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the entries...")

    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = COVER_SCHEMA(entity)
        entities.append(VirtualCover(entity, False))
    async_add_entities(entities)


class VirtualCover(VirtualOpenableEntity, CoverEntity):
    """Representation of a Virtual cover."""

    def __init__(self, config, old_style : bool):
        """Initialize the Virtual cover device."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_supported_features = CoverEntityFeature(
            CoverEntityFeature.OPEN |
            CoverEntityFeature.CLOSE |
            CoverEntityFeature.STOP |
            CoverEntityFeature.SET_POSITION
        )

        _LOGGER.info(f"VirtualCover: {self.name} created")

    @property
    def current_cover_position(self) -> int | None:
        return self._current_position

    async def async_open_cover(self, **kwargs: Any) -> None:
        _LOGGER.info(f"opening {self.name}")
        self._set_position(100)

    async def async_close_cover(self, **kwargs: Any) -> None:
        _LOGGER.info(f"closing {self.name}")
        self._set_position(0)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        _LOGGER.info(f"stopping {self.name}")
        self._stop()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        _LOGGER.info(f"setting {self.name} position {kwargs['position']}")
        self._set_position(kwargs['position'])
