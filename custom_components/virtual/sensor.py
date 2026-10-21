"""This component provides support for a virtual sensor."""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import (
    DOMAIN as PLATFORM_DOMAIN,
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import get_entity_from_domain, get_entity_configs
from .const import (
    ATTR_GROUP_NAME,
    ATTR_VALUE,
    COMPONENT_CONFIG,
    COMPONENT_DOMAIN,
    COMPONENT_SERVICES,
    CONF_CLASS,
    CONF_INITIAL_VALUE,
    CONF_YAML_CONFIG,
    DEVICE_CLASS_UNITS,
)
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_SENSOR_VALUE = "0"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_SENSOR_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=""): cv.string,
}))
SENSOR_SCHEMA = vol.Schema(virtual_schema(DEFAULT_SENSOR_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=""): cv.string,
}))

SERVICE_SET = "set"
SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required(ATTR_VALUE): cv.string,
})


def setup_services(hass: HomeAssistant) -> None:

    async def async_virtual_service(call: ServiceCall) -> None:
        """Call virtual service handler."""
        _LOGGER.debug(f"{call.service} service called")
        await async_virtual_set_service(hass, call)

    # Build up services...
    if PLATFORM_DOMAIN not in hass.data[COMPONENT_SERVICES]:
        _LOGGER.debug("installing handlers")
        hass.data[COMPONENT_SERVICES][PLATFORM_DOMAIN] = "installed"
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_SET, async_virtual_service, schema=SERVICE_SCHEMA,
        )


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")

        sensors = [VirtualSensor(config, True)]
        async_add_entities(sensors, True)
        setup_services(hass)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the entries...")

    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = SENSOR_SCHEMA(entity)
        entities.append(VirtualSensor(entity, False))
    async_add_entities(entities)
    setup_services(hass)


class VirtualSensor(VirtualEntity, SensorEntity):
    """An implementation of a Virtual Sensor."""

    def __init__(self, config, old_style: bool):
        """Initialize a Virtual Sensor."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_device_class = config.get(CONF_CLASS)

        # Set unit of measurement
        unit = config.get(CONF_UNIT_OF_MEASUREMENT)
        if unit in ("C", "c") and self._attr_device_class == SensorDeviceClass.TEMPERATURE:
            unit = DEVICE_CLASS_UNITS["temperature"]
        elif not unit and self._attr_device_class:
            unit = DEVICE_CLASS_UNITS.get(str(self._attr_device_class))

        self._attr_native_unit_of_measurement = unit

        _LOGGER.info(f"VirtualSensor: {self.name} created")

    def _create_state(self, config):
        super()._create_state(config)

        self._attr_native_value = config.get(CONF_INITIAL_VALUE, DEFAULT_SENSOR_VALUE)

    def _restore_state(self, state, config):
        super()._restore_state(state, config)

        if state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN, None):
            self._attr_native_value = state.state
        else:
            self._attr_native_value = config.get(CONF_INITIAL_VALUE, DEFAULT_SENSOR_VALUE)

    def set(self, value) -> None:
        _LOGGER.debug(f"set {self.name} to {value}")
        self._attr_native_value = value
        self._update_attributes()
        self.async_write_ha_state()


async def async_virtual_set_service(hass, call):
    for entity_id in call.data[ATTR_ENTITY_ID]:
        value = call.data[ATTR_VALUE]
        _LOGGER.debug(f"setting {entity_id} to {value})")
        get_entity_from_domain(hass, PLATFORM_DOMAIN, entity_id).set(value)
