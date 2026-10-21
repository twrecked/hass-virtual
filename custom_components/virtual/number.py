"""This component provides support for a virtual number."""
from __future__ import annotations

import logging
from collections.abc import Callable

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.number import (
    DOMAIN as PLATFORM_DOMAIN,
    NumberDeviceClass,
    NumberEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_UNIT_OF_MEASUREMENT
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
    CONF_INITIAL_VALUE,
    CONF_MAX,
    CONF_MIN,
    CONF_YAML_CONFIG,
    DEVICE_CLASS_UNITS,
)
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_NUMBER_VALUE = "0"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_NUMBER_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Required(CONF_MIN): vol.Coerce(float),
    vol.Required(CONF_MAX): vol.Coerce(float),
    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=""): cv.string,
}))
NUMBER_SCHEMA = vol.Schema(virtual_schema(DEFAULT_NUMBER_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Required(CONF_MIN): vol.Coerce(float),
    vol.Required(CONF_MAX): vol.Coerce(float),
    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=""): cv.string,
}))

async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")

        numbers = [VirtualNumber(config, True)]
        async_add_entities(numbers, True)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the entries...")

    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = NUMBER_SCHEMA(entity)
        entities.append(VirtualNumber(entity, False))
    async_add_entities(entities)


class VirtualNumber(VirtualEntity, NumberEntity):
    """An implementation of a Virtual Number."""

    def __init__(self, config, old_style: bool):
        """Initialize a Virtual Number."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_device_class = config.get(CONF_CLASS)
        self._attr_native_min_value = float(config.get(CONF_MIN))
        self._attr_native_max_value = float(config.get(CONF_MAX))

        # Set unit of measurement
        unit = config.get(CONF_UNIT_OF_MEASUREMENT)
        if unit in ("C", "c") and self._attr_device_class == NumberDeviceClass.TEMPERATURE:
            unit = DEVICE_CLASS_UNITS["temperature"]
        elif not unit and self._attr_device_class:
            unit = DEVICE_CLASS_UNITS.get(str(self._attr_device_class))

        self._attr_native_unit_of_measurement = unit

        _LOGGER.info(f"VirtualNumber: {self.name} created")

    def _create_state(self, config):
        super()._create_state(config)

        init_val = config.get(CONF_INITIAL_VALUE, DEFAULT_NUMBER_VALUE)
        try:
            val = float(init_val)
            self._attr_native_value = max(self._attr_native_min_value, min(self._attr_native_max_value, val))
        except (ValueError, TypeError):
            self._attr_native_value = self._attr_native_min_value

    def _restore_state(self, state, config):
        super()._restore_state(state, config)

        try:
            val = float(state.state)
            if self._attr_native_min_value <= val <= self._attr_native_max_value:
                self._attr_native_value = val
            else:
                self._attr_native_value = self._attr_native_min_value
        except (ValueError, TypeError):
            self._create_state(config)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        _LOGGER.debug(f"set {self.name} to {value}")
        self._attr_native_value = value
        self._update_attributes()
        self.async_write_ha_state()