"""
This component provides support for a virtual light.

"""

import logging
import pprint

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    SUPPORT_BRIGHTNESS,
    Light,
)
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA)
from . import COMPONENT_DOMAIN, COMPONENT_SERVICES


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

CONF_NAME = "name"
CONF_INITIAL_VALUE = "initial_value"
CONF_INITIAL_BRIGHTNESS = "initial_brightness"

DEFAULT_INITIAL_VALUE = "off"
DEFAULT_INITIAL_BRIGHTNESS = "100"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_INITIAL_VALUE, default=DEFAULT_INITIAL_VALUE): cv.string,
    vol.Optional(CONF_INITIAL_BRIGHTNESS, default=DEFAULT_INITIAL_BRIGHTNESS): cv.string,
})


async def async_setup_platform(hass, config, async_add_entities, _discovery_info=None):
    lights = [VirtualLight(config)]
    async_add_entities(lights, True)


class VirtualLight(Light):

    def __init__(self, config):
        """Initialize an Virtual light."""
        self._name = config.get(CONF_NAME)
        self._unique_id = self._name.lower().replace(' ', '_')
        self._state = config.get(CONF_INITIAL_VALUE)
        self._brightness = config.get(CONF_INITIAL_BRIGHTNESS)
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
        return SUPPORT_BRIGHTNESS 

    def turn_on(self, **kwargs):
        """Turn the light on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS,None)
        if brightness is not None:
            self._brightness = brightness

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
    def device_state_attributes(self):
        """Return the state attributes."""

        attrs = {
            name: value for name, value in (
                ('friendly_name', self._name),
                ('brightness', self._brightness),
            ) if value is not None
        }

        return attrs

