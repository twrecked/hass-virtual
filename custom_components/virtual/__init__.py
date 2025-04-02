"""
This component provides support for virtual components.

"""

import logging
import voluptuous as vol
import asyncio

import homeassistant.helpers.config_validation as cv
import homeassistant.helpers.device_registry as dr
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.issue_registry import (
    async_create_issue,
    IssueSeverity
)
from homeassistant.helpers.service import verify_domain_control
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.const import ATTR_ENTITY_ID, CONF_SOURCE, Platform
from homeassistant.core import (
    DOMAIN as HOMEASSISTANT_DOMAIN,
    HomeAssistant,
    callback
)
from homeassistant.exceptions import HomeAssistantError

from .const import *
from .cfg import BlendedCfg, UpgradeCfg


__version__ = '0.9.2'

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
        COMPONENT_DOMAIN: vol.Schema({
            vol.Optional(CONF_YAML_CONFIG, default=False): cv.boolean,
        }),
    },
    extra=vol.ALLOW_EXTRA,
)

SERVICE_AVAILABILE = 'set_available'
SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required('value'): cv.boolean,
})

VIRTUAL_PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.COVER,
    Platform.DEVICE_TRACKER,
    Platform.FAN,
    Platform.LIGHT,
    Platform.LOCK,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.VALVE
]


def str_to_bool(value) -> bool:
    value = value.lower()
    if value in ["y", "yes", "t", "true", "on", "1"]:
        return True
    if value in ["n", "no", "f", "false", "off", "0"]:
        return False
    raise ValueError


async def async_setup(hass, config):
    """Set up a virtual components.

    This uses the old mechanism and has to be enabled with 'yaml_config: True'
    """

    # Set up hass data if necessary
    if COMPONENT_DOMAIN not in hass.data:
        hass.data[COMPONENT_DOMAIN] = {}
        hass.data[COMPONENT_SERVICES] = {}
        hass.data[COMPONENT_CONFIG] = {}

    # See if yaml support was enabled.
    if not config.get(COMPONENT_DOMAIN, {}).get(CONF_YAML_CONFIG, False):

        # New style. We import old config if needed.
        _LOGGER.debug("setting up new virtual components")
        hass.data[COMPONENT_CONFIG][CONF_YAML_CONFIG] = False

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

            async_create_issue(
                hass,
                HOMEASSISTANT_DOMAIN,
                f"deprecated_yaml_{COMPONENT_DOMAIN}",
                is_fixable=False,
                issue_domain=COMPONENT_DOMAIN,
                severity=IssueSeverity.WARNING,
                translation_key="deprecated_yaml",
                translation_placeholders={
                    "domain": COMPONENT_DOMAIN,
                    "integration_title": "Virtual",
                },
            )

        else:
            _LOGGER.debug('ignoring a YAML setup')

    else:

        # Original style. We just use the entities as now.
        _LOGGER.debug("setting up old virtual components")
        hass.data[COMPONENT_CONFIG][CONF_YAML_CONFIG] = True

        @verify_domain_control(hass, COMPONENT_DOMAIN)
        async def async_virtual_service_set_available(call) -> None:
            """Call virtual service handler."""
            _LOGGER.info("{} service called".format(call.service))
            await async_virtual_set_availability_service(hass, call)

        hass.services.async_register(COMPONENT_DOMAIN, SERVICE_AVAILABILE, async_virtual_service_set_available)

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

    # Set up hass data if necessary
    if COMPONENT_DOMAIN not in hass.data:
        hass.data[COMPONENT_DOMAIN] = {}
        hass.data[COMPONENT_SERVICES] = {}
        hass.data[COMPONENT_CONFIG] = {}

    # Get the config.
    _LOGGER.debug(f"creating new cfg")
    vcfg = BlendedCfg(hass, entry.data)
    await vcfg.async_load()

    # create the devices.
    _LOGGER.debug("creating the devices")
    for device in vcfg.devices:
        _LOGGER.debug(f"creating-device={device}")
        await _async_get_or_create_virtual_device_in_registry(hass, entry, device)
    await asyncio.sleep(1)

    # Delete orphaned devices.
    for switch, device in vcfg.orphaned_entities.items():
        _LOGGER.debug(f"deleting {switch}/{device}")
        await _async_delete_virtual_device_from_registry(hass, entry, device)

    # Update the component data.
    hass.data[COMPONENT_DOMAIN].update({
        entry.data[ATTR_GROUP_NAME]: {
            ATTR_ENTITIES: vcfg.entities,
            ATTR_DEVICES: vcfg.devices,
            ATTR_FILE_NAME: entry.data[ATTR_FILE_NAME]
        }
    })
    _LOGGER.debug(f"update hass data {hass.data[COMPONENT_DOMAIN]}")

    # Create the entities.
    _LOGGER.debug("creating the entities")
    await hass.config_entries.async_forward_entry_setups(entry, VIRTUAL_PLATFORMS)

    # Install service handler.
    @verify_domain_control(hass, COMPONENT_DOMAIN)
    async def async_virtual_service_set_available(call) -> None:
        """Call virtual service handler."""
        _LOGGER.info(f"{call.service} service called")
        await async_virtual_set_availability_service(hass, call)

    if not hasattr(hass.data[COMPONENT_SERVICES], COMPONENT_DOMAIN):
        _LOGGER.debug("installing handlers")
        hass.data[COMPONENT_SERVICES][COMPONENT_DOMAIN] = 'installed'
        hass.services.async_register(COMPONENT_DOMAIN, SERVICE_AVAILABILE,
                                     async_virtual_service_set_available, schema=SERVICE_SCHEMA)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug(f"unloading virtual group {entry.data[ATTR_GROUP_NAME]}")
    # _LOGGER.debug(f"before hass={hass.data[COMPONENT_DOMAIN]}")
    unload_ok = await hass.config_entries.async_unload_platforms(entry, VIRTUAL_PLATFORMS)
    if unload_ok:
        _LOGGER.debug("unloaded ok")
        hass.data[COMPONENT_DOMAIN].pop(entry.data[ATTR_GROUP_NAME])
        # _LOGGER.debug(f"ocfg={ocfg}")
    # _LOGGER.debug(f"after hass={hass.data[COMPONENT_DOMAIN]}")

    return unload_ok


