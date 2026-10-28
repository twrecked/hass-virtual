"""This component provides support for virtual components."""
from __future__ import annotations

import logging
import secrets
from typing import Any
from aiohttp import web
import voluptuous as vol
import yaml

from homeassistant.components import webhook
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
    ServiceCall,
    callback
)
from homeassistant.exceptions import HomeAssistantError

from .const import (
    ATTR_DEVICE_ID,
    ATTR_DEVICES,
    ATTR_ENTITIES,
    ATTR_FILE_NAME,
    ATTR_GROUP_NAME,
    ATTR_VALUE,
    COMPONENT_CONFIG,
    COMPONENT_DOMAIN,
    COMPONENT_MANUFACTURER,
    COMPONENT_MODEL,
    COMPONENT_SERVICES,
    CONF_NAME,
    CONF_YAML_CONFIG,
    SERVICE_SET_BATTERY_SOC,
    SERVICE_SET_SOLAR_POWER,
)
from .cfg import BlendedCfg, UpgradeCfg
from .simulations import SimulationManager


__version__ = '0.10.0-alpha.5'

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
        COMPONENT_DOMAIN: vol.Schema({
            vol.Optional(CONF_YAML_CONFIG, default=False): cv.boolean,
        }),
    },
    extra=vol.ALLOW_EXTRA,
)

SERVICE_AVAILABLE = 'set_available'
SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required('value'): cv.boolean,
})

SERVICE_BATTERY_SOC_SCHEMA = vol.Schema({
    vol.Required(ATTR_VALUE): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=100.0)),
    vol.Optional(CONF_NAME): cv.string,
})

SERVICE_SOLAR_POWER_SCHEMA = vol.Schema({
    vol.Required(ATTR_VALUE): cv.string,
    vol.Optional(CONF_NAME): cv.string,
})

SERVICE_SIM_SPEED_SCHEMA = vol.Schema({
    vol.Required("speed"): vol.Coerce(float),
    vol.Optional(CONF_NAME): cv.string,
})

VIRTUAL_PLATFORMS = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CAMERA,
    Platform.CLIMATE,
    Platform.COVER,
    Platform.DEVICE_TRACKER,
    Platform.FAN,
    Platform.LIGHT,
    Platform.LOCK,
    Platform.MEDIA_PLAYER,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TEXT,
    Platform.VALVE,
]


def str_to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    val = str(value).lower()
    if val in ["y", "yes", "t", "true", "on", "1"]:
        return True
    if val in ["n", "no", "f", "false", "off", "0"]:
        return False
    raise ValueError(f"Cannot convert {value} to boolean")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
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

        @verify_domain_control(COMPONENT_DOMAIN)
        async def async_virtual_service_set_available(call) -> None:
            """Call virtual service handler."""
            _LOGGER.info(f"{call.service} service called")
            await async_virtual_set_availability_service(hass, call)

        hass.services.async_register(COMPONENT_DOMAIN, SERVICE_AVAILABLE, async_virtual_service_set_available)

    return True


@callback
def _async_find_matching_config_entry(hass: HomeAssistant) -> ConfigEntry | None:
    """ If we have anything in config_entries for virtual we consider it
    configured and will ignore the YAML.
    """
    for entry in hass.config_entries.async_entries(COMPONENT_DOMAIN):
        return entry
    return None


