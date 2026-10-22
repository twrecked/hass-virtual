"""This component provides support for a virtual climate entity."""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_FAN_MODE,
    ATTR_HVAC_ACTION,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    ClimateEntity,
    ClimateEntityFeature,
    DOMAIN as PLATFORM_DOMAIN,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    PRECISION_HALVES,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import get_entity_from_domain, get_entity_configs
from .const import (
    ATTR_GROUP_NAME,
    COMPONENT_CONFIG,
    COMPONENT_DOMAIN,
    COMPONENT_SERVICES,
    CONF_FAN_MODES,
    CONF_HVAC_MODES,
    CONF_INITIAL_CURRENT_TEMPERATURE,
    CONF_INITIAL_TEMPERATURE,
    CONF_INITIAL_VALUE,
    CONF_MAX,
    CONF_MIN,
    CONF_PRESET_MODES,
    CONF_TARGET_TEMP_STEP,
    CONF_YAML_CONFIG,
    SERVICE_SET_CURRENT_TEMPERATURE,
)
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_CLIMATE_VALUE = "heat"
DEFAULT_TARGET_TEMP = 21.0
DEFAULT_CURRENT_TEMP = 20.0
DEFAULT_MIN_TEMP = 7.0
DEFAULT_MAX_TEMP = 35.0
DEFAULT_TARGET_TEMP_STEP = 0.5

HVAC_MODE_MAP = {
    "off": HVACMode.OFF,
    "heat": HVACMode.HEAT,
    "cool": HVACMode.COOL,
    "heat_cool": HVACMode.HEAT_COOL,
    "auto": HVACMode.AUTO,
    "dry": HVACMode.DRY,
    "fan_only": HVACMode.FAN_ONLY,
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_CLIMATE_VALUE, {
    vol.Optional(CONF_INITIAL_TEMPERATURE, default=DEFAULT_TARGET_TEMP): vol.Coerce(float),
    vol.Optional(CONF_INITIAL_CURRENT_TEMPERATURE, default=DEFAULT_CURRENT_TEMP): vol.Coerce(float),
    vol.Optional(CONF_MIN, default=DEFAULT_MIN_TEMP): vol.Coerce(float),
    vol.Optional(CONF_MAX, default=DEFAULT_MAX_TEMP): vol.Coerce(float),
    vol.Optional(CONF_TARGET_TEMP_STEP, default=DEFAULT_TARGET_TEMP_STEP): vol.Coerce(float),
    vol.Optional(CONF_HVAC_MODES, default=["off", "heat", "cool", "auto"]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_PRESET_MODES, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_FAN_MODES, default=[]): vol.All(cv.ensure_list, [cv.string]),
}))

CLIMATE_SCHEMA = vol.Schema(virtual_schema(DEFAULT_CLIMATE_VALUE, {
    vol.Optional(CONF_INITIAL_TEMPERATURE, default=DEFAULT_TARGET_TEMP): vol.Coerce(float),
    vol.Optional(CONF_INITIAL_CURRENT_TEMPERATURE, default=DEFAULT_CURRENT_TEMP): vol.Coerce(float),
    vol.Optional(CONF_MIN, default=DEFAULT_MIN_TEMP): vol.Coerce(float),
    vol.Optional(CONF_MAX, default=DEFAULT_MAX_TEMP): vol.Coerce(float),
    vol.Optional(CONF_TARGET_TEMP_STEP, default=DEFAULT_TARGET_TEMP_STEP): vol.Coerce(float),
    vol.Optional(CONF_HVAC_MODES, default=["off", "heat", "cool", "auto"]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_PRESET_MODES, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_FAN_MODES, default=[]): vol.All(cv.ensure_list, [cv.string]),
}))

SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required(ATTR_TEMPERATURE): vol.Coerce(float),
})


