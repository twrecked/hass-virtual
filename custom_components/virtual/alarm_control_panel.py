"""This component provides support for a virtual alarm control panel."""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
    CodeFormat,
    DOMAIN as PLATFORM_DOMAIN,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import get_entity_configs
from .const import (
    ATTR_GROUP_NAME,
    COMPONENT_CONFIG,
    COMPONENT_DOMAIN,
    CONF_ARMING_TIME,
    CONF_CODE,
    CONF_CODE_ARM_REQUIRED,
    CONF_INITIAL_VALUE,
    CONF_TRIGGER_TIME,
    CONF_YAML_CONFIG,
)
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_ALARM_VALUE = "disarmed"

VALID_STATES = {
    "disarmed": AlarmControlPanelState.DISARMED,
    "armed_home": AlarmControlPanelState.ARMED_HOME,
    "armed_away": AlarmControlPanelState.ARMED_AWAY,
    "armed_night": AlarmControlPanelState.ARMED_NIGHT,
    "armed_vacation": AlarmControlPanelState.ARMED_VACATION,
    "armed_custom_bypass": AlarmControlPanelState.ARMED_CUSTOM_BYPASS,
    "triggered": AlarmControlPanelState.TRIGGERED,
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_ALARM_VALUE, {
    vol.Optional(CONF_CODE): cv.string,
    vol.Optional(CONF_CODE_ARM_REQUIRED, default=False): cv.boolean,
    vol.Optional(CONF_ARMING_TIME, default=0): cv.positive_int,
    vol.Optional(CONF_TRIGGER_TIME, default=0): cv.positive_int,
}))
ALARM_SCHEMA = vol.Schema(virtual_schema(DEFAULT_ALARM_VALUE, {
    vol.Optional(CONF_CODE): cv.string,
    vol.Optional(CONF_CODE_ARM_REQUIRED, default=False): cv.boolean,
    vol.Optional(CONF_ARMING_TIME, default=0): cv.positive_int,
    vol.Optional(CONF_TRIGGER_TIME, default=0): cv.positive_int,
}))


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")

        panels = [VirtualAlarmControlPanel(config, True)]
        async_add_entities(panels, True)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the entries...")

    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = ALARM_SCHEMA(entity)
        entities.append(VirtualAlarmControlPanel(entity, False))
    async_add_entities(entities)


class VirtualAlarmControlPanel(VirtualEntity, AlarmControlPanelEntity):
    """Representation of a Virtual alarm control panel."""

    def __init__(self, config: dict[str, Any], old_style: bool):
        """Initialize the Virtual alarm control panel."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._code = config.get(CONF_CODE)
        self._code_arm_required = config.get(CONF_CODE_ARM_REQUIRED, False)
        self._arming_time = int(config.get(CONF_ARMING_TIME, 0))
        self._trigger_time = int(config.get(CONF_TRIGGER_TIME, 0))
        self._timer_handle = None

        self._attr_supported_features = (
            AlarmControlPanelEntityFeature.ARM_HOME
            | AlarmControlPanelEntityFeature.ARM_AWAY
            | AlarmControlPanelEntityFeature.ARM_NIGHT
            | AlarmControlPanelEntityFeature.ARM_VACATION
            | AlarmControlPanelEntityFeature.ARM_CUSTOM_BYPASS
            | AlarmControlPanelEntityFeature.TRIGGER
        )

        if self._code:
            self._attr_code_format = CodeFormat.NUMBER if str(self._code).isdigit() else CodeFormat.TEXT
            self._attr_code_arm_required = self._code_arm_required
        else:
            self._attr_code_format = None
            self._attr_code_arm_required = False

        _LOGGER.info(f"VirtualAlarmControlPanel: {self.name} created")

    def _create_state(self, config: dict[str, Any]) -> None:
        super()._create_state(config)
        raw_state = str(config.get(CONF_INITIAL_VALUE, DEFAULT_ALARM_VALUE)).lower()
        self._attr_alarm_state = VALID_STATES.get(raw_state, AlarmControlPanelState.DISARMED)

    def _restore_state(self, state, config: dict[str, Any]) -> None:
        super()._restore_state(state, config)
        if state.state and state.state in VALID_STATES:
            self._attr_alarm_state = VALID_STATES[state.state]
        else:
            self._create_state(config)

    def _cancel_timer(self) -> None:
        if self._timer_handle:
            self._timer_handle()
            self._timer_handle = None

    async def async_will_remove_from_hass(self) -> None:
        self._cancel_timer()
        await super().async_will_remove_from_hass()

    def _validate_code(self, code: str | None, arming: bool = False) -> bool:
        if not self._code:
            return True
        if arming and not self._code_arm_required:
            return True
        if code and str(code) == str(self._code):
            return True
        return False

    def _start_arming(self, target_state: AlarmControlPanelState) -> None:
        self._cancel_timer()

        if self._arming_time > 0:
            self._attr_alarm_state = AlarmControlPanelState.ARMING
            self.async_write_ha_state()

            @callback
            def _finish_arming(_now) -> None:
                self._timer_handle = None
                self._attr_alarm_state = target_state
                self.async_write_ha_state()

            self._timer_handle = async_call_later(self.hass, self._arming_time, _finish_arming)
        else:
            self._attr_alarm_state = target_state
            self.async_write_ha_state()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        if not self._validate_code(code, arming=False):
            _LOGGER.warning(f"Invalid code provided to disarm {self.name}")
            raise HomeAssistantError("Invalid alarm code")

        self._cancel_timer()
        self._attr_alarm_state = AlarmControlPanelState.DISARMED
        self._update_attributes()
        self.async_write_ha_state()

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        if not self._validate_code(code, arming=True):
            raise HomeAssistantError("Invalid alarm code")
        self._start_arming(AlarmControlPanelState.ARMED_HOME)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        if not self._validate_code(code, arming=True):
            raise HomeAssistantError("Invalid alarm code")
        self._start_arming(AlarmControlPanelState.ARMED_AWAY)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night command."""
        if not self._validate_code(code, arming=True):
            raise HomeAssistantError("Invalid alarm code")
        self._start_arming(AlarmControlPanelState.ARMED_NIGHT)

    async def async_alarm_arm_vacation(self, code: str | None = None) -> None:
        """Send arm vacation command."""
        if not self._validate_code(code, arming=True):
            raise HomeAssistantError("Invalid alarm code")
        self._start_arming(AlarmControlPanelState.ARMED_VACATION)

    async def async_alarm_arm_custom_bypass(self, code: str | None = None) -> None:
        """Send arm custom bypass command."""
        if not self._validate_code(code, arming=True):
            raise HomeAssistantError("Invalid alarm code")
        self._start_arming(AlarmControlPanelState.ARMED_CUSTOM_BYPASS)

    async def async_alarm_trigger(self, code: str | None = None) -> None:
        """Send trigger command."""
        self._cancel_timer()

        if self._trigger_time > 0:
            self._attr_alarm_state = AlarmControlPanelState.PENDING
            self.async_write_ha_state()

            @callback
            def _finish_trigger(_now) -> None:
                self._timer_handle = None
                self._attr_alarm_state = AlarmControlPanelState.TRIGGERED
                self.async_write_ha_state()

            self._timer_handle = async_call_later(self.hass, self._trigger_time, _finish_trigger)
        else:
            self._attr_alarm_state = AlarmControlPanelState.TRIGGERED
            self.async_write_ha_state()
