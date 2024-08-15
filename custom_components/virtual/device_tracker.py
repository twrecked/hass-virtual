"""
This component provides support for a virtual device tracker.

"""

import logging
import voluptuous as vol
from collections.abc import Callable

import homeassistant.helpers.config_validation as cv
from homeassistant.components.device_tracker import (
    DOMAIN as PLATFORM_DOMAIN,
    SourceType,
    TrackerEntity,
)
from homeassistant.components.zone import ATTR_RADIUS
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_LATITUDE,
    ATTR_LONGITUDE
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA

from . import get_entity_from_domain, get_entity_configs
from .const import *
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

CONF_LOCATION = 'location'
CONF_GPS = 'gps'
DEFAULT_DEVICE_TRACKER_VALUE = 'home'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_DEVICE_TRACKER_VALUE, {
}))
DEVICE_TRACKER_SCHEMA = vol.Schema(virtual_schema(DEFAULT_DEVICE_TRACKER_VALUE, {
}))

SERVICE_MOVE = "move"
SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Optional(CONF_LOCATION): cv.string,
    vol.Optional(CONF_GPS): {
        vol.Required(ATTR_LATITUDE): cv.latitude,
        vol.Required(ATTR_LONGITUDE): cv.longitude,
        vol.Optional(ATTR_RADIUS): cv.string,
    },
})


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the device_tracker entries...")

    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = DEVICE_TRACKER_SCHEMA(entity)
        entities.append(VirtualDeviceTracker(entity))
    async_add_entities(entities)

    async def async_virtual_service(call):
        """Call virtual service handler."""
        _LOGGER.debug(f"{call.service} service called")
        if call.service == SERVICE_MOVE:
            await async_virtual_move_service(hass, call)

    # Build up services...
    if not hasattr(hass.data[COMPONENT_SERVICES], PLATFORM_DOMAIN):
        _LOGGER.debug("installing handlers")
        hass.data[COMPONENT_SERVICES][PLATFORM_DOMAIN] = 'installed'
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_MOVE, async_virtual_service, schema=SERVICE_SCHEMA,
        )


class VirtualDeviceTracker(TrackerEntity, VirtualEntity):
    """Represent a tracked device."""

    def __init__(self, config):
        """Initialize a Virtual Device Tracker."""

        # Handle deprecated option.
        if config.get(CONF_LOCATION, None) is not None:
            _LOGGER.info("'location' option is deprecated for virtual device trackers, please use 'initial_value'")
            config[CONF_INITIAL_VALUE] = config.pop(CONF_LOCATION)

        super().__init__(config, PLATFORM_DOMAIN)

        self._location = None
        self._coords = {}

        _LOGGER.debug(f"{self._attr_name}, available={self._attr_available}")
        _LOGGER.debug(f"{self._attr_name}, entity={self.entity_id}")

    def _create_state(self, config):
        _LOGGER.debug(f"device_tracker-create=config={config}")
        super()._create_state(config)
        self._location = config.get(CONF_INITIAL_VALUE)

    def _restore_state(self, state, config):
        _LOGGER.debug(f"device_tracker-restore=state={state.state}")
        _LOGGER.debug(f"device_tracker-restore=attrs={state.attributes}")

        if ATTR_AVAILABLE not in state.attributes:
            _LOGGER.debug("looks wrong, from upgrade? creating instead...")
            self._create_state(config)
            return

        super()._restore_state(state, config)
        if ATTR_LONGITUDE in state.attributes and ATTR_LATITUDE in state.attributes:
            self._location = None
            self._coords = {
                ATTR_LONGITUDE: state.attributes[ATTR_LONGITUDE],
                ATTR_LATITUDE: state.attributes[ATTR_LATITUDE],
                ATTR_RADIUS: 0
            }
        else:
            self._location = state.state
            self._coords = {}

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
        return self._coords.get(ATTR_LATITUDE, None)

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return self._coords.get(ATTR_LONGITUDE, None)

    def move_to_location(self, new_location):
        _LOGGER.debug(f"{self._attr_name} moving to {new_location}")
        self._location = new_location
        self._coords = {}
        self.async_schedule_update_ha_state()

    def move_to_coords(self, new_coords):
        _LOGGER.debug(f"{self._attr_name} moving via GPS to {new_coords}")
        self._location = None
        self._coords = new_coords
        self.async_schedule_update_ha_state()


async def async_virtual_move_service(hass, call):
    for entity_id in call.data['entity_id']:
        _LOGGER.debug(f"moving {entity_id} --> {call.data}")

        entity = get_entity_from_domain(hass, PLATFORM_DOMAIN, entity_id)
        if entity is None:
            _LOGGER.debug(f"can't find {entity_id}")
            return

        location = call.data.get(CONF_LOCATION, None)
        coords = call.data.get(CONF_GPS, None)
        if location is not None:
            entity.move_to_location(location)
        elif coords is not None:
            entity.move_to_coords(coords)
        else:
            _LOGGER.debug(f"not moving {entity_id}")

