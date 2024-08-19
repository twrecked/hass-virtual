"""
This component provides support for a virtual lock.

"""

import logging
import random
import voluptuous as vol
from collections.abc import Callable
from datetime import timedelta
from typing import Any

import homeassistant.helpers.config_validation as cv
from homeassistant.components.lock import (
    DOMAIN as PLATFORM_DOMAIN,
    LockEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_LOCKED
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import get_entity_configs
from .const import *
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

CONF_CHANGE_TIME = "locking_time"
CONF_TEST_JAMMING = "jamming_test"

DEFAULT_LOCK_VALUE = "locked"
DEFAULT_CHANGE_TIME = timedelta(seconds=0)
DEFAULT_TEST_JAMMING = 0

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_LOCK_VALUE, {
    vol.Optional(CONF_CHANGE_TIME, default=DEFAULT_CHANGE_TIME): vol.All(cv.time_period, cv.positive_timedelta),
    vol.Optional(CONF_TEST_JAMMING, default=DEFAULT_TEST_JAMMING): cv.positive_int,
}))
LOCK_SCHEMA = vol.Schema(virtual_schema(DEFAULT_LOCK_VALUE, {
    vol.Optional(CONF_CHANGE_TIME, default=DEFAULT_CHANGE_TIME): vol.All(cv.time_period, cv.positive_timedelta),
    vol.Optional(CONF_TEST_JAMMING, default=DEFAULT_TEST_JAMMING): cv.positive_int,
}))


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")

        locks = [VirtualLock(hass, config, True)]
        async_add_entities(locks, True)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the entries...")

    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = LOCK_SCHEMA(entity)
        entities.append(VirtualLock(hass, entity, False))
    async_add_entities(entities)


class VirtualLock(VirtualEntity, LockEntity):
    """Representation of a Virtual lock."""

    def __init__(self, hass, config, old_style: bool):
        """Initialize the Virtual lock device."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._hass = hass
        self._change_time = config.get(CONF_CHANGE_TIME)
        self._test_jamming = config.get(CONF_TEST_JAMMING)
        
        _LOGGER.info('VirtualLock: {} created'.format(self.name))

    def _create_state(self, config):
        super()._create_state(config)

        self._attr_is_locked = config.get(CONF_INITIAL_VALUE).lower() == STATE_LOCKED

    def _restore_state(self, state, config):
        super()._restore_state(state, config)

        self._attr_is_locked = state.state == STATE_LOCKED

    def _lock(self) -> None:
        if self._test_jamming == 0 or random.randint(0, self._test_jamming) > 0:
            _LOGGER.debug(f"locked {self.name}")
            self._attr_is_locked = True
            self._attr_is_locking = False
            self._attr_is_unlocking = False
            self._attr_is_jammed = False
        else:
            self._jam()

    def _locking(self) -> None:
        _LOGGER.debug(f"locking {self.name}")
        self._attr_is_locked = False
        self._attr_is_locking = True
        self._attr_is_unlocking = False
        self._attr_is_jammed = False

    def _unlock(self) -> None:
        _LOGGER.debug(f"unlocked {self.name}")
        self._attr_is_locked = False
        self._attr_is_locking = False
        self._attr_is_unlocking = False
        self._attr_is_jammed = False

    def _unlocking(self) -> None:
        _LOGGER.debug(f"unlocking {self.name}")
        self._attr_is_locked = False
        self._attr_is_locking = False
        self._attr_is_unlocking = True
        self._attr_is_jammed = False

    def _jam(self) -> None:
        _LOGGER.debug(f"jamming {self.name}")
        self._attr_is_locked = False
        self._attr_is_jammed = True

    @callback
    async def _finish_operation(self, _point_in_time) -> None:
        if self.is_locking:
            self._lock()
        if self.is_unlocking:
            self._unlock()
        self.async_schedule_update_ha_state()

    def _start_operation(self):
        async_call_later(self.hass, self._change_time, self._finish_operation)

    async def async_lock(self, **kwargs: Any) -> None:
        if self._change_time == DEFAULT_CHANGE_TIME:
            self._lock()
        else:
            self._locking()
            self._start_operation()

    async def async_unlock(self, **kwargs: Any) -> None:
        if self._change_time == DEFAULT_CHANGE_TIME:
            self._unlock()
        else:
            self._unlocking()
            self._start_operation()

    async def async_open(self, **kwargs: Any) -> None:
        _LOGGER.debug(f"opening {self.name}")
        self.unlock()
