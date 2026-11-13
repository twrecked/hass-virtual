"""
Handles file-based virtual device configuration and coordination.

Because virtual devices require flexible, detailed configuration (durations, power simulation,
battery lifespans, sensor linkage), devices are organized in YAML files linked to an integration entry.

Key components:
- `BlendedCfg`: Acts as a virtual device coordinator. Loads YAML device definitions,
  manages entity identity and ADR-0007 naming, reconciles state with Home Assistant's
  device and entity registries, and supplies structured payloads to platform setup.
- `UpgradeCfg`: Helper class to import legacy pre-v0.9 configuration into the modern file layout.
"""
from __future__ import annotations

import asyncio
import copy
import logging
import json
import voluptuous as vol
import uuid
from datetime import timedelta
from typing import Any

from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_PLATFORM,
    CONF_UNIT_OF_MEASUREMENT,
    Platform
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.util import slugify
from homeassistant.util.yaml import parse_yaml, dump

from .const import (
    ATTR_DEVICES,
    ATTR_DEVICE_ID,
    ATTR_FILE_NAME,
    ATTR_GROUP_NAME,
    ATTR_UNIQUE_ID,
    ATTR_VERSION,
    COMPONENT_DOMAIN,
    CONF_CLASS,
    CONF_NAME,
    CONF_SIMULATIONS,
    IMPORTED_GROUP_NAME,
    default_config_file,
    default_meta_file,
)
from .entity import virtual_schema


_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_DEFAULT_INITIAL_VALUE = 'off'
BINARY_SENSOR_SCHEMA = vol.Schema(virtual_schema(BINARY_SENSOR_DEFAULT_INITIAL_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
}))

SENSOR_DEFAULT_INITIAL_VALUE = '0'
SENSOR_SCHEMA = vol.Schema(virtual_schema(SENSOR_DEFAULT_INITIAL_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=""): cv.string,
}))

_meta_lock = asyncio.Lock()


def _fix_value(value):
    """ If needed, convert value into a type that can be stored in yaml.
    """
    if isinstance(value, timedelta):
        return max(value.seconds, 1)
    return value


def _read_file(file_name: str) -> str:
    with open(file_name, "r", encoding="utf-8") as f:
        return f.read()


def _write_file(file_name: str, content: str) -> None:
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(content)


async def _async_load_json(hass, file_name: str):
    _LOGGER.debug("loading JSON %s", file_name)
    try:
        content = await hass.async_add_executor_job(_read_file, file_name)
        return json.loads(content)
    except Exception as e:
        _LOGGER.debug("Error loading JSON %s: %s", file_name, e)
        return {}


async def _async_save_json(hass, file_name: str, data):
    _LOGGER.debug("saving JSON %s", file_name)
    try:
        content = json.dumps(data, indent=4)
        await hass.async_add_executor_job(_write_file, file_name, content)
    except Exception as e:
        _LOGGER.debug("Error saving JSON %s: %s", file_name, e)


async def _async_load_yaml(hass, file_name: str):
    _LOGGER.debug("loading YAML %s", file_name)
    try:
        content = await hass.async_add_executor_job(_read_file, file_name)
        return parse_yaml(content)
    except Exception as e:
        _LOGGER.debug("Error loading YAML %s: %s", file_name, e)
        return {}


async def _async_save_yaml(hass, file_name: str, data):
    _LOGGER.debug("saving YAML %s", file_name)
    try:
        content = dump(data)
        await hass.async_add_executor_job(_write_file, file_name, content)
    except Exception as e:
        _LOGGER.debug("Error saving YAML %s: %s", file_name, e)


async def _load_meta_data(hass, group_name: str):
    """Read in meta data for a particular group.
    """
    async with _meta_lock:
        data = await _async_load_json(hass, default_meta_file(hass))
        return data.get(ATTR_DEVICES, {}).get(group_name, {})


async def _save_meta_data(hass, group_name, meta_data):
    """Save meta data for a particular group name.
    """
    async with _meta_lock:

        # Read in current meta data
        devices = await _async_load_json(hass, default_meta_file(hass))
        devices = devices.get(ATTR_DEVICES, {})

        # Update (or add) the group piece.
        _LOGGER.debug(f"meta before {devices}")
        devices.update({
            group_name: meta_data
        })
        _LOGGER.debug(f"meta after {devices}")

        # Write it back out.
        await _async_save_json(hass, default_meta_file(hass), {
            ATTR_VERSION: 1,
            ATTR_DEVICES: devices
        })


