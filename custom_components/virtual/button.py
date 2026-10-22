"""This component provides support for a virtual button."""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    DOMAIN as PLATFORM_DOMAIN,
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
    CONF_CLASS,
    CONF_YAML_CONFIG,
)
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_BUTTON_VALUE = ""

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_BUTTON_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
}))
BUTTON_SCHEMA = vol.Schema(virtual_schema(DEFAULT_BUTTON_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
}))


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")

        buttons = [VirtualButton(config, True)]
        async_add_entities(buttons, True)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the entries...")

    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = BUTTON_SCHEMA(entity)
        entities.append(VirtualButton(entity, False))
    async_add_entities(entities)


class VirtualButton(VirtualEntity, ButtonEntity):
    """Representation of a Virtual button."""

    def __init__(self, config: dict[str, Any], old_style: bool):
        """Initialize the Virtual button device."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_device_class = config.get(CONF_CLASS)
        _LOGGER.info(f"VirtualButton: {self.name} created")

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info(f"VirtualButton: {self.name} pressed")
        self.hass.bus.async_fire("virtual_button_pressed", {
            "entity_id": self.entity_id,
            "name": self.name,
        })
