"""This component provides support for a virtual select entity."""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.select import (
    DOMAIN as PLATFORM_DOMAIN,
    SelectEntity,
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
    CONF_OPTIONS,
    CONF_YAML_CONFIG,
)
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_SELECT_VALUE = ""

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_SELECT_VALUE, {
    vol.Required(CONF_OPTIONS, default=[]): vol.All(cv.ensure_list, [cv.string]),
}))
SELECT_SCHEMA = vol.Schema(virtual_schema(DEFAULT_SELECT_VALUE, {
    vol.Required(CONF_OPTIONS, default=[]): vol.All(cv.ensure_list, [cv.string]),
}))


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")

        selects = [VirtualSelect(config, True)]
        async_add_entities(selects, True)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the entries...")

    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = SELECT_SCHEMA(entity)
        entities.append(VirtualSelect(entity, False))
    async_add_entities(entities)


class VirtualSelect(VirtualEntity, SelectEntity):
    """Representation of a Virtual select."""

    def __init__(self, config: dict[str, Any], old_style: bool):
        """Initialize the Virtual select device."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_options = [str(opt) for opt in config.get(CONF_OPTIONS, [])]
        _LOGGER.info(f"VirtualSelect: {self.name} created with options {self._attr_options}")

    def _create_state(self, config: dict[str, Any]):
        super()._create_state(config)

        initial = config.get(CONF_INITIAL_VALUE)
        if initial and str(initial) in self._attr_options:
            self._attr_current_option = str(initial)
        elif self._attr_options:
            self._attr_current_option = self._attr_options[0]
        else:
            self._attr_current_option = None

    def _restore_state(self, state, config: dict[str, Any]):
        super()._restore_state(state, config)

        if state.state in self._attr_options:
            self._attr_current_option = state.state
        else:
            self._create_state(config)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        _LOGGER.debug(f"setting {self.name} option to {option}")
        self._attr_current_option = option
        self._update_attributes()
        self.async_write_ha_state()
