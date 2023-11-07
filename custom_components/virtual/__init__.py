"""
This component provides support for virtual components.

"""

import logging
import voluptuous as vol
from distutils import util

import homeassistant.helpers.config_validation as cv
import homeassistant.helpers.device_registry as dr
from homeassistant.helpers.service import verify_domain_control
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.const import ATTR_ENTITY_ID, CONF_SOURCE, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .const import *
from .cfg import BlendedCfg, UpgradeCfg


__version__ = '0.9.0a1'

_LOGGER = logging.getLogger(__name__)

SERVICE_AVAILABILE = 'set_available'
SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required('value'): cv.boolean,
})

VIRTUAL_PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH
]
ALL_VIRTUAL_PLATFORMS = [
    Platform.BINARY_SENSOR, Platform.SENSOR,
    Platform.FAN, Platform.LIGHT,
    Platform.LOCK, Platform.SWITCH, Platform.DEVICE_TRACKER
]


def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up a virtual component.
    """

    hass.data.setdefault(COMPONENT_DOMAIN, {})

    # See if we have already imported the data. If we haven't then do it now.
    config_entry = _async_find_matching_config_entry(hass)
    if not config_entry:
        _LOGGER.debug('importing a YAML setup')
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                COMPONENT_DOMAIN,
                context={CONF_SOURCE: SOURCE_IMPORT},
                data=config
            )
        )
        return True

    _LOGGER.debug('ignoring a YAML setup')
    return True


@callback
def _async_find_matching_config_entry(hass):
    """ If we have anything in config_entries for virtual we consider it
    configured and will ignore the YAML.
    """
    for entry in hass.config_entries.async_entries(COMPONENT_DOMAIN):
        return entry


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug(f'async setup {entry.data}')

    # Install the config.
    vcfg = BlendedCfg(entry.data)
    hass.data[COMPONENT_DOMAIN] = vcfg.entities
    hass.data[COMPONENT_SERVICES] = {}
    _LOGGER.debug(f"update hass data {hass.data[COMPONENT_DOMAIN]}")

    # create the devices.
    _LOGGER.debug("creating the devices")
    for device in vcfg.devices:
        await _async_get_or_create_momentary_device_in_registry(hass, entry, device)

    # Create the entities.
    _LOGGER.debug("creating the entities")
    await hass.config_entries.async_forward_entry_setups(entry, VIRTUAL_PLATFORMS)

    # Install service handler.
    @verify_domain_control(hass, COMPONENT_DOMAIN)
    async def async_virtual_service_set_available(call) -> None:
        """Call virtual service handler."""
        _LOGGER.info(f"{call.service} service called")
        await async_virtual_set_availability_service(hass, call)

    _LOGGER.debug("installing service handler")
    hass.services.async_register(COMPONENT_DOMAIN, SERVICE_AVAILABILE, async_virtual_service_set_available)

    return True


async def async_setup2(hass, config):
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


async def _async_get_or_create_momentary_device_in_registry(
        hass: HomeAssistant, entry: ConfigEntry, device
) -> None:
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(COMPONENT_DOMAIN, device[ATTR_DEVICE_ID])},
        manufacturer=COMPONENT_MANUFACTURER,
        model=COMPONENT_MODEL,
        name=device[CONF_NAME],
        sw_version=__version__
    )


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