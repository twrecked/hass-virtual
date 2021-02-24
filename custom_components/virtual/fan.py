"""
This component provides support for a virtual fan.

Borrowed heavily from components/demo/fan.py
"""

import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.fan import (
    SPEED_HIGH,
    SPEED_LOW,
    SPEED_MEDIUM,
    SUPPORT_DIRECTION,
    SUPPORT_OSCILLATE,
    SUPPORT_SET_SPEED,
    FanEntity,
)
from homeassistant.const import STATE_OFF
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA)

_LOGGER = logging.getLogger(__name__)

CONF_NAME = "name"
CONF_SPEED = "speed"
CONF_OSCILLATE = "oscillate"
CONF_DIRECTION = "direction"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_SPEED, default=False): cv.boolean,
    vol.Optional(CONF_OSCILLATE, default=False): cv.boolean,
    vol.Optional(CONF_DIRECTION, default=False): cv.boolean,
})


async def async_setup_platform(_hass, config, async_add_entities, _discovery_info=None):
    """Set up the Demo config entry."""
    fans = [VirtualFan(config)]
    async_add_entities(fans, True)


class VirtualFan(FanEntity):
    """A demonstration fan component."""

    def __init__(self, config):
        """Initialize the entity."""
        self._name = config.get(CONF_NAME)
        self._unique_id = self._name.lower().replace(' ', '_')

        self._speed = STATE_OFF
        self._supported_features = 0
        self._oscillating = None
        self._direction = None
        if config.get(CONF_SPEED, False):
            self._supported_features |= SUPPORT_SET_SPEED
        if config.get(CONF_OSCILLATE, False):
            self._supported_features |= SUPPORT_OSCILLATE
            self._oscillating = False
        if config.get(CONF_DIRECTION, False):
            self._supported_features |= SUPPORT_DIRECTION
            self._direction = "forward"

        _LOGGER.info('VirtualFan: {} created'.format(self._name))

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Get entity name."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed for a demo fan."""
        return False

    @property
    def speed(self) -> str:
        """Return the current speed."""
        return self._speed

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return [STATE_OFF, SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]

    def turn_on(self, speed: str = None, **kwargs) -> None:
        """Turn on the entity."""
        if speed is None:
            speed = SPEED_MEDIUM
        self.set_speed(speed)

    def turn_off(self, **kwargs) -> None:
        """Turn off the entity."""
        self.oscillate(False)
        self.set_speed(STATE_OFF)

    def set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        self._speed = speed
        self.schedule_update_ha_state()

    def set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""
        self._direction = direction
        self.schedule_update_ha_state()

    def oscillate(self, oscillating: bool) -> None:
        """Set oscillation."""
        self._oscillating = oscillating
        self.schedule_update_ha_state()

    @property
    def current_direction(self) -> str:
        """Fan direction."""
        return self._direction

    @property
    def oscillating(self) -> bool:
        """Oscillating."""
        return self._oscillating

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return self._supported_features
