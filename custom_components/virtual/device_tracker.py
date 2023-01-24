"""
This component provides support for a virtual device tracker.

"""

import logging
import json

from homeassistant.const import CONF_DEVICES, STATE_HOME
from homeassistant.components.device_tracker import DOMAIN
from homeassistant.helpers.event import async_track_state_change_event
from .const import (
    COMPONENT_DOMAIN,
    CONF_NAME,
    CONF_PERSISTENT,
    DEFAULT_PERSISTENT,
)

_LOGGER = logging.getLogger(__name__)

CONF_LOCATION = 'location'
DEFAULT_LOCATION = 'home'

DEPENDENCIES = [COMPONENT_DOMAIN]
STATE_FILE = "/config/.storage/virtual.restore_state"

tracker_states = {}


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

    # Read in the last known states.
    old_tracker_states = {}
    try:
        with open(STATE_FILE, 'r') as f:
            old_tracker_states = json.load(f)
    except:
        pass

    new_tracker_states = {}
    for device in config[CONF_DEVICES]:
        if not isinstance(device, dict):
            device = {
                CONF_NAME: device,
            }

        name = device.get(CONF_NAME, 'unknown')
        location = device.get(CONF_LOCATION, DEFAULT_LOCATION)
        peristent = device.get(CONF_PERSISTENT, DEFAULT_PERSISTENT)
        entity_id = f"{DOMAIN}.{name}"

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