def setup_services(hass: HomeAssistant) -> None:
    async def async_virtual_service(call: ServiceCall) -> None:
        """Call virtual climate service handler."""
        _LOGGER.debug(f"{call.service} service called")
        await async_virtual_set_current_temp_service(hass, call)

    if PLATFORM_DOMAIN not in hass.data[COMPONENT_SERVICES]:
        _LOGGER.debug("installing climate handlers")
        hass.data[COMPONENT_SERVICES][PLATFORM_DOMAIN] = "installed"
        hass.services.async_register(
            COMPONENT_DOMAIN,
            SERVICE_SET_CURRENT_TEMPERATURE,
            async_virtual_service,
            schema=SERVICE_SCHEMA,
        )


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
        setup_services(hass)


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
    setup_services(hass)


class VirtualClimate(VirtualEntity, ClimateEntity):
    """Representation of a Virtual climate entity."""

    def __init__(self, config: dict[str, Any], old_style: bool):
        """Initialize the Virtual climate device."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_min_temp = float(config.get(CONF_MIN, DEFAULT_MIN_TEMP))
        self._attr_max_temp = float(config.get(CONF_MAX, DEFAULT_MAX_TEMP))
        self._attr_target_temperature_step = float(config.get(CONF_TARGET_TEMP_STEP, DEFAULT_TARGET_TEMP_STEP))
        self._attr_precision = PRECISION_HALVES if self._attr_target_temperature_step == 0.5 else PRECISION_TENTHS

        # HVAC modes
        raw_modes = config.get(CONF_HVAC_MODES, ["off", "heat", "cool", "auto"])
        self._attr_hvac_modes = [HVAC_MODE_MAP[m.lower()] for m in raw_modes if m.lower() in HVAC_MODE_MAP]
        if not self._attr_hvac_modes:
            self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]

        # Preset modes
        self._attr_preset_modes = config.get(CONF_PRESET_MODES, [])
        # Fan modes
        self._attr_fan_modes = config.get(CONF_FAN_MODES, [])

        # Supported features
        features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
        if self._attr_preset_modes:
            features |= ClimateEntityFeature.PRESET_MODE
        if self._attr_fan_modes:
            features |= ClimateEntityFeature.FAN_MODE
        self._attr_supported_features = features

        _LOGGER.info(f"VirtualClimate: {self.name} created")

    def _calculate_hvac_action(self) -> HVACAction:
        if self._attr_hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        if self._attr_current_temperature is None or self._attr_target_temperature is None:
            return HVACAction.IDLE

        if self._attr_hvac_mode == HVACMode.HEAT:
            if self._attr_current_temperature < self._attr_target_temperature:
                return HVACAction.HEATING
            return HVACAction.IDLE
        elif self._attr_hvac_mode == HVACMode.COOL:
            if self._attr_current_temperature > self._attr_target_temperature:
                return HVACAction.COOLING
            return HVACAction.IDLE
        elif self._attr_hvac_mode in (HVACMode.AUTO, HVACMode.HEAT_COOL):
            if self._attr_current_temperature < self._attr_target_temperature - 0.5:
                return HVACAction.HEATING
            elif self._attr_current_temperature > self._attr_target_temperature + 0.5:
                return HVACAction.COOLING
            return HVACAction.IDLE
        return HVACAction.IDLE

    def _create_state(self, config: dict[str, Any]) -> None:
        super()._create_state(config)

        raw_mode = str(config.get(CONF_INITIAL_VALUE, DEFAULT_CLIMATE_VALUE)).lower()
        self._attr_hvac_mode = HVAC_MODE_MAP.get(raw_mode, self._attr_hvac_modes[0])
        self._attr_target_temperature = float(config.get(CONF_INITIAL_TEMPERATURE, DEFAULT_TARGET_TEMP))
        self._attr_current_temperature = float(config.get(CONF_INITIAL_CURRENT_TEMPERATURE, DEFAULT_CURRENT_TEMP))
        self._attr_preset_mode = self._attr_preset_modes[0] if self._attr_preset_modes else None
        self._attr_fan_mode = self._attr_fan_modes[0] if self._attr_fan_modes else None
        self._attr_hvac_action = self._calculate_hvac_action()

    def _restore_state(self, state, config: dict[str, Any]) -> None:
        super()._restore_state(state, config)

        if state.state and state.state.lower() in HVAC_MODE_MAP:
            self._attr_hvac_mode = HVAC_MODE_MAP[state.state.lower()]
        else:
            self._attr_hvac_mode = self._attr_hvac_modes[0]

        target_temp = state.attributes.get(ATTR_TEMPERATURE)
        if target_temp is not None:
            try:
                self._attr_target_temperature = float(target_temp)
            except (ValueError, TypeError):
                self._attr_target_temperature = float(config.get(CONF_INITIAL_TEMPERATURE, DEFAULT_TARGET_TEMP))
        else:
            self._attr_target_temperature = float(config.get(CONF_INITIAL_TEMPERATURE, DEFAULT_TARGET_TEMP))

        current_temp = state.attributes.get(ATTR_CURRENT_TEMPERATURE)
        if current_temp is not None:
            try:
                self._attr_current_temperature = float(current_temp)
            except (ValueError, TypeError):
                self._attr_current_temperature = float(config.get(CONF_INITIAL_CURRENT_TEMPERATURE, DEFAULT_CURRENT_TEMP))
        else:
            self._attr_current_temperature = float(config.get(CONF_INITIAL_CURRENT_TEMPERATURE, DEFAULT_CURRENT_TEMP))

        self._attr_preset_mode = state.attributes.get(ATTR_PRESET_MODE)
        self._attr_fan_mode = state.attributes.get(ATTR_FAN_MODE)
        self._attr_hvac_action = self._calculate_hvac_action()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode | str) -> None:
        """Set new target hvac mode."""
        mode_val = HVAC_MODE_MAP.get(str(hvac_mode).lower(), hvac_mode)
        if mode_val in self._attr_hvac_modes:
            self._attr_hvac_mode = mode_val
            self._attr_hvac_action = self._calculate_hvac_action()
            self._update_attributes()
            self.async_write_ha_state()
        else:
            raise ValueError(f"Unsupported HVAC mode: {hvac_mode}")

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is not None:
            self._attr_target_temperature = max(self._attr_min_temp, min(self._attr_max_temp, float(temp)))
            self._attr_hvac_action = self._calculate_hvac_action()
            self._update_attributes()
            self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new target preset mode."""
        if preset_mode in self._attr_preset_modes:
            self._attr_preset_mode = preset_mode
            self._update_attributes()
            self.async_write_ha_state()
        else:
            raise ValueError(f"Unsupported preset mode: {preset_mode}")

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        if fan_mode in self._attr_fan_modes:
            self._attr_fan_mode = fan_mode
            self._update_attributes()
            self.async_write_ha_state()
        else:
            raise ValueError(f"Unsupported fan mode: {fan_mode}")

    async def async_turn_on(self) -> None:
        """Turn on the climate entity."""
        for mode in (HVACMode.HEAT, HVACMode.AUTO, HVACMode.COOL):
            if mode in self._attr_hvac_modes:
                await self.async_set_hvac_mode(mode)
                return
        await self.async_set_hvac_mode(self._attr_hvac_modes[0])

    async def async_turn_off(self) -> None:
        """Turn off the climate entity."""
        if HVACMode.OFF in self._attr_hvac_modes:
            await self.async_set_hvac_mode(HVACMode.OFF)

    def set_current_temperature(self, temperature: float) -> None:
        """Update current ambient temperature."""
        _LOGGER.debug(f"Setting current temperature of {self.name} to {temperature}")
        self._attr_current_temperature = float(temperature)
        self._attr_hvac_action = self._calculate_hvac_action()
        self._update_attributes()
        self.async_write_ha_state()


async def async_virtual_set_current_temp_service(hass: HomeAssistant, call: ServiceCall) -> None:
    temp = call.data[ATTR_TEMPERATURE]
    for entity_id in call.data[ATTR_ENTITY_ID]:
        _LOGGER.debug(f"setting current temp of {entity_id} to {temp}")
        get_entity_from_domain(hass, PLATFORM_DOMAIN, entity_id).set_current_temperature(temp)