def get_entity_configs(hass, group_name, domain):
    return hass.data.get(COMPONENT_DOMAIN, {}).get(group_name, {}).get(ATTR_ENTITIES, {}).get(domain, [])


def get_entity_from_domain(hass, domain, entity_id):
    component = hass.data.get(domain)
    if component is None:
        raise HomeAssistantError("{} component not set up".format(domain))

    entity = component.get_entity(entity_id)
    if entity is None:
        raise HomeAssistantError("{} not found".format(entity_id))

    return entity


async def async_virtual_set_availability_service(hass, call):
    value = call.data['value']
    if type(value) is not bool:
        value = str_to_bool(value)

    for entity_id in call.data['entity_id']:
        domain = entity_id.split(".")[0]
        _LOGGER.info("{} set_avilable(value={})".format(entity_id, value))
        get_entity_from_domain(hass, domain, entity_id).set_available(value)


async def _async_get_or_create_virtual_device_in_registry(
        hass: HomeAssistant, entry: ConfigEntry, device
) -> None:
    registry = dr.async_get(hass)
    registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(COMPONENT_DOMAIN, device[ATTR_DEVICE_ID])},
        manufacturer=COMPONENT_MANUFACTURER,
        model=COMPONENT_MODEL,
        name=device[CONF_NAME],
        sw_version=__version__
    )


async def _async_delete_virtual_device_from_registry(
        hass: HomeAssistant, _entry: ConfigEntry, device
) -> None:
    registery = dr.async_get(hass)
    device_in_registry = registery.async_get_device(
        identifiers={(COMPONENT_DOMAIN, device[ATTR_DEVICE_ID])},
    )
    if device_in_registry:
        _LOGGER.debug(f"found something to delete! {device_in_registry.id}")
        registery.async_remove_device(device_in_registry.id)
    else:
        _LOGGER.info(f"have orphaned device in meta {device[ATTR_DEVICE_ID]}")
