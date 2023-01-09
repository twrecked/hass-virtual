"""
This component provides support for a virtual light.

"""
from __future__ import annotations

import logging
import pprint

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_HS_COLOR,
    ATTR_EFFECT,
    DOMAIN,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    SUPPORT_COLOR_TEMP,
    SUPPORT_EFFECT,
    LightEntity,
    ColorMode,
)
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA)
from .const import (
    COMPONENT_DOMAIN,
    CONF_INITIAL_AVAILABILITY,
    CONF_INITIAL_VALUE,
    CONF_NAME,
    CONF_PERSISTENT,
    DEFAULT_INITIAL_AVAILABILITY,
    DEFAULT_PERSISTENT,
)
from .entity import VirtualEntity

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

DEFAULT_INITIAL_VALUE = "on"
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

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_INITIAL_VALUE, default=DEFAULT_INITIAL_VALUE): cv.string,
    vol.Optional(CONF_INITIAL_AVAILABILITY, default=DEFAULT_INITIAL_AVAILABILITY): cv.boolean,
    vol.Optional(CONF_PERSISTENT, default=DEFAULT_PERSISTENT): cv.boolean,

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


async def async_setup_platform(_hass, config, async_add_entities, _discovery_info=None):
    lights = [VirtualLight(config)]
    async_add_entities(lights, True)


class VirtualLight(VirtualEntity, LightEntity):

    def __init__(self, config):
        """Initialize a Virtual light."""
        super().__init__(config, DOMAIN)

        self._attr_supported_color_modes = {ColorMode.ONOFF}
        self._attr_supported_features = 0

        if config.get(CONF_SUPPORT_BRIGHTNESS):
            self._attr_supported_features |= SUPPORT_BRIGHTNESS
            self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)
        if config.get(CONF_SUPPORT_COLOR):
            self._attr_supported_features |= SUPPORT_COLOR
            self._attr_color_mode = ColorMode.HS
            self._attr_supported_color_modes.add(ColorMode.HS)
        if config.get(CONF_SUPPORT_COLOR_TEMP):
            self._attr_supported_features |= SUPPORT_COLOR_TEMP
            self._attr_color_mode = ColorMode.COLOR_TEMP
            self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)
        if config.get(CONF_SUPPORT_EFFECT):
            self._attr_supported_features |= SUPPORT_EFFECT
            self._attr_effect_list = self._config.get(CONF_INITIAL_EFFECT_LIST)

    def _create_state(self, config):
        super()._create_state(config)

        self._attr_is_on = config.get(CONF_INITIAL_VALUE, "off").lower() == "on"

        if self._attr_supported_features & SUPPORT_BRIGHTNESS:
            self._attr_brightness = config.get(CONF_INITIAL_BRIGHTNESS)
        if self._attr_supported_features & SUPPORT_COLOR:
            self._attr_hs_color = config.get(CONF_INITIAL_COLOR)
        if self._attr_supported_features & SUPPORT_COLOR_TEMP:
            self._attr_color_temp = config.get(CONF_INITIAL_COLOR_TEMP)
        if self._attr_supported_features & SUPPORT_EFFECT:
            self._attr_effect = config.get(CONF_INITIAL_EFFECT)
        self._update_attributes()

    def _restore_state(self, state, config):
        super()._restore_state(state, config)

        self._attr_is_on = state.state.lower() == "on"

        if self._attr_supported_features & SUPPORT_BRIGHTNESS:
            self._attr_brightness = state.attributes.get('brightness', config.get(CONF_INITIAL_BRIGHTNESS))
        if self._attr_supported_features & SUPPORT_COLOR:
            self._attr_hs_color = state.attributes.get('hs_color', config.get(CONF_INITIAL_COLOR))
        if self._attr_supported_features & SUPPORT_COLOR_TEMP:
            self._attr_color_temp = state.attributes.get('color_temp', config.get(CONF_INITIAL_COLOR_TEMP))
        if self._attr_supported_features & SUPPORT_EFFECT:
            self._attr_effect = state.attributes.get('effect', config.get(CONF_INITIAL_EFFECT))
        self._update_attributes()

    def _update_attributes(self):
        """Return the state attributes."""
        self._attr_extra_state_attributes = self._add_virtual_attributes({
            name: value for name, value in (
                ('brightness', self._attr_brightness),
                ('color_mode', self._attr_color_mode),
                ('color_temp', self._attr_color_temp),
                ('effect', self._attr_effect),
                ('effect_list', self._attr_effect_list),
                ('hs_color', self._attr_hs_color),
            ) if value is not None
        })

    def turn_on(self, **kwargs):
        """Turn the light on."""
        hs_color = kwargs.get(ATTR_HS_COLOR, None)
        if hs_color is not None and self._attr_supported_features & SUPPORT_COLOR:
            self._attr_color_mode = ColorMode.HS
            self._attr_hs_color = hs_color
            self._attr_color_temp = None

        ct = kwargs.get(ATTR_COLOR_TEMP, None)
        if ct is not None and self._attr_supported_features & SUPPORT_COLOR_TEMP:
            self._attr_color_mode = ColorMode.COLOR_TEMP
            self._attr_color_temp = ct
            self._attr_hs_color = None

        brightness = kwargs.get(ATTR_BRIGHTNESS, None)
        if brightness is not None:
            self._attr_brightness = brightness

        effect = kwargs.get(ATTR_EFFECT, None)
        if effect is not None and self._attr_supported_features & SUPPORT_EFFECT:
            self._attr_effect = effect

        _LOGGER.info("turn_on: {}".format(pprint.pformat(kwargs)))
        self._attr_is_on = True
        self._update_attributes()

    def turn_off(self, **kwargs):
        """Turn the light off."""
        _LOGGER.info("turn_off: {}".format(pprint.pformat(kwargs)))
        self._attr_is_on = False
        self._update_attributes()

    # @property
    # def extra_state_attributes(self):
    #     """Return the state attributes."""
    #     return self._add_virtual_attributes({
    #         name: value for name, value in (
    #             ('brightness', self._attr_brightness),
    #             ('color_mode', self._attr_color_mode),
    #             ('color_temp', self._attr_color_temp),
    #             ('effect', self._attr_effect),
    #             ('effect_list', self._attr_effect_list),
    #             ('hs_color', self._attr_hs_color),
    #         ) if value is not None
    #     })
