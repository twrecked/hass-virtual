"""
This component provides support for a virtual light.

"""
from __future__ import annotations

import logging
import pprint
import voluptuous as vol
from collections.abc import Callable
from typing import Any

import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP,
    ATTR_EFFECT,
    ATTR_EFFECT_LIST,
    ATTR_HS_COLOR,
    ColorMode,
    DOMAIN as PLATFORM_DOMAIN,
    LightEntity,
    LightEntityFeature,
    SUPPORT_EFFECT,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import get_entity_configs
from .const import *
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

CONF_SUPPORT_BRIGHTNESS = "support_brightness"
CONF_INITIAL_BRIGHTNESS = "initial_brightness"
CONF_SUPPORT_COLOR = "support_color"
CONF_INITIAL_COLOR = "initial_color"
CONF_SUPPORT_COLOR_TEMP = "support_color_temp"
CONF_INITIAL_COLOR_TEMP = "initial_color_temp"
CONF_SUPPORT_WHITE_VALUE = "support_white_value"
CONF_INITIAL_WHITE_VALUE = "initial_white_value"
CONF_SUPPORT_EFFECT = "support_effect"
CONF_INITIAL_EFFECT = "initial_effect"
CONF_INITIAL_EFFECT_LIST = "initial_effect_list"

DEFAULT_LIGHT_VALUE = "on"
DEFAULT_SUPPORT_BRIGHTNESS = True
DEFAULT_INITIAL_BRIGHTNESS = 255
DEFAULT_SUPPORT_COLOR = False
DEFAULT_INITIAL_COLOR = [0, 100]
DEFAULT_SUPPORT_COLOR_TEMP = False
DEFAULT_INITIAL_COLOR_TEMP = 240
DEFAULT_SUPPORT_WHITE_VALUE = False
DEFAULT_INITIAL_WHITE_VALUE = 240
DEFAULT_SUPPORT_EFFECT = False
DEFAULT_INITIAL_EFFECT = "none"
DEFAULT_INITIAL_EFFECT_LIST = ["rainbow", "none"]