async def _delete_meta_data(hass, group_name):
    """Save meta data for a particular group name.
    """
    async with _meta_lock:

        # Read in current meta data
        devices = await _async_load_json(hass, default_meta_file(hass))
        devices = devices.get(ATTR_DEVICES, {})

        # Delete the group piece.
        _LOGGER.debug(f"meta before {devices}")
        devices.pop(group_name, None)
        _LOGGER.debug(f"meta after {devices}")

        # Write it back out.
        await _async_save_json(hass, default_meta_file(hass), {
            ATTR_VERSION: 1,
            ATTR_DEVICES: devices
        })


async def _save_user_data(hass, file_name, devices, simulations=None):
    payload = {
        ATTR_VERSION: 1,
        ATTR_DEVICES: devices
    }
    if simulations:
        payload[CONF_SIMULATIONS] = simulations
    await _async_save_yaml(hass, file_name, payload)


async def _load_user_data(hass, file_name):
    raw_data = await _async_load_yaml(hass, file_name)
    if isinstance(raw_data, dict):
        simulations = raw_data.get(CONF_SIMULATIONS, [])
        devices = raw_data.get(ATTR_DEVICES, raw_data)
        if ATTR_DEVICES not in raw_data:
            devices = {k: v for k, v in raw_data.items() if k not in (ATTR_VERSION, CONF_SIMULATIONS)}
        return devices, simulations
    return {}, []


def _fix_config(config):
    """Find and return the virtual entries from any platform config.
    """
    _LOGGER.debug(f"config={config}")
    entries = []
    for entry in config:
        if entry[CONF_PLATFORM] == COMPONENT_DOMAIN:
            entry = copy.deepcopy(entry)
            entry.pop(CONF_PLATFORM)
            entries.append(entry)
    return entries


def _upgrade_name(name: str):
    """We're making the non virtual prefix the default so this flips the naming.
    """
    if name.startswith("!"):
        return name[1:]
    elif name.startswith("virtual_"):
        return f"+{name[8:]}"
    else:
        return f"+{name}"


def _parse_old_config(devices, configs, platform):
    """Parse out config into different devices.

    We do several things:
    - insert a platform key/value, i.e, this this is a switch
    - fix the naming
    - create and store the entity under a device, for imported config there
      will only be one entity per device
    """
    for config in configs:
        if not isinstance(config, dict):
            _LOGGER.debug(f"not dictionary={config}")
            continue
        if config[CONF_PLATFORM] != COMPONENT_DOMAIN:
            continue

        # Copy and fix up config.
        config = copy.deepcopy(config)
        config[CONF_PLATFORM] = platform
        config[CONF_NAME] = _upgrade_name(config[CONF_NAME])

        # Fix values that need to be saved in yaml
        config = {k: _fix_value(v) for k, v in config.items()}

        # Insert or create a device for it.
        if config[CONF_NAME] in devices:
            devices[config[CONF_NAME]].append(config)
        else:
            devices[config[CONF_NAME]] = [config]

    return devices


def _make_original_unique_id(name):
    if name.startswith("+"):
        return slugify(name[1:])
    else:
        return slugify(name)


def _make_name(name):
    if name.startswith("+"):
        return name[1:]
    return name


def _make_entity_id(platform, name):
    if name.startswith("+"):
        return f'{platform}.{COMPONENT_DOMAIN}_{slugify(name[1:])}'
    else:
        return f'{platform}.{slugify(name)}'


def _make_unique_id():
    return f'{uuid.uuid4()}.{COMPONENT_DOMAIN}'


def _make_suffix(platform, device_class):
    """Make a suitable suffix for an unnamed entity."""
    if device_class is not None:
        return f"{device_class}"
    return f"{platform}"


