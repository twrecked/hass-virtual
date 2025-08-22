"""
This component provides support for a virtual climate device.

Borrowed heavily from components/demo/climate.py
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from collections.abc import Callable

import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate import (
    ATTR_CURRENT_HUMIDITY,
    ATTR_CURRENT_TEMPERATURE,
    ATTR_FAN_MODE,
    ATTR_HUMIDITY,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    ATTR_SWING_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    ATTR_TEMPERATURE,
    ClimateEntity,
    ClimateEntityFeature,
    DOMAIN as PLATFORM_DOMAIN,
)

from homeassistant.const import (
    ATTR_TEMPERATURE,
    UnitOfTemperature,
)

# Import enums from the correct modules
try:
    from homeassistant.components.climate import HVACMode, HVACAction
except ImportError:
    from homeassistant.components.climate.const import HVACMode, HVACAction

try:
    from homeassistant.components.climate import FanMode, PresetMode, SwingMode
except ImportError:
    # For newer versions of Home Assistant, these are in different modules
    try:
        from homeassistant.components.fan import FanMode
    except ImportError:
        FanMode = None
        
    try:
        from homeassistant.components.climate import PresetMode
    except ImportError:
        PresetMode = None
        
    try:
        from homeassistant.components.climate import SwingMode
    except ImportError:
        SwingMode = None
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_validation import (PLATFORM_SCHEMA)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import get_entity_configs
from .const import *
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

# Constants are imported from .const

DEFAULT_CLIMATE_VALUE = "off"
DEFAULT_MIN_TEMP = 7.0
DEFAULT_MAX_TEMP = 35.0
DEFAULT_TARGET_TEMP = 20.0
DEFAULT_TARGET_TEMP_HIGH = 26.0
DEFAULT_TARGET_TEMP_LOW = 16.0
DEFAULT_TARGET_TEMP_STEP = 0.5
DEFAULT_CURRENT_TEMP = 20.0
DEFAULT_CURRENT_HUMIDITY = 50
DEFAULT_HUMIDITY = 50

BASE_SCHEMA = virtual_schema(DEFAULT_CLIMATE_VALUE, {
    vol.Optional("hvac_modes", default=["heat", "cool", "heat_cool", "dry", "fan_only", "off"]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional("fan_modes", default=["auto", "low", "medium", "high"]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional("preset_modes", default=["none", "eco", "boost"]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional("swing_modes", default=["off", "vertical", "horizontal", "both"]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional("min_temp", default=DEFAULT_MIN_TEMP): vol.Coerce(float),
    vol.Optional("max_temp", default=DEFAULT_MAX_TEMP): vol.Coerce(float),
    vol.Optional("target_temp_step", default=DEFAULT_TARGET_TEMP_STEP): vol.Coerce(float),
    vol.Optional("current_temperature", default=DEFAULT_CURRENT_TEMP): vol.Coerce(float),
    vol.Optional("current_humidity", default=DEFAULT_CURRENT_HUMIDITY): vol.Coerce(int),
    vol.Optional("target_temperature", default=DEFAULT_TARGET_TEMP): vol.Coerce(float),
    vol.Optional("target_temperature_high", default=DEFAULT_TARGET_TEMP_HIGH): vol.Coerce(float),
    vol.Optional("target_temperature_low", default=DEFAULT_TARGET_TEMP_LOW): vol.Coerce(float),
    vol.Optional("humidity", default=DEFAULT_HUMIDITY): vol.Coerce(int),
    vol.Optional("fan_mode", default="auto"): cv.string,
    vol.Optional("preset_mode", default="none"): cv.string,
    vol.Optional("swing_mode", default="off"): cv.string,
    vol.Optional("hvac_action", default="idle"): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(BASE_SCHEMA)

CLIMATE_SCHEMA = vol.Schema(BASE_SCHEMA)


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")

        climates = [VirtualClimate(config, True)]
        async_add_entities(climates, True)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the entries...")

    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = CLIMATE_SCHEMA(entity)
        entities.append(VirtualClimate(entity, False))
    async_add_entities(entities)


class VirtualClimate(VirtualEntity, ClimateEntity):
    """A demonstration climate component."""

    def __init__(self, config, old_style: bool):
        """Initialize the entity."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        # Set supported features
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE |
            ClimateEntityFeature.TARGET_TEMPERATURE_RANGE |
            ClimateEntityFeature.FAN_MODE |
            ClimateEntityFeature.PRESET_MODE |
            ClimateEntityFeature.SWING_MODE |
            ClimateEntityFeature.TURN_OFF |
            ClimateEntityFeature.TURN_ON
        )

        # Set HVAC modes
        self._attr_hvac_modes = config.get("hvac_modes")
        
        # Set fan modes - handle case where FanMode might not be available
        fan_modes = config.get("fan_modes")
        if FanMode is None and fan_modes:
            # Convert string modes to simple strings if FanMode enum is not available
            self._attr_fan_modes = [str(mode) for mode in fan_modes]
        else:
            self._attr_fan_modes = fan_modes
        
        # Set preset modes - handle case where PresetMode might not be available
        preset_modes = config.get("preset_modes")
        if PresetMode is None and preset_modes:
            # Convert string modes to simple strings if PresetMode enum is not available
            self._attr_preset_modes = [str(mode) for mode in preset_modes]
        else:
            self._attr_preset_modes = preset_modes
        
        # Set swing modes - handle case where SwingMode might not be available
        swing_modes = config.get("swing_modes")
        if SwingMode is None and swing_modes:
            # Convert string modes to simple strings if SwingMode enum is not available
            self._attr_swing_modes = [str(mode) for mode in swing_modes]
        else:
            self._attr_swing_modes = swing_modes
        
        # Set temperature range
        self._attr_min_temp = config.get("min_temp")
        self._attr_max_temp = config.get("max_temp")
        self._attr_target_temperature_step = config.get("target_temp_step")
        
        # Set initial values
        self._attr_current_temperature = config.get("current_temperature")
        self._attr_current_humidity = config.get("current_humidity")
        self._attr_target_temperature = config.get("target_temperature")
        self._attr_target_temperature_high = config.get("target_temperature_high")
        self._attr_target_temperature_low = config.get("target_temperature_low")
        self._attr_humidity = config.get("humidity")
        self._attr_fan_mode = config.get("fan_mode")
        self._attr_preset_mode = config.get("preset_mode")
        self._attr_swing_mode = config.get("swing_mode")
        self._attr_hvac_action = config.get("hvac_action")
        
        # Set initial HVAC mode
        initial_value = config.get("initial_value")
        if initial_value.lower() == "off":
            self._attr_hvac_mode = "off"
        else:
            # Use the first non-off mode from the configured modes, or default to heat
            available_modes = [mode for mode in self._attr_hvac_modes if mode != "off"]
            if available_modes:
                self._attr_hvac_mode = available_modes[0]
            else:
                self._attr_hvac_mode = "heat"

        _LOGGER.info(f"VirtualClimate: {self.name} created")

    def _update_hvac_action(self):
        """Update HVAC action based on current mode."""
        if self._attr_hvac_mode == "off":
            self._attr_hvac_action = "off"
        elif self._attr_hvac_mode == "heat":
            self._attr_hvac_action = "heating"
        elif self._attr_hvac_mode == "cool":
            self._attr_hvac_action = "cooling"
        elif self._attr_hvac_mode == "dry":
            self._attr_hvac_action = "drying"
        elif self._attr_hvac_mode == "fan_only":
            self._attr_hvac_action = "fan"
        elif self._attr_hvac_mode == "heat_cool":
            # For heat_cool mode, determine action based on current vs target temperature
            if self._attr_current_temperature and self._attr_target_temperature:
                if self._attr_current_temperature < self._attr_target_temperature:
                    self._attr_hvac_action = "heating"
                elif self._attr_current_temperature > self._attr_target_temperature:
                    self._attr_hvac_action = "cooling"
                else:
                    self._attr_hvac_action = "idle"
            else:
                self._attr_hvac_action = "idle"
        else:
            self._attr_hvac_action = "idle"

    def _create_state(self, config):
        super()._create_state(config)

    def _restore_state(self, state, config):
        super()._restore_state(state, config)

        # Restore climate-specific attributes
        self._attr_current_temperature = state.attributes.get(ATTR_CURRENT_TEMPERATURE, self._attr_current_temperature)
        self._attr_current_humidity = state.attributes.get(ATTR_CURRENT_HUMIDITY, self._attr_current_humidity)
        self._attr_target_temperature = state.attributes.get(ATTR_TEMPERATURE, self._attr_target_temperature)
        self._attr_target_temperature_high = state.attributes.get(ATTR_TARGET_TEMP_HIGH, self._attr_target_temperature_high)
        self._attr_target_temperature_low = state.attributes.get(ATTR_TARGET_TEMP_LOW, self._attr_target_temperature_low)
        self._attr_humidity = state.attributes.get(ATTR_HUMIDITY, self._attr_humidity)
        self._attr_fan_mode = state.attributes.get(ATTR_FAN_MODE, self._attr_fan_mode)
        self._attr_preset_mode = state.attributes.get(ATTR_PRESET_MODE, self._attr_preset_mode)
        self._attr_swing_mode = state.attributes.get(ATTR_SWING_MODE, self._attr_swing_mode)
        self._attr_hvac_action = state.attributes.get("hvac_action", self._attr_hvac_action)
        
        # Restore HVAC mode
        if state.state in self.hvac_modes:
            self._attr_hvac_mode = state.state

    def _update_attributes(self):
        super()._update_attributes()
        self._attr_extra_state_attributes.update({
            name: value for name, value in (
                (ATTR_CURRENT_TEMPERATURE, self._attr_current_temperature),
                (ATTR_CURRENT_HUMIDITY, self._attr_current_humidity),
                (ATTR_TARGET_TEMP_HIGH, self._attr_target_temperature_high),
                (ATTR_TARGET_TEMP_LOW, self._attr_target_temperature_low),
                (ATTR_HUMIDITY, self._attr_humidity),
                (ATTR_FAN_MODE, self._attr_fan_mode),
                (ATTR_PRESET_MODE, self._attr_preset_mode),
                (ATTR_SWING_MODE, self._attr_swing_mode),
                ("hvac_action", self._attr_hvac_action),
            ) if value is not None
        })

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        _LOGGER.debug(f"setting {self.name} temperature with kwargs: {kwargs}")
        
        if ATTR_TEMPERATURE in kwargs:
            self._attr_target_temperature = kwargs[ATTR_TEMPERATURE]
        if ATTR_TARGET_TEMP_HIGH in kwargs:
            self._attr_target_temperature_high = kwargs[ATTR_TARGET_TEMP_HIGH]
        if ATTR_TARGET_TEMP_LOW in kwargs:
            self._attr_target_temperature_low = kwargs[ATTR_TARGET_TEMP_LOW]
            
        self._update_attributes()

    async def async_set_humidity(self, humidity: int) -> None:
        """Set new target humidity."""
        _LOGGER.debug(f"setting {self.name} humidity to {humidity}")
        self._attr_humidity = humidity
        self._update_attributes()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        _LOGGER.debug(f"setting {self.name} fan mode to {fan_mode}")
        if fan_mode in self.fan_modes:
            self._attr_fan_mode = fan_mode
            self._update_attributes()
        else:
            raise ValueError(f"Invalid fan mode: {fan_mode}")

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        _LOGGER.debug(f"setting {self.name} preset mode to {preset_mode}")
        if preset_mode in self.preset_modes:
            self._attr_preset_mode = preset_mode
            self._update_attributes()
        else:
            raise ValueError(f"Invalid preset mode: {preset_mode}")

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new target swing mode."""
        _LOGGER.debug(f"setting {self.name} swing mode to {swing_mode}")
        if swing_mode in self.swing_modes:
            self._attr_swing_mode = swing_mode
            self._update_attributes()
        else:
            raise ValueError(f"Invalid swing mode: {swing_mode}")

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new target hvac mode."""
        _LOGGER.debug(f"setting {self.name} hvac mode to {hvac_mode}")
        if hvac_mode in self.hvac_modes:
            # Store the previous mode for cycling
            if self._attr_hvac_mode != "off":
                self._previous_hvac_mode = self._attr_hvac_mode
            
            self._attr_hvac_mode = hvac_mode
            self._update_hvac_action()
            self._update_attributes()
        else:
            raise ValueError(f"Invalid hvac mode: {hvac_mode}")

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        _LOGGER.debug(f"turning {self.name} on")
        if self._attr_hvac_mode == "off":
            # Find the next available mode, cycling through available modes
            available_modes = [mode for mode in self._attr_hvac_modes if mode != "off"]
            if available_modes:
                # If we have a previous mode stored, try to use the next one
                if hasattr(self, '_previous_hvac_mode') and self._previous_hvac_mode in available_modes:
                    # Find the index of the previous mode and move to the next
                    try:
                        current_index = available_modes.index(self._previous_hvac_mode)
                        next_index = (current_index + 1) % len(available_modes)
                        self._attr_hvac_mode = available_modes[next_index]
                    except ValueError:
                        self._attr_hvac_mode = available_modes[0]
                else:
                    # Use the first available mode
                    self._attr_hvac_mode = available_modes[0]
                
                # Set appropriate action based on the mode
                self._update_hvac_action()
            else:
                # Fallback to heat if no other modes available
                self._attr_hvac_mode = "heat"
                self._attr_hvac_action = "heating"
        self._update_attributes()

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        _LOGGER.debug(f"turning {self.name} off")
        self._attr_hvac_mode = "off"
        self._attr_hvac_action = "off"
        self._update_attributes()

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS
