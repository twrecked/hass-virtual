"""This component provides support for a virtual binary sensor with auto-off timeout and entity gating."""
from __future__ import annotations

import datetime
import logging
from collections.abc import Callable
from typing import Any

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    DOMAIN as PLATFORM_DOMAIN,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, HomeAssistant, ServiceCall, callback
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util, slugify

from . import get_entity_from_domain, get_entity_configs
from .const import (
    ATTR_GROUP_NAME,
    ATTR_LINKED_ENTITY,
    ATTR_OFF_DELAY,
    ATTR_TIME_REMAINING,
    COMPONENT_CONFIG,
    COMPONENT_DOMAIN,
    COMPONENT_SERVICES,
    CONF_CLASS,
    CONF_INITIAL_VALUE,
    CONF_LINKED_ENTITY,
    CONF_OFF_DELAY,
    CONF_YAML_CONFIG,
)
from .entity import VirtualEntity, virtual_schema

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_BINARY_SENSOR_VALUE = "off"

BASE_SCHEMA = virtual_schema(DEFAULT_BINARY_SENSOR_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_OFF_DELAY): vol.Coerce(float),
    vol.Optional(CONF_LINKED_ENTITY): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(BASE_SCHEMA)
BINARY_SENSOR_SCHEMA = vol.Schema(BASE_SCHEMA)

SERVICE_ON = "turn_on"
SERVICE_OFF = "turn_off"
SERVICE_TOGGLE = "toggle"

SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
})

SERVICE_ON_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Optional("duration"): vol.Coerce(float),
})


def setup_services(hass: HomeAssistant) -> None:
    """Register virtual binary sensor services."""

    async def async_virtual_service(call: ServiceCall) -> None:
        """Call virtual service handler."""
        _LOGGER.debug(f"{call.service} service called")
        if call.service == SERVICE_ON:
            await async_virtual_on_service(hass, call)
        elif call.service == SERVICE_OFF:
            await async_virtual_off_service(hass, call)
        elif call.service == SERVICE_TOGGLE:
            await async_virtual_toggle_service(hass, call)

    if PLATFORM_DOMAIN not in hass.data[COMPONENT_SERVICES]:
        _LOGGER.debug("installing binary_sensor handlers")
        hass.data[COMPONENT_SERVICES][PLATFORM_DOMAIN] = "installed"
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_ON, async_virtual_service, schema=SERVICE_ON_SCHEMA,
        )
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_OFF, async_virtual_service, schema=SERVICE_SCHEMA,
        )
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_TOGGLE, async_virtual_service, schema=SERVICE_SCHEMA,
        )


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up virtual binary sensor from YAML configuration."""
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")
        binary_sensors = [VirtualBinarySensor(config, True)]
        async_add_entities(binary_sensors, True)
        setup_services(hass)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable[[list], None],
) -> None:
    """Set up virtual binary sensor from a config entry."""
    _LOGGER.debug("setting up the entries...")
    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = BINARY_SENSOR_SCHEMA(entity)
        entities.append(VirtualBinarySensor(entity, False))
    async_add_entities(entities)
    setup_services(hass)


class VirtualBinarySensor(VirtualEntity, BinarySensorEntity):
    """An implementation of a Virtual Binary Sensor with auto-off timeout and entity gating."""

    def __init__(self, config: dict[str, Any], old_style: bool):
        """Initialize a Virtual Binary Sensor."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_device_class = config.get(CONF_CLASS)

        raw_delay = config.get(CONF_OFF_DELAY)
        self._off_delay: float | None = float(raw_delay) if raw_delay is not None else None

        self._linked_entity_config: str | None = config.get(CONF_LINKED_ENTITY)
        self._linked_entity_id: str | None = None
        self._linked_entity_state: str = STATE_ON

        self._off_time: datetime.datetime | None = None
        self._timer_cancel: Callable[[], None] | None = None
        self._entity_unsub: Callable[[], None] | None = None

        _LOGGER.info(
            f"VirtualBinarySensor: {self.name} created (off_delay={self._off_delay}, linked_entity={self._linked_entity_config})"
        )

    def _create_state(self, config: dict[str, Any]) -> None:
        """Create initial state."""
        super()._create_state(config)
        self._attr_is_on = config.get(CONF_INITIAL_VALUE, DEFAULT_BINARY_SENSOR_VALUE).lower() == STATE_ON

    def _restore_state(self, state, config: dict[str, Any]) -> None:
        """Restore state from persistent storage with null safety (per AGENTS.local.md)."""
        super()._restore_state(state, config)

        if state.state and state.state.lower() in (STATE_ON, STATE_OFF):
            self._attr_is_on = state.state.lower() == STATE_ON
        else:
            self._attr_is_on = config.get(CONF_INITIAL_VALUE, DEFAULT_BINARY_SENSOR_VALUE).lower() == STATE_ON

    def _update_attributes(self) -> None:
        """Update extra state attributes."""
        super()._update_attributes()

        if self._off_delay is not None:
            self._attr_extra_state_attributes[ATTR_OFF_DELAY] = self._off_delay

        if self._linked_entity_id or self._linked_entity_config:
            self._attr_extra_state_attributes[ATTR_LINKED_ENTITY] = self._linked_entity_id or self._linked_entity_config

        if self._off_time and self._attr_is_on:
            now = dt_util.utcnow()
            remaining = max(0, int((self._off_time - now).total_seconds()))
            self._attr_extra_state_attributes[ATTR_TIME_REMAINING] = remaining
        else:
            self._attr_extra_state_attributes[ATTR_TIME_REMAINING] = 0

    def _resolve_linked_entity_id(self) -> str | None:
        """Resolve linked entity name to entity_id across common domains."""
        if not self._linked_entity_config:
            return None
        if "." in self._linked_entity_config:
            return self._linked_entity_config

        slug = slugify(self._linked_entity_config)
        # Search by common platforms: camera, switch, light, media_player, etc.
        for domain in ("camera", "switch", "light", "media_player", "climate", "fan", "lock", "cover"):
            for candidate in (f"{domain}.{slug}", f"{domain}.{COMPONENT_DOMAIN}_{slug}"):
                if self.hass.states.get(candidate):
                    return candidate

        return f"camera.{slug}"

    def _is_linked_entity_off(self, state_str: str) -> bool:
        """Check if linked entity is in an off or unavailable state."""
        return state_str.lower() in (STATE_OFF, STATE_UNAVAILABLE, STATE_UNKNOWN, "standby")

    def _on_linked_entity_change(self, new_state: str) -> None:
        """Handle state transition of linked entity."""
        _LOGGER.debug(f"{self.name}: linked entity {self._linked_entity_id} changed to {new_state}")
        self._linked_entity_state = new_state
        if self._is_linked_entity_off(new_state):
            if self._attr_is_on:
                _LOGGER.debug(f"{self.name}: linked entity is {new_state}, turning binary sensor off")
                self.turn_off()
            else:
                self._update_attributes()
                self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to Home Assistant."""
        await super().async_added_to_hass()

        if not self._linked_entity_config:
            return

        self._linked_entity_id = self._resolve_linked_entity_id()
        if self._linked_entity_id:
            current_state = self.hass.states.get(self._linked_entity_id)
            if current_state:
                self._linked_entity_state = current_state.state

            @callback
            def _handle_entity_change(event: Event) -> None:
                new_state = event.data.get("new_state")
                if new_state is None:
                    return
                self._on_linked_entity_change(new_state.state)

            self._entity_unsub = async_track_state_change_event(
                self.hass, [self._linked_entity_id], _handle_entity_change
            )

        self._update_attributes()

    async def async_will_remove_from_hass(self) -> None:
        """Clean up timers and subscriptions when entity is removed."""
        self._cancel_timer()
        if self._entity_unsub:
            self._entity_unsub()
            self._entity_unsub = None
        await super().async_will_remove_from_hass()

    def _cancel_timer(self) -> None:
        """Cancel any active auto-off countdown timer."""
        if self._timer_cancel:
            self._timer_cancel()
            self._timer_cancel = None
        self._off_time = None

    @callback
    def _on_timer_expired(self, _now=None) -> None:
        """Handle expiration of auto-off timeout."""
        _LOGGER.debug(f"{self.name}: auto-off timeout expired, resetting to off")
        self._timer_cancel = None
        self._off_time = None
        self._attr_is_on = False
        self._update_attributes()
        self.async_write_ha_state()

    def turn_on(self, duration: float | None = None) -> None:
        """Turn the binary sensor on with optional auto-off duration."""
        _LOGGER.debug(f"turning {self.name} on (duration={duration})")

        # Gating check: if linked entity is off, do not trigger
        if self._linked_entity_id:
            current = self.hass.states.get(self._linked_entity_id) if self.hass else None
            current_state = current.state if current else self._linked_entity_state
            if self._is_linked_entity_off(current_state):
                _LOGGER.warning(
                    f"Cannot trigger {self.name}: linked entity {self._linked_entity_id} is {current_state}"
                )
                return

        self._attr_is_on = True

        # Cancel any previous timer to extend countdown
        self._cancel_timer()

        eff_duration = duration if duration is not None else self._off_delay
        if eff_duration is not None and eff_duration > 0:
            self._off_time = dt_util.utcnow() + datetime.timedelta(seconds=eff_duration)
            self._timer_cancel = async_call_later(self.hass, eff_duration, self._on_timer_expired)

        self._update_attributes()
        self.async_write_ha_state()

    def turn_off(self) -> None:
        """Turn the binary sensor off."""
        _LOGGER.debug(f"turning {self.name} off")
        self._cancel_timer()
        self._attr_is_on = False
        self._update_attributes()
        self.async_write_ha_state()

    def toggle(self) -> None:
        """Toggle the binary sensor state."""
        if self.is_on:
            self.turn_off()
        else:
            self.turn_on()


async def async_virtual_on_service(hass: HomeAssistant, call: ServiceCall) -> None:
    """Turn on virtual binary sensor(s) with optional duration."""
    duration = call.data.get("duration")
    for entity_id in call.data[ATTR_ENTITY_ID]:
        _LOGGER.debug(f"turning on {entity_id} (duration={duration})")
        get_entity_from_domain(hass, PLATFORM_DOMAIN, entity_id).turn_on(duration=duration)


async def async_virtual_off_service(hass: HomeAssistant, call: ServiceCall) -> None:
    """Turn off virtual binary sensor(s)."""
    for entity_id in call.data[ATTR_ENTITY_ID]:
        _LOGGER.debug(f"turning off {entity_id}")
        get_entity_from_domain(hass, PLATFORM_DOMAIN, entity_id).turn_off()


async def async_virtual_toggle_service(hass: HomeAssistant, call: ServiceCall) -> None:
    """Toggle virtual binary sensor(s)."""
    for entity_id in call.data[ATTR_ENTITY_ID]:
        _LOGGER.debug(f"toggling {entity_id}")
        get_entity_from_domain(hass, PLATFORM_DOMAIN, entity_id).toggle()