class BlendedCfg:
    """Virtual device controller and configuration manager.

    Acts as an in-memory hardware bridge and coordinator for a virtual device file.
    Loads and parses YAML device definitions, determines primary and sub-entity
    naming (ADR-0007), resolves entity IDs and unique IDs against Home Assistant's
    native registries, and supplies structured device and entity payloads to setup.
    """

    def __init__(self, hass: HomeAssistant, flow_data: dict[str, Any], entry_id: str | None = None):
        self._hass = hass
        self._group_name = flow_data[ATTR_GROUP_NAME]
        self._file_name = flow_data[ATTR_FILE_NAME]
        self._entry_id = entry_id

        self._meta_data: dict[str, Any] = {}
        self._orphaned_entities: dict[str, Any] = {}
        self._devices: list[dict[str, Any]] = []
        self._entities: dict[str, Any] = {}
        self._simulations: list[dict[str, Any]] = []

    async def async_load(self):
        meta_data = await _load_meta_data(self._hass, self._group_name)
        devices, simulations = await _load_user_data(self._hass, self._file_name)
        self._simulations = simulations
        changed = False

        _LOGGER.debug(f"loaded-meta-data={meta_data}")
        _LOGGER.debug(f"loaded-devices={devices}")

        # Check Home Assistant native registries for existing devices/entities
        import homeassistant.helpers.device_registry as dr
        import homeassistant.helpers.entity_registry as er

        dev_reg = dr.async_get(self._hass)
        ent_reg = er.async_get(self._hass)

        existing_devs = []
        existing_ents = []
        if self._entry_id:
            existing_devs = dr.async_entries_for_config_entry(dev_reg, self._entry_id)
            existing_ents = er.async_entries_for_config_entry(ent_reg, self._entry_id)

        # Let's fix up the devices/entities
        for device_name, entities in devices.items():

            # Create device. One per all entities.
            self._devices.append({
                ATTR_DEVICE_ID: device_name,
                CONF_NAME: _make_name(device_name)
            })

            clean_device_name = _make_name(device_name)

            # Match existing device in registry by identifier
            matched_dev = None
            for d in existing_devs:
                if any(ident == (COMPONENT_DOMAIN, device_name) for ident in d.identifiers):
                    matched_dev = d
                    break

            dev_entities = (
                [e for e in existing_ents if e.device_id == matched_dev.id]
                if matched_dev
                else []
            )

            for entity in entities:

                platform = entity.pop(CONF_PLATFORM)
                device_class = entity.get(CONF_CLASS, None)
                raw_name = entity.get(CONF_NAME, None)

                # Determine if this is the primary entity or a sub-entity
                is_primary = False
                sub_name = None
                if raw_name is None or raw_name == "":
                    is_primary = True
                else:
                    clean_raw = _make_name(raw_name).strip()
                    norm_dev = clean_device_name.strip().lower()
                    if clean_raw.lower() == norm_dev:
                        is_primary = True
                    elif clean_raw.lower().startswith(norm_dev):
                        stripped = clean_raw[len(clean_device_name):].lstrip(" -_:")
                        if stripped:
                            sub_name = stripped
                        else:
                            is_primary = True
                    else:
                        sub_name = clean_raw

                # 1. Match from existing Home Assistant entity_registry
                matched_ent = None
                for e in dev_entities:
                    if e.domain == platform:
                        if is_primary:
                            if e.original_name is None or e.original_name == clean_device_name or e.original_name == raw_name:
                                matched_ent = e
                                break
                        else:
                            if e.original_name == sub_name or e.original_name == f"{clean_device_name} {sub_name}" or e.original_name == raw_name:
                                matched_ent = e
                                break

                unique_id = None
                entity_id = None
                found_key = None

                if matched_ent:
                    unique_id = matched_ent.unique_id
                    entity_id = matched_ent.entity_id
                    found_key = f"{device_name} {sub_name}" if not is_primary else device_name

                # 2. Fall back to meta_data candidate keys (e.g. from virtual.meta.json)
                if unique_id is None:
                    if is_primary:
                        candidates = [
                            device_name,
                            clean_device_name,
                            f"{device_name} {_make_suffix(platform, device_class)}",
                            f"{clean_device_name} {_make_suffix(platform, device_class)}",
                            raw_name,
                        ]
                    else:
                        candidates = [
                            f"{device_name} {sub_name}",
                            f"{clean_device_name} {sub_name}",
                            raw_name,
                            sub_name,
                            f"{device_name}_{sub_name}",
                        ]

                    for candidate in candidates:
                        if candidate and candidate in meta_data:
                            meta_entry = meta_data[candidate]
                            found_key = candidate
                            unique_id = meta_entry.get(ATTR_UNIQUE_ID)
                            entity_id = meta_entry.get(ATTR_ENTITY_ID)
                            break

                # 3. For new entities: generate deterministic unique_id & entity_id
                if unique_id is None:
                    if is_primary:
                        found_key = device_name
                        dev_slug = slugify(clean_device_name)
                        unique_id = f"{dev_slug}.{COMPONENT_DOMAIN}"
                        entity_id = _make_entity_id(platform, device_name)
                    else:
                        found_key = f"{clean_device_name} {sub_name}"
                        dev_slug = slugify(clean_device_name)
                        sub_slug = slugify(sub_name)
                        unique_id = f"{dev_slug}_{sub_slug}.{COMPONENT_DOMAIN}"
                        if device_name.startswith("+"):
                            entity_id = f"{platform}.{COMPONENT_DOMAIN}_{dev_slug}_{sub_slug}"
                        else:
                            entity_id = f"{platform}.{dev_slug}_{sub_slug}"

                if found_key in meta_data:
                    self._meta_data[found_key] = meta_data.pop(found_key)
                else:
                    self._meta_data[found_key] = {
                        ATTR_UNIQUE_ID: unique_id,
                        ATTR_ENTITY_ID: entity_id,
                        ATTR_DEVICE_ID: device_name,
                    }

                # Update the entity. Primary entity passes CONF_NAME: None
                entity.update({
                    CONF_NAME: sub_name if not is_primary else None,
                    ATTR_ENTITY_ID: entity_id,
                    ATTR_UNIQUE_ID: unique_id,
                    ATTR_DEVICE_ID: device_name,
                })
                _LOGGER.debug(f"added entity {platform}/{entity}")

                if platform not in self._entities:
                    self._entities[platform] = []
                self._entities[platform].append(entity)

        # Create orphaned list. If we have anything here we need to update
        # the saved meta data.
        for switch, values in meta_data.items():
            values[CONF_NAME] = switch
            self._orphaned_entities.update({
                values[ATTR_UNIQUE_ID]: values
            })
            changed = True

        # Make sure changes are kept.
        if changed:
            await _save_meta_data(self._hass, self._group_name, self._meta_data)

        _LOGGER.debug(f"meta-data={self._meta_data}")
        _LOGGER.debug(f"devices={self._devices}")
        _LOGGER.debug(f"entities={self._entities}")
        _LOGGER.debug(f"orphaned-entities={self._orphaned_entities}")

    async def async_delete(self):
        _LOGGER.debug(f"deleting {self._group_name}")
        await _delete_meta_data(self._hass, self._group_name)

    @property
    def devices(self):
        return self._devices

    @property
    def entities(self):
        return self._entities

    @property
    def orphaned_entities(self):
        return self._orphaned_entities

    @property
    def binary_sensor_config(self):
        return self._entities.get(Platform.BINARY_SENSOR, [])

    @property
    def sensor_config(self):
        return self._entities.get(Platform.SENSOR, [])

    @property
    def switch_config(self):
        return self._entities.get(Platform.SWITCH, [])

    @property
    def siren_config(self):
        return self._entities.get(Platform.SIREN, [])

    @property
    def simulations(self) -> list[dict[str, Any]]:
        return self._simulations


