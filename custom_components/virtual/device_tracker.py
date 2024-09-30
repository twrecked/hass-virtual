"""
This component provides support for a virtual device tracker.

"""

import aiofiles
import logging
import voluptuous as vol
import json
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
    ATTR_LONGITUDE,
    CONF_DEVICES
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.event import async_track_state_change_event

from . import get_entity_from_domain, get_entity_configs
from .const import *
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

CONF_LOCATION = 'location'
CONF_GPS = 'gps'
CONF_GPS_ACCURACY = 'gps_accuracy'
DEFAULT_DEVICE_TRACKER_VALUE = 'home'
DEFAULT_LOCATION = 'home'

STATE_FILE = "/config/.storage/virtual.restore_state"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICES, default=[]): cv.ensure_list
})

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
    vol.Optional(CONF_GPS_ACCURACY): cv.positive_int,
})

tracker_states = {}

async def _async_load_json(file_name):
    try:
        async with aiofiles.open(file_name, 'r') as state_file:
            contents = await state_file.read()
            return json.loads(contents)
    except Exception as e:
        return {}


def _write_state():
    global tracker_states
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(tracker_states, f)
    except:
        pass

def _state_changed(event):
    entity_id = event.data.get('entity_id', None)
    new_state = event.data.get('new_state', None)
    if entity_id is None or new_state is None:
        _LOGGER.info(f'state changed error')
        return

    # update database
    _LOGGER.info(f"moving {entity_id} to {new_state.state}")
    global tracker_states
    tracker_states[entity_id] = new_state.state
    _write_state()


def _shutting_down(event):
    _LOGGER.info(f'shutting down {event}')
    _write_state()


async def async_setup_scanner(hass, config, async_see, _discovery_info=None):
    """Set up the virtual tracker."""

    if not hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        return True
    _LOGGER.debug("setting up old device trackers...")

    # Read in the last known states.
    old_tracker_states = await _async_load_json(STATE_FILE)

    new_tracker_states = {}
    for device in config[CONF_DEVICES]:
        if not isinstance(device, dict):
            device = {
                CONF_NAME: device,
            }

        name = device.get(CONF_NAME, 'unknown')
        location = device.get(CONF_LOCATION, DEFAULT_LOCATION)
        peristent = device.get(CONF_PERSISTENT, DEFAULT_PERSISTENT)
        entity_id = f"{PLATFORM_DOMAIN}.{name}"

        if peristent:
            location = old_tracker_states.get(entity_id, location)
            new_tracker_states[entity_id] = location
            _LOGGER.info(f"setting persistent {entity_id} to {location}")
        else:
            _LOGGER.info(f"setting ephemeral {entity_id} to {location}")

        see_args = {
            "dev_id": name,
            "source_type": COMPONENT_DOMAIN,
            "location_name": location,
        }
        hass.async_create_task(async_see(**see_args))

    # Start listening if there are persistent entities.
    global tracker_states
    tracker_states = new_tracker_states
    if tracker_states:
        async_track_state_change_event(hass, tracker_states.keys(), _state_changed)
        hass.bus.async_listen("homeassistant_stop", _shutting_down)
    else:
        _write_state()

    return True


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
        self._gps_accuracy = 0

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
        if self._coords:
            return "gps"
        return "virtual"

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return self._coords.get(ATTR_LATITUDE, None)

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return self._coords.get(ATTR_LONGITUDE, None)

    @property
    def location_accuracy(self) -> int:
        return self._gps_accuracy

    def move_to_location(self, new_location):
        _LOGGER.debug(f"{self._attr_name} moving to {new_location}")
        self._location = new_location
        self._coords = {}
        self.async_schedule_update_ha_state()

    def move_to_coords(self, new_coords, accuracy):
        _LOGGER.debug(f"{self._attr_name} moving via GPS to {new_coords} ({accuracy}m)")
        self._location = None
        self._coords = new_coords
        self._gps_accuracy = accuracy
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
            accuracy = call.data.get(CONF_GPS_ACCURACY, 0)
            entity.move_to_coords(coords, accuracy)
        else:
            _LOGGER.debug(f"not moving {entity_id}")

