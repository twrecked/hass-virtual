"""This component provides support for a virtual siren."""
from __future__ import annotations

import datetime
import logging
from collections.abc import Callable
from typing import Any

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.siren import (
    ATTR_AVAILABLE_TONES,
    ATTR_DURATION,
    ATTR_TONE,
    ATTR_VOLUME_LEVEL,
    DOMAIN as PLATFORM_DOMAIN,
    SirenEntity,
    SirenEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util

from . import get_entity_configs
from .const import (
    ATTR_CONTROL_MODE,
    ATTR_GROUP_NAME,
    ATTR_TIME_REMAINING,
    COMPONENT_CONFIG,
    COMPONENT_DOMAIN,
    CONF_AVAILABLE_TONES,
    CONF_CLASS,
    CONF_DURATION,
    CONF_INITIAL_VALUE,
    CONF_INITIAL_VOLUME,
    CONF_MODE,
    CONF_SUPPORT_VOLUME_SET,
    CONF_YAML_CONFIG,
    DEFAULT_SIREN_DURATION,
    DEFAULT_SIREN_VALUE,
)
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

MODE_MANUAL = "manual"
MODE_AUTOMATIC = "automatic"

BASE_SCHEMA = virtual_schema(DEFAULT_SIREN_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_DURATION, default=DEFAULT_SIREN_DURATION): cv.positive_int,
    vol.Optional(CONF_MODE): vol.In(["manual", "automatic", "auto"]),
    vol.Optional(CONF_AVAILABLE_TONES): vol.Any(cv.ensure_list, dict),
    vol.Optional(CONF_SUPPORT_VOLUME_SET, default=False): cv.boolean,
    vol.Optional(CONF_INITIAL_VOLUME, default=1.0): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(BASE_SCHEMA)
SIREN_SCHEMA = vol.Schema(BASE_SCHEMA)


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")

        sirens = [VirtualSiren(config, True)]
        async_add_entities(sirens, True)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the entries...")

    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = SIREN_SCHEMA(entity)
        entities.append(VirtualSiren(entity, False))
    async_add_entities(entities)


class VirtualSiren(VirtualEntity, SirenEntity):
    """Representation of a Virtual siren."""

    def __init__(self, config: dict[str, Any], old_style: bool) -> None:
        """Initialize the Virtual siren device."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_device_class = config.get(CONF_CLASS)
        self._default_duration: int = int(config.get(CONF_DURATION, DEFAULT_SIREN_DURATION))

        mode_conf = config.get(CONF_MODE)
        if mode_conf:
            norm_mode = mode_conf.lower()
            if norm_mode in (MODE_AUTOMATIC, "auto"):
                self._mode = MODE_AUTOMATIC
                if self._default_duration <= 0:
                    self._default_duration = 30
            else:
                self._mode = MODE_MANUAL
        else:
            self._mode = MODE_AUTOMATIC if self._default_duration > 0 else MODE_MANUAL

        self._available_tones = config.get(CONF_AVAILABLE_TONES)
        self._support_volume_set = config.get(CONF_SUPPORT_VOLUME_SET, False)
        self._initial_volume = float(config.get(CONF_INITIAL_VOLUME, 1.0))

        features = SirenEntityFeature.TURN_ON | SirenEntityFeature.TURN_OFF | SirenEntityFeature.DURATION
        if self._available_tones:
            features |= SirenEntityFeature.TONES
            self._attr_available_tones = self._available_tones
        if self._support_volume_set:
            features |= SirenEntityFeature.VOLUME_SET
        self._attr_supported_features = features

        self._timer_cancel: Callable[[], None] | None = None
        self._off_time: datetime.datetime | None = None
        self._active_duration: int | None = None
        self._active_tone: int | str | None = None
        self._active_volume_level: float | None = self._initial_volume if self._support_volume_set else None

        _LOGGER.info(
            f"VirtualSiren: {self.name} created (mode={self._mode}, default_duration={self._default_duration})"
        )

    def _create_state(self, config: dict[str, Any]) -> None:
        super()._create_state(config)
        self._attr_is_on = config.get(CONF_INITIAL_VALUE, DEFAULT_SIREN_VALUE).lower() == STATE_ON
        self._active_duration = self._default_duration if (self._attr_is_on and self._default_duration > 0) else None
        self._active_tone = None
        self._active_volume_level = self._initial_volume if self._support_volume_set else None

    def _restore_state(self, state, config: dict[str, Any]) -> None:
        super()._restore_state(state, config)

        if state.state and state.state.lower() in (STATE_ON, STATE_OFF):
            self._attr_is_on = state.state.lower() == STATE_ON
        else:
            self._attr_is_on = config.get(CONF_INITIAL_VALUE, DEFAULT_SIREN_VALUE).lower() == STATE_ON

        if self._support_volume_set:
            vol_val = state.attributes.get(ATTR_VOLUME_LEVEL)
            if vol_val is not None:
                try:
                    self._active_volume_level = max(0.0, min(1.0, float(vol_val)))
                except (ValueError, TypeError):
                    self._active_volume_level = self._initial_volume
            else:
                self._active_volume_level = self._initial_volume

        if self._available_tones:
            tone_val = state.attributes.get(ATTR_TONE)
            if tone_val is not None:
                if isinstance(self._available_tones, dict):
                    if tone_val in self._available_tones or tone_val in self._available_tones.values():
                        self._active_tone = tone_val
                    else:
                        self._active_tone = None
                elif isinstance(self._available_tones, list):
                    if tone_val in self._available_tones:
                        self._active_tone = tone_val
                    else:
                        self._active_tone = None
            else:
                self._active_tone = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self._attr_is_on and self._default_duration > 0:
            self._cancel_timer()
            self._off_time = dt_util.utcnow() + datetime.timedelta(seconds=self._default_duration)
            self._timer_cancel = async_call_later(self.hass, self._default_duration, self._on_timer_expired)
            self._update_attributes()
            self.async_write_ha_state()

    def _cancel_timer(self) -> None:
        if self._timer_cancel is not None:
            self._timer_cancel()
            self._timer_cancel = None
        self._off_time = None

    @callback
    def _on_timer_expired(self, _now) -> None:
        _LOGGER.debug(f"Siren {self.name} timer expired, turning off")
        self._timer_cancel = None
        self._off_time = None
        self._attr_is_on = False
        self._active_duration = None
        self._update_attributes()
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        self._cancel_timer()
        await super().async_will_remove_from_hass()

    def _update_attributes(self) -> None:
        super()._update_attributes()

        self._attr_extra_state_attributes[ATTR_CONTROL_MODE] = self._mode
        if self._default_duration > 0:
            self._attr_extra_state_attributes[ATTR_DURATION] = self._default_duration

        if self._support_volume_set and self._active_volume_level is not None:
            self._attr_extra_state_attributes[ATTR_VOLUME_LEVEL] = self._active_volume_level

        if self._available_tones and self._active_tone is not None:
            self._attr_extra_state_attributes[ATTR_TONE] = self._active_tone

        if self._attr_is_on and self._off_time is not None:
            now = dt_util.utcnow()
            remaining = max(0, int((self._off_time - now).total_seconds()))
            self._attr_extra_state_attributes[ATTR_TIME_REMAINING] = remaining

    async def async_turn_on(self, **kwargs: Any) -> None:
        _LOGGER.debug(f"turning {self.name} on with {kwargs}")
        self._cancel_timer()
        self._attr_is_on = True

        if ATTR_TONE in kwargs:
            self._active_tone = kwargs[ATTR_TONE]

        if ATTR_VOLUME_LEVEL in kwargs:
            try:
                self._active_volume_level = max(0.0, min(1.0, float(kwargs[ATTR_VOLUME_LEVEL])))
            except (ValueError, TypeError):
                pass

        eff_duration = kwargs.get(ATTR_DURATION)
        if eff_duration is None:
            eff_duration = self._default_duration
        else:
            try:
                eff_duration = int(eff_duration)
            except (ValueError, TypeError):
                eff_duration = self._default_duration

        self._active_duration = eff_duration if eff_duration > 0 else None

        if eff_duration > 0:
            self._off_time = dt_util.utcnow() + datetime.timedelta(seconds=eff_duration)
            self._timer_cancel = async_call_later(self.hass, eff_duration, self._on_timer_expired)

        self._update_attributes()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        _LOGGER.debug(f"turning {self.name} off")
        self._cancel_timer()
        self._attr_is_on = False
        self._active_duration = None
        self._update_attributes()
        self.async_write_ha_state()
