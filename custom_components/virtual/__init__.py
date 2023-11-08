"""
This component provides support for virtual components.

"""

import logging
import voluptuous as vol
from distutils import util
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.service import verify_domain_control
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.exceptions import HomeAssistantError

from .const import (
    COMPONENT_DOMAIN,
    COMPONENT_SERVICES
)

__version__ = '0.8.0.1'

_LOGGER = logging.getLogger(__name__)

SERVICE_AVAILABILE = 'set_available'
SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required('value'): cv.boolean,
})


async def async_setup(hass, config):
    """Set up a virtual components."""

    hass.data[COMPONENT_SERVICES] = {}
    _LOGGER.debug('setup')

    @verify_domain_control(hass, COMPONENT_DOMAIN)
    async def async_virtual_service_set_available(call) -> None:
        """Call virtual service handler."""
        _LOGGER.info("{} service called".format(call.service))
        await async_virtual_set_availability_service(hass, call)

    hass.services.async_register(COMPONENT_DOMAIN, SERVICE_AVAILABILE, async_virtual_service_set_available)

    return True


def get_entity_from_domain(hass, domain, entity_id):
    component = hass.data.get(domain)
    if component is None:
        raise HomeAssistantError("{} component not set up".format(domain))

    entity = component.get_entity(entity_id)
    if entity is None:
        raise HomeAssistantError("{} not found".format(entity_id))

    return entity


async def async_virtual_set_availability_service(hass, call):
    entity_id = call.data['entity_id']
    value = call.data['value']

    if not type(value)==bool:
        value = bool(util.strtobool(value))
    domain = entity_id.split(".")[0]
    _LOGGER.info("{} set_avilable(value={})".format(entity_id, value))
    get_entity_from_domain(hass, domain, entity_id).set_available(value)