"""
This component provides support for a virtual fan.

Borrowed heavily from components/demo/fan.py
"""

from __future__ import annotations

import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.fan import (
    ATTR_DIRECTION,
    ATTR_OSCILLATING,
    ATTR_PERCENTAGE,
    ATTR_PRESET_MODE,
    DOMAIN,
    SUPPORT_DIRECTION,
    SUPPORT_OSCILLATE,
    SUPPORT_SET_SPEED,
    FanEntity,
)
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA)

from .const import (
    COMPONENT_DOMAIN,
)
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

CONF_DIRECTION = "direction"
CONF_MODES = "modes"
CONF_OSCILLATE = "oscillate"
CONF_PERCENTAGE = "percentage"
CONF_SPEED = "speed"
CONF_SPEED_COUNT = "speed_count"

DEFAULT_INITIAL_VALUE = "off"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_INITIAL_VALUE, {

    vol.Optional(CONF_SPEED, default=False): cv.boolean,
    vol.Optional(CONF_SPEED_COUNT, default=0): cv.positive_int,
    vol.Optional(CONF_OSCILLATE, default=False): cv.boolean,
    vol.Optional(CONF_DIRECTION, default=False): cv.boolean,
    vol.Optional(CONF_MODES, default=[]): vol.All(cv.ensure_list, [cv.string]),
}))


async def async_setup_platform(_hass, config, async_add_entities, _discovery_info=None):
    """Set up the Demo config entry."""
    fans = [VirtualFan(config)]
    async_add_entities(fans, True)


class VirtualFan(VirtualEntity, FanEntity):
    """A demonstration fan component."""

    def __init__(self, config):
        """Initialize the entity."""
        super().__init__(config, DOMAIN)

        # Modes if supported
        self._attr_preset_modes = config.get(CONF_MODES)

        # Try for speed count then speed.
        #  - speed_count; number of speeds we support
        #  - speed == True; 3 speeds
        #  - speed == False; no speeds
        self._attr_speed_count = config.get(CONF_SPEED_COUNT)
        if config.get(CONF_SPEED, False):
            self._attr_speed_count = 3

        self._attr_supported_features = 0
        if self._attr_speed_count > 0:
            self._attr_supported_features |= SUPPORT_SET_SPEED
        if config.get(CONF_OSCILLATE, False):
            self._attr_supported_features |= SUPPORT_OSCILLATE
        if config.get(CONF_DIRECTION, False):
            self._attr_supported_features |= SUPPORT_DIRECTION

        _LOGGER.info('VirtualFan: {} created'.format(self.name))

    def _create_state(self, config):
        super()._create_state(config)

        if self._attr_supported_features & SUPPORT_DIRECTION:
            self._attr_current_direction = "forward"
        if self._attr_supported_features & SUPPORT_OSCILLATE:
            self._attr_oscillating = False
        self._attr_percentage = None
        self._attr_preset_mode = None

    def _restore_state(self, state, config):
        super()._restore_state(state, config)

        if self._attr_supported_features & SUPPORT_DIRECTION:
            self._attr_current_direction = state.attributes.get(ATTR_DIRECTION)
        if self._attr_supported_features & SUPPORT_OSCILLATE:
            self._attr_oscillating = state.attributes.get(ATTR_OSCILLATING)
        self._attr_percentage = state.attributes.get(ATTR_PERCENTAGE)
        self._attr_preset_mode = state.attributes.get(ATTR_PRESET_MODE)

    def _update_attributes(self):
        super()._update_attributes();
        self._attr_extra_state_attributes.update({
            name: value for name, value in (
                (ATTR_DIRECTION, self._attr_current_direction),
                (ATTR_OSCILLATING, self._attr_oscillating),
                (ATTR_PERCENTAGE, self._attr_percentage),
                (ATTR_PRESET_MODE, self._attr_preset_mode),
            ) if value is not None
        })

    def set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan, as a percentage."""
        _LOGGER.debug(f"setting {self.name} pcent to {percentage}")
        self._attr_percentage = percentage
        self._attr_preset_mode = None
        self._update_attributes()

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        _LOGGER.debug(f"setting {self.name} mode to {preset_mode}")
        if preset_mode in self.preset_modes:
            self._attr_preset_mode = preset_mode
            self._attr_percentage = None
            self._update_attributes()
        else:
            raise ValueError(f"Invalid preset mode: {preset_mode}")

    def turn_on(
        self,
        speed: str = None,
        percentage: int = None,
        preset_mode: str = None,
        **kwargs,
    ) -> None:
        """Turn on the entity."""
        _LOGGER.debug(f"turning {self.name} on")
        if preset_mode:
            self.set_preset_mode(preset_mode)
            return

        if percentage is None:
            percentage = 67
        self.set_percentage(percentage)

    def turn_off(self, **kwargs) -> None:
        """Turn off the entity."""
        _LOGGER.debug(f"turning {self.name} off")
        self.set_percentage(0)

    def set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""
        _LOGGER.debug(f"setting direction of {self.name} to {direction}")
        self._attr_current_direction = direction
        self._update_attributes()

    def oscillate(self, oscillating: bool) -> None:
        """Set oscillation."""
        _LOGGER.debug(f"setting oscillate of {self.name} to {oscillating}")
        self._attr_oscillating = oscillating
        self._update_attributes()