async def _async_handle_builder_webhook(
    hass: HomeAssistant, webhook_id: str, request: web.Request, entry: ConfigEntry
) -> web.Response:
    """Handle incoming YAML save from Virtual Device Editor."""
    token = request.query.get("token") or request.headers.get("X-Auth-Token")
    expected_token = (
        hass.data.get(f"{COMPONENT_DOMAIN}_webhooks", {})
        .get(entry.entry_id, {})
        .get("webhook_token")
    )
    if not token or token != expected_token:
        _LOGGER.warning("Invalid token received on virtual builder webhook")
        return web.Response(text="Invalid token", status=403)

    body = await request.text()
    if not body:
        return web.Response(text="Empty body", status=400)

    try:
        parsed = yaml.safe_load(body)
        if not isinstance(parsed, dict):
            return web.Response(text="YAML root must be a dictionary", status=400)
    except Exception as err:
        _LOGGER.warning("Invalid YAML received on builder webhook: %s", err)
        return web.Response(text=f"Invalid YAML: {err}", status=400)

    file_name = entry.data.get(ATTR_FILE_NAME)
    if not file_name:
        return web.Response(text="No file_name configured for entry", status=500)

    def _write_yaml() -> None:
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(body)

    await hass.async_add_executor_job(_write_yaml)
    _LOGGER.info(f"Successfully updated {file_name} from Virtual Device Editor")

    # Reload config entry asynchronously to pick up changes
    hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))
    return web.Response(text="OK", status=200)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug(f'async setup {entry.data}')

    # Set up hass data if necessary
    if COMPONENT_DOMAIN not in hass.data:
        hass.data[COMPONENT_DOMAIN] = {}
        hass.data[COMPONENT_SERVICES] = {}
        hass.data[COMPONENT_CONFIG] = {}

    # Register builder webhook
    webhook_id = f"virtual_{entry.entry_id}"
    token = secrets.token_hex(16)
    webhooks_data = hass.data.setdefault(f"{COMPONENT_DOMAIN}_webhooks", {})
    webhooks_data[entry.entry_id] = {
        "webhook_token": token,
        "webhook_id": webhook_id,
    }

    async def _handle_webhook(hass_instance: HomeAssistant, wh_id: str, req: web.Request) -> web.Response:
        return await _async_handle_builder_webhook(hass_instance, wh_id, req, entry)

    try:
        webhook.async_register(
            hass,
            COMPONENT_DOMAIN,
            f"Virtual Builder ({entry.data.get(ATTR_GROUP_NAME, 'group')})",
            webhook_id,
            _handle_webhook,
            allowed_methods=["POST"],
        )
    except ValueError:
        pass

    # Get the config.
    _LOGGER.debug(f"creating new cfg")
    vcfg = BlendedCfg(hass, entry.data)
    await vcfg.async_load()

    # create the devices.
    _LOGGER.debug("creating the devices")
    for device in vcfg.devices:
        _LOGGER.debug(f"creating-device={device}")
        await _async_get_or_create_virtual_device_in_registry(hass, entry, device)

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

    # Start any configured simulations
    sim_manager: SimulationManager = hass.data.get("virtual_simulation_manager")
    if sim_manager and vcfg.simulations:
        _LOGGER.debug("setting up virtual simulations")
        await sim_manager.async_setup_simulations(entry, vcfg.simulations)

    # Install service handler.
    @verify_domain_control(COMPONENT_DOMAIN)
    async def async_virtual_service_set_available(call) -> None:
        """Call virtual service handler."""
        _LOGGER.info(f"{call.service} service called")
        await async_virtual_set_availability_service(hass, call)

    if COMPONENT_DOMAIN not in hass.data[COMPONENT_SERVICES]:
        _LOGGER.debug("installing handlers")
        hass.data[COMPONENT_SERVICES][COMPONENT_DOMAIN] = 'installed'
        hass.services.async_register(COMPONENT_DOMAIN, SERVICE_AVAILABLE,
                                     async_virtual_service_set_available, schema=SERVICE_SCHEMA)

        @verify_domain_control(COMPONENT_DOMAIN)
        async def async_virtual_service_set_battery_soc(call) -> None:
            sm: SimulationManager = hass.data.get("virtual_simulation_manager")
            if sm:
                sm.set_battery_soc(float(call.data[ATTR_VALUE]), call.data.get(CONF_NAME))

        @verify_domain_control(COMPONENT_DOMAIN)
        async def async_virtual_service_set_solar_power(call) -> None:
            sm: SimulationManager = hass.data.get("virtual_simulation_manager")
            if sm:
                sm.set_solar_power(call.data[ATTR_VALUE], call.data.get(CONF_NAME))

        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_SET_BATTERY_SOC, async_virtual_service_set_battery_soc, schema=SERVICE_BATTERY_SOC_SCHEMA
        )
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_SET_SOLAR_POWER, async_virtual_service_set_solar_power, schema=SERVICE_SOLAR_POWER_SCHEMA
        )

        @verify_domain_control(COMPONENT_DOMAIN)
        async def async_virtual_service_set_sim_speed(call) -> None:
            sm: SimulationManager = hass.data.get("virtual_simulation_manager")
            if sm:
                sm.set_sim_speed(float(call.data["speed"]), call.data.get(CONF_NAME))

        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_SET_SIM_SPEED, async_virtual_service_set_sim_speed, schema=SERVICE_SIM_SPEED_SCHEMA
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug(f"unloading virtual group {entry.data[ATTR_GROUP_NAME]}")
    # _LOGGER.debug(f"before hass={hass.data[COMPONENT_DOMAIN]}")
    unload_ok = await hass.config_entries.async_unload_platforms(entry, VIRTUAL_PLATFORMS)
    if unload_ok:
        sm: SimulationManager = hass.data.get("virtual_simulation_manager")
        if sm:
            await sm.async_unload_simulations(entry)
        _LOGGER.debug("unloaded ok")
        hass.data[COMPONENT_DOMAIN].pop(entry.data[ATTR_GROUP_NAME], None)
        # Unregister webhook
        webhook_id = f"virtual_{entry.entry_id}"
        try:
            webhook.async_unregister(hass, webhook_id)
        except Exception:
            pass
        hass.data.get(f"{COMPONENT_DOMAIN}_webhooks", {}).pop(entry.entry_id, None)

    return unload_ok


def get_entity_configs(hass: HomeAssistant, group_name: str, domain: str) -> list[dict[str, Any]]:
    return hass.data.get(COMPONENT_DOMAIN, {}).get(group_name, {}).get(ATTR_ENTITIES, {}).get(domain, [])


def get_entity_from_domain(hass: HomeAssistant, domain: str, entity_id: str) -> Any:
    component = hass.data.get(domain)
    if component is None:
        raise HomeAssistantError(f"{domain} component not set up")

    entity = component.get_entity(entity_id)
    if entity is None:
        raise HomeAssistantError(f"{entity_id} not found")

    return entity


async def async_virtual_set_availability_service(hass: HomeAssistant, call: ServiceCall) -> None:
    value = call.data['value']
    if not isinstance(value, bool):
        value = str_to_bool(value)

    for entity_id in call.data['entity_id']:
        domain = entity_id.split(".")[0]
        _LOGGER.info(f"{entity_id} set_available(value={value})")
        get_entity_from_domain(hass, domain, entity_id).set_available(value)


async def _async_get_or_create_virtual_device_in_registry(
        hass: HomeAssistant, entry: ConfigEntry, device: dict[str, Any]
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
        hass: HomeAssistant, _entry: ConfigEntry, device: dict[str, Any]
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
