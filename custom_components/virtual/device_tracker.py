"""
This component provides support for a virtual device tracker.

"""

import logging
import pprint

import voluptuous as vol

from homeassistant.const import CONF_DEVICES, STATE_HOME 
from homeassistant.core import callback
from . import COMPONENT_DOMAIN

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

async def async_setup_scanner(hass, config, async_see, discovery_info=None):
    """Set up the virtual tracker."""

    # Move all configured devices home
    for dev_id in config[CONF_DEVICES]:
        _LOGGER.info("moving {} home".format(dev_id))
        see_args = {"dev_id": dev_id, "source_type": COMPONENT_DOMAIN, "location_name": STATE_HOME}
        hass.async_create_task(async_see(**see_args))

    return True

