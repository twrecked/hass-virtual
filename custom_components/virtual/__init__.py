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


def get_entity_from_domain(hass, domain, entity_id):
    component = hass.data.get(domain)
    if component is None:
        raise HomeAssistantError("{} component not set up".format(domain))

    entity = component.get_entity(entity_id)
    if entity is None:
        raise HomeAssistantError("{} not found".format(entity_id))

    return entity
