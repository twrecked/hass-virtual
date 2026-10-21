"""
This component provides support for a virtual switch.

"""

import logging
import voluptuous as vol
from collections.abc import Callable
from typing import Any

import homeassistant.helpers.config_validation as cv
from homeassistant.components.switch import (
    DOMAIN as PLATFORM_DOMAIN,
    SwitchEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import get_entity_configs
from .const import *
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_SWITCH_VALUE = "off"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_SWITCH_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
}))
SWITCH_SCHEMA = vol.Schema(virtual_schema(DEFAULT_SWITCH_VALUE, {
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

        switches = [VirtualSwitch(config, True)]
        async_add_entities(switches, True)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the entries...")

    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = SWITCH_SCHEMA(entity)
        entities.append(VirtualSwitch(entity, False))
    async_add_entities(entities)


class VirtualSwitch(VirtualEntity, SwitchEntity):
    """Representation of a Virtual switch."""

    def __init__(self, config, old_style : bool):
        """Initialize the Virtual switch device."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_device_class = config.get(CONF_CLASS)

        _LOGGER.info(f"VirtualSwitch: {self.name} created")

    def _create_state(self, config):
        super()._create_state(config)

        self._attr_is_on = config.get(CONF_INITIAL_VALUE, DEFAULT_SWITCH_VALUE).lower() == STATE_ON

    def _restore_state(self, state, config):
        super()._restore_state(state, config)

        if state.state and state.state.lower() in (STATE_ON, STATE_OFF):
            self._attr_is_on = state.state.lower() == STATE_ON
        else:
            self._attr_is_on = config.get(CONF_INITIAL_VALUE, DEFAULT_SWITCH_VALUE).lower() == STATE_ON

    async def async_turn_on(self, **kwargs: Any) -> None:
        _LOGGER.debug(f"turning {self.name} on")
        self._attr_is_on = True
        self._update_attributes()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        _LOGGER.debug(f"turning {self.name} off")
        self._attr_is_on = False
        self._update_attributes()
        self.async_write_ha_state()
