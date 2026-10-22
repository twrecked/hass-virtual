"""This component provides support for a virtual text entity."""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.text import (
    DOMAIN as PLATFORM_DOMAIN,
    TextEntity,
    TextMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import get_entity_configs
from .const import (
    ATTR_GROUP_NAME,
    COMPONENT_CONFIG,
    COMPONENT_DOMAIN,
    CONF_INITIAL_VALUE,
    CONF_MAX,
    CONF_MIN,
    CONF_MODE,
    CONF_PATTERN,
    CONF_YAML_CONFIG,
)
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_TEXT_VALUE = ""

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_TEXT_VALUE, {
    vol.Optional(CONF_MIN, default=0): cv.positive_int,
    vol.Optional(CONF_MAX, default=255): cv.positive_int,
    vol.Optional(CONF_MODE, default="text"): vol.In(["text", "password"]),
    vol.Optional(CONF_PATTERN): cv.string,
}))
TEXT_SCHEMA = vol.Schema(virtual_schema(DEFAULT_TEXT_VALUE, {
    vol.Optional(CONF_MIN, default=0): cv.positive_int,
    vol.Optional(CONF_MAX, default=255): cv.positive_int,
    vol.Optional(CONF_MODE, default="text"): vol.In(["text", "password"]),
    vol.Optional(CONF_PATTERN): cv.string,
}))


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")

        texts = [VirtualText(config, True)]
        async_add_entities(texts, True)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the entries...")

    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = TEXT_SCHEMA(entity)
        entities.append(VirtualText(entity, False))
    async_add_entities(entities)


class VirtualText(VirtualEntity, TextEntity):
    """Representation of a Virtual text."""

    def __init__(self, config: dict[str, Any], old_style: bool):
        """Initialize the Virtual text device."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_native_min = int(config.get(CONF_MIN, 0))
        self._attr_native_max = int(config.get(CONF_MAX, 255))
        self._attr_pattern = config.get(CONF_PATTERN)

        mode_str = config.get(CONF_MODE, "text")
        self._attr_mode = TextMode.PASSWORD if mode_str == "password" else TextMode.TEXT

        _LOGGER.info(f"VirtualText: {self.name} created")

    def _create_state(self, config: dict[str, Any]):
        super()._create_state(config)
        self._attr_native_value = str(config.get(CONF_INITIAL_VALUE, DEFAULT_TEXT_VALUE))

    def _restore_state(self, state, config: dict[str, Any]):
        super()._restore_state(state, config)
        self._attr_native_value = state.state if state.state is not None else str(config.get(CONF_INITIAL_VALUE, DEFAULT_TEXT_VALUE))

    async def async_set_value(self, value: str) -> None:
        """Change the value."""
        _LOGGER.debug(f"setting {self.name} value to {value}")
        self._attr_native_value = value
        self._update_attributes()
        self.async_write_ha_state()
