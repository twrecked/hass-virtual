"""
This component provides support for a virtual device tracker.

"""

import logging
import json

from homeassistant.const import CONF_DEVICES, STATE_HOME
from homeassistant.components.device_tracker import DOMAIN
from homeassistant.helpers.event import async_track_state_change_event
from . import COMPONENT_DOMAIN

_LOGGER = logging.getLogger(__name__)

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

    # parse out the last known state
    global tracker_states
    try:
        with open(STATE_FILE, 'r') as f:
            tracker_states = json.load(f)
    except:
        pass

    for device in config[CONF_DEVICES]:
        entity_id = f"{DOMAIN}.{device}"
        state = tracker_states.get(entity_id, STATE_HOME)
        tracker_states[entity_id] = state
        _LOGGER.info(f"setting {entity_id} to {state}")

        see_args = {
            "dev_id": device,
            "source_type": COMPONENT_DOMAIN,
            "location_name": state,
        }
        hass.async_create_task(async_see(**see_args))

    async_track_state_change_event(hass, tracker_states.keys(), _state_changed)
    hass.bus.async_listen("homeassistant_stop", _shutting_down)

    return True