BASE_SCHEMA = virtual_schema(DEFAULT_LIGHT_VALUE, {
    vol.Optional(CONF_SUPPORT_BRIGHTNESS, default=DEFAULT_SUPPORT_BRIGHTNESS): cv.boolean,
    vol.Optional(CONF_INITIAL_BRIGHTNESS, default=DEFAULT_INITIAL_BRIGHTNESS): cv.byte,
    vol.Optional(CONF_SUPPORT_COLOR, default=DEFAULT_SUPPORT_COLOR): cv.boolean,
    vol.Optional(CONF_INITIAL_COLOR, default=DEFAULT_INITIAL_COLOR): cv.ensure_list,
    vol.Optional(CONF_SUPPORT_COLOR_TEMP, default=DEFAULT_SUPPORT_COLOR_TEMP): cv.boolean,
    vol.Optional(CONF_INITIAL_COLOR_TEMP, default=DEFAULT_INITIAL_COLOR_TEMP): cv.byte,
    vol.Optional(CONF_SUPPORT_WHITE_VALUE, default=DEFAULT_SUPPORT_WHITE_VALUE): cv.boolean,
    vol.Optional(CONF_INITIAL_WHITE_VALUE, default=DEFAULT_INITIAL_WHITE_VALUE): cv.byte,
    vol.Optional(CONF_SUPPORT_EFFECT, default=DEFAULT_SUPPORT_EFFECT): cv.boolean,
    vol.Optional(CONF_INITIAL_EFFECT, default=DEFAULT_INITIAL_EFFECT): cv.string,
    vol.Optional(CONF_INITIAL_EFFECT_LIST, default=DEFAULT_INITIAL_EFFECT_LIST): cv.ensure_list
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(BASE_SCHEMA)

LIGHT_SCHEMA = vol.Schema(BASE_SCHEMA)


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")

        lights = [VirtualLight(config, True)]
        async_add_entities(lights, True)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the entries...")

    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = LIGHT_SCHEMA(entity)
        entities.append(VirtualLight(entity, False))
    async_add_entities(entities)


class VirtualLight(VirtualEntity, LightEntity):

    def __init__(self, config, old_style: bool):
        """Initialize a Virtual light."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_supported_features = LightEntityFeature(0)
        self._attr_supported_color_modes = set()
        self._attr_color_mode = ColorMode.UNKNOWN

        if config.get(CONF_SUPPORT_COLOR_TEMP):
            self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)
        if config.get(CONF_SUPPORT_COLOR):
            self._attr_supported_color_modes.add(ColorMode.HS)
        if config.get(CONF_SUPPORT_BRIGHTNESS):
            if not self._attr_supported_color_modes:
                self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)
        if not self._attr_supported_color_modes:
            self._attr_supported_color_modes.add(ColorMode.ONOFF)

        if config.get(CONF_SUPPORT_EFFECT):
            self._attr_supported_features |= SUPPORT_EFFECT
            self._attr_effect_list = self._config.get(CONF_INITIAL_EFFECT_LIST)

    def _create_state(self, config):
        super()._create_state(config)

        self._attr_is_on = config.get(CONF_INITIAL_VALUE).lower() == STATE_ON

        if ColorMode.BRIGHTNESS in self._attr_supported_color_modes:
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_brightness = config.get(CONF_INITIAL_BRIGHTNESS)
        if ColorMode.HS in self._attr_supported_color_modes:
            self._attr_color_mode = ColorMode.HS
            self._attr_hs_color = config.get(CONF_INITIAL_COLOR)
            self._attr_brightness = config.get(CONF_INITIAL_BRIGHTNESS)
        if ColorMode.COLOR_TEMP in self._attr_supported_color_modes:
            self._attr_color_mode = ColorMode.COLOR_TEMP
            self._attr_color_temp = config.get(CONF_INITIAL_COLOR_TEMP)
            self._attr_brightness = config.get(CONF_INITIAL_BRIGHTNESS)
        if self._attr_supported_features & SUPPORT_EFFECT:
            self._attr_effect = config.get(CONF_INITIAL_EFFECT)

    def _restore_state(self, state, config):
        super()._restore_state(state, config)

        self._attr_is_on = state.state.lower() == STATE_ON

        self._attr_color_mode = state.attributes.get(ATTR_COLOR_MODE, ColorMode.ONOFF)
        if self._attr_color_mode == ColorMode.BRIGHTNESS:
            self._attr_brightness = state.attributes.get(ATTR_BRIGHTNESS, config.get(CONF_INITIAL_BRIGHTNESS))
        if self._attr_color_mode == ColorMode.HS:
            self._attr_hs_color = state.attributes.get(ATTR_HS_COLOR, config.get(CONF_INITIAL_COLOR))
            self._attr_brightness = state.attributes.get(ATTR_BRIGHTNESS, config.get(CONF_INITIAL_BRIGHTNESS))
        if self._attr_color_mode == ColorMode.COLOR_TEMP:
            self._attr_color_temp = state.attributes.get(ATTR_COLOR_TEMP, config.get(CONF_INITIAL_COLOR_TEMP))
            self._attr_brightness = state.attributes.get(ATTR_BRIGHTNESS, config.get(CONF_INITIAL_BRIGHTNESS))
        if self._attr_supported_features & SUPPORT_EFFECT:
            self._attr_effect = state.attributes.get(ATTR_EFFECT, config.get(CONF_INITIAL_EFFECT))

    def _update_attributes(self):
        """Return the state attributes."""
        super()._update_attributes()
        self._attr_extra_state_attributes.update({
            name: value for name, value in (
                (ATTR_BRIGHTNESS, self._attr_brightness),
                (ATTR_COLOR_MODE, self._attr_color_mode),
                (ATTR_COLOR_TEMP, self._attr_color_temp),
                (ATTR_EFFECT, self._attr_effect),
                (ATTR_EFFECT_LIST, self._attr_effect_list),
                (ATTR_HS_COLOR, self._attr_hs_color),
            ) if value is not None
        })

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        _LOGGER.debug(f"turning {self.name} on {pprint.pformat(kwargs)}")
        hs_color = kwargs.get(ATTR_HS_COLOR, None)

        if hs_color is not None and ColorMode.HS in self._attr_supported_color_modes:
            self._attr_color_mode = ColorMode.HS
            self._attr_hs_color = hs_color
            self._attr_color_temp = None

        ct = kwargs.get(ATTR_COLOR_TEMP, None)
        if ct is not None and ColorMode.COLOR_TEMP in self._attr_supported_color_modes:
            self._attr_color_mode = ColorMode.COLOR_TEMP
            self._attr_color_temp = ct
            self._attr_hs_color = None

        brightness = kwargs.get(ATTR_BRIGHTNESS, None)
        if brightness is not None:
            if self._attr_color_mode == ColorMode.UNKNOWN:
                self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_brightness = brightness

        if self._attr_color_mode == ColorMode.UNKNOWN:
            self._attr_color_mode = ColorMode.ONOFF

        effect = kwargs.get(ATTR_EFFECT, None)
        if effect is not None and self._attr_supported_features & SUPPORT_EFFECT:
            self._attr_effect = effect

        self._attr_is_on = True
        self._update_attributes()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        _LOGGER.debug(f"turning {self.name} off {pprint.pformat(kwargs)}")
        self._attr_is_on = False
        self._update_attributes()