class UpgradeCfg:
    """Read in the old YAML config and convert it to the new format.
    """

    @staticmethod
    async def async_import_yaml(hass: HomeAssistant, config: dict[str, Any]):
        """ Take the current virtual config and make the new yaml file.

        Virtual needs a lot of fine tuning so rather than get rid of the
        options or clutter up the config flow system I'm adding a text file
        where the user can configure things.
        """

        devices_meta_data = {}
        devices = {}

        # Add in the easily formatted devices.
        for platform in [Platform.BINARY_SENSOR, Platform.SENSOR,
                         Platform.FAN, Platform.LIGHT,
                         Platform.LOCK, Platform.SIREN, Platform.SWITCH]:
            devices = _parse_old_config(devices, config.get(platform, []), str(platform))

        # Device tracker is awkward, we have to split it out and fake looking
        # like the other entities.
        all_device_trackers = config.get(Platform.DEVICE_TRACKER, [])
        for device_trackers in all_device_trackers:
            if device_trackers[CONF_PLATFORM] != COMPONENT_DOMAIN:
                continue
            for device_tracker_name in device_trackers.get("devices", []):
                if isinstance(device_tracker_name, dict):
                    device_tracker_name = device_tracker_name[CONF_NAME]
                devices = _parse_old_config(devices, [{
                    CONF_PLATFORM: COMPONENT_DOMAIN,
                    CONF_NAME: device_tracker_name
                }], str(Platform.DEVICE_TRACKER))

        _LOGGER.info(f"devices={devices}")

        # Here we have all the original devices we build the meta data.
        # For import
        #  - we can only have one entity per device, which means...
        #  - devices are their own parent
        for name, values in devices.items():
            unique_id = _make_original_unique_id(name)
            entity_id = _make_entity_id(values[0][CONF_PLATFORM], name)

            _LOGGER.debug(f"uid={unique_id}")
            _LOGGER.debug(f"eid={entity_id}")
            devices_meta_data.update({name: {
                ATTR_UNIQUE_ID: unique_id,
                ATTR_ENTITY_ID: entity_id
            }})

        _LOGGER.debug(f"devices-meta-data={devices_meta_data}")

        await _save_user_data(hass, default_config_file(hass), devices)
        await _save_meta_data(hass, IMPORTED_GROUP_NAME, devices_meta_data)

    @staticmethod
    def create_flow_data(hass: HomeAssistant, _config: dict[str, Any]) -> dict[str, Any]:
        """ Take the current virtual config and make the new flow configuration.
        """
        _LOGGER.debug(f"new-config-file={default_config_file(hass)}")
        _LOGGER.debug(f"new-meta-file={default_meta_file(hass)}")

        return {
            ATTR_GROUP_NAME: IMPORTED_GROUP_NAME,
            ATTR_FILE_NAME: default_config_file(hass)
        }
