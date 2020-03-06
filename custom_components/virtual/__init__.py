"""
This component provides support for virtual components.

"""

import logging


__version__ = '0.1'

_LOGGER = logging.getLogger(__name__)

COMPONENT_DOMAIN = 'virtual'
COMPONENT_SERVICES = 'virtual-services'


def setup(hass, config):
    """Set up a virtual components."""

    hass.data[COMPONENT_SERVICES] = {}
    _LOGGER.debug('setup')
    return True
