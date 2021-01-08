"""
This component provides support for a virtual light.

"""

import logging
import pprint

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_HS_COLOR,
    ATTR_WHITE_VALUE,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    SUPPORT_COLOR_TEMP,
    SUPPORT_WHITE_VALUE,
    LightEntity,
)
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA)
from . import COMPONENT_DOMAIN

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

CONF_NAME = "name"
CONF_INITIAL_VALUE = "initial_value"
CONF_INITIAL_BRIGHTNESS = "initial_brightness"
CONF_SUPPORT_COLOR = "support_color"
CONF_INITIAL_COLOR = "initial_color"
CONF_SUPPORT_COLOR_TEMP = "support_color_temp"
CONF_INITIAL_COLOR_TEMP = "initial_color_temp"
CONF_SUPPORT_WHITE_VALUE = "support_white_value"
CONF_INITIAL_WHITE_VALUE = "initial_white_value"

DEFAULT_INITIAL_VALUE = "on"
DEFAULT_INITIAL_BRIGHTNESS = 255
DEFAULT_SUPPORT_COLOR = False
DEFAULT_INITIAL_COLOR = [0,100]
DEFAULT_SUPPORT_COLOR_TEMP = False
DEFAULT_INITIAL_COLOR_TEMP = 240
DEFAULT_SUPPORT_WHITE_VALUE = False
DEFAULT_INITIAL_WHITE_VALUE = 240

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_INITIAL_VALUE, default=DEFAULT_INITIAL_VALUE): cv.string,
    vol.Optional(CONF_INITIAL_BRIGHTNESS, default=DEFAULT_INITIAL_BRIGHTNESS): cv.byte,
    vol.Optional(CONF_SUPPORT_COLOR, default=DEFAULT_SUPPORT_COLOR): cv.boolean,
    vol.Optional(CONF_INITIAL_COLOR, default=DEFAULT_INITIAL_COLOR): cv.ensure_list,
    vol.Optional(CONF_SUPPORT_COLOR_TEMP, default=DEFAULT_SUPPORT_COLOR_TEMP): cv.boolean,
    vol.Optional(CONF_INITIAL_COLOR_TEMP, default=DEFAULT_INITIAL_COLOR_TEMP): cv.byte,
    vol.Optional(CONF_SUPPORT_WHITE_VALUE, default=DEFAULT_SUPPORT_WHITE_VALUE): cv.boolean,
    vol.Optional(CONF_INITIAL_WHITE_VALUE, default=DEFAULT_INITIAL_WHITE_VALUE): cv.byte,
})


async def async_setup_platform(_hass, config, async_add_entities, _discovery_info=None):
    lights = [VirtualLight(config)]
    async_add_entities(lights, True)


class VirtualLight(LightEntity):

    def __init__(self, config):
        """Initialize an Virtual light."""
        self._name = config.get(CONF_NAME)
        self._unique_id = self._name.lower().replace(' ', '_')
        self._state = config.get(CONF_INITIAL_VALUE)
        self._brightness = config.get(CONF_INITIAL_BRIGHTNESS)
        self._features = SUPPORT_BRIGHTNESS

        self._hs_color = None
        self._ct = None
        self._white =  None
        self._color_mode = None
        if config.get(CONF_SUPPORT_COLOR):
            self._features |= SUPPORT_COLOR
            self._hs_color = config.get(CONF_INITIAL_COLOR)
            self._color_mode = "hs"
        if config.get(CONF_SUPPORT_COLOR_TEMP):
            self._features |= SUPPORT_COLOR_TEMP
            self._ct = config.get(CONF_INITIAL_COLOR_TEMP)
            self._color_mode = "ct"
        if config.get(CONF_SUPPORT_WHITE_VALUE):
            self._features |= SUPPORT_WHITE_VALUE
            self._white =  config.get(CONF_INITIAL_WHITE_VALUE)
        _LOGGER.info('VirtualLight: %s created', self._name)

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def is_on(self) -> bool:
        """Return True if light is on."""
        return self._state.lower() == "on"

    @property
    def supported_features(self):
        """Flag features that are supported."""
        return self._features

    def turn_on(self, **kwargs):
        """Turn the light on."""
        hs_color = kwargs.get(ATTR_HS_COLOR, None)
        if hs_color is not None and self._features & SUPPORT_COLOR:
            self._color_mode = "hs"
            self._hs_color = hs_color
            self._ct = None
            
        ct = kwargs.get(ATTR_COLOR_TEMP, None)
        if ct is not None and self._features & SUPPORT_COLOR_TEMP:
            self._color_mode = "ct"
            self._ct = ct
            self._hs_color = None

        brightness = kwargs.get(ATTR_BRIGHTNESS, None)
        if brightness is not None:
            self._brightness = brightness

        white = kwargs.get(ATTR_WHITE_VALUE, None)
        if white is not None and self._features & SUPPORT_WHITE_VALUE:
            self._white = white

        _LOGGER.info("turn_on: {}".format(pprint.pformat(kwargs)))
        self._state = "on"

    def turn_off(self, **kwargs):
        """Turn the light off."""
        _LOGGER.info("turn_off: {}".format(pprint.pformat(kwargs)))
        self._state = "off"

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._brightness

    @property
    def hs_color(self) -> tuple:
        """Return the hs color value."""
        if self._color_mode == "hs":
            return self._hs_color
        return None

    @property
    def color_temp(self) -> int:
        """Return the CT color temperature."""
        if self._color_mode == "ct":
            return self._ct
        return None

    @property
    def white_value(self) -> int:
        """Return the white value of this light between 0..255."""
        return self._white

    @property
    def device_state_attributes(self):
        """Return the state attributes."""

        attrs = {
            name: value for name, value in (
                ('friendly_name', self._name),
                ('brightness', self._brightness),
                ('hs_color', self._hs_color),
                ('white_value', self._white),
                ('color_temp', self._ct),
                ('color_mode', self._color_mode),
            ) if value is not None
        }

        return attrs
