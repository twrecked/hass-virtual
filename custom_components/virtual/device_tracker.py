"""
This component provides support for a virtual device tracker.

"""

import logging
from collections.abc import Callable

from homeassistant.components.device_tracker import (
    DOMAIN as PLATFORM_DOMAIN,
    SourceType,
    TrackerEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import HomeAssistantType

from .const import *
from .entity import VirtualEntity

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

CONF_LOCATION = 'location'
DEFAULT_LOCATION = 'home'


async def async_setup_entry(
        hass: HomeAssistantType,
        _entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the device_tracker entries...")

    entities = []
    for entity in hass.data[COMPONENT_DOMAIN].get(PLATFORM_DOMAIN, []):
        entities.append(VirtualDeviceTracker(entity))
    async_add_entities(entities)


class VirtualDeviceTracker(TrackerEntity, VirtualEntity):
    """Represent a tracked device."""

    _location: str | None = None

    def __init__(self, config):
        """Initialize a Virtual light."""
        super().__init__(config, PLATFORM_DOMAIN)

    def _create_state(self, config):
        super()._create_state(config)
        self._location = DEFAULT_LOCATION

    def _restore_state(self, state, config):
        super()._restore_state(state, config)
        self._location = state.state

    @property
    def location_name(self) -> str | None:
        """Return a location name for the current location of the device."""
        return self._location

    @property
    def source_type(self) -> SourceType | str:
        return "virtual"

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return None

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return None
