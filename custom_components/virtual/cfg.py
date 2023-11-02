"""
Handles the file based Virtual configuration.

Virtual seems to need a lot device config so rather than get rid of
the options or clutter up the config flow system I'm adding a text file
where the user can configure things.

There are 2 pieces:

- `BlendedCfg`; this class is responsible for loading the new file based
  configuration and merging it with the flow data and options.

- `UpgradeCfg`; A helper class to import configuration from the old YAML
  layout.
"""

import copy
import logging
import json
import threading
import voluptuous as vol
from datetime import timedelta

from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_PLATFORM,
    CONF_UNIT_OF_MEASUREMENT,
    Platform
)
from homeassistant.helpers import config_validation as cv
from homeassistant.util import slugify
from homeassistant.util.yaml import load_yaml, save_yaml

from .const import *
from .entity import virtual_schema


_LOGGER = logging.getLogger(__name__)

IMPORTED_YAML_FILE = "/config/virtual.yaml"

BINARY_SENSOR_DEFAULT_INITIAL_VALUE = 'off'
BINARY_SENSOR_SCHEMA = vol.Schema(virtual_schema(BINARY_SENSOR_DEFAULT_INITIAL_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
}))

SENSOR_DEFAULT_INITIAL_VALUE = '0'
SENSOR_SCHEMA = vol.Schema(virtual_schema(SENSOR_DEFAULT_INITIAL_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=""): cv.string,
}))

DB_LOCK = threading.Lock()


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


def _fix_value(value):
    """ If needed, convert value into a type that can be stored in yaml.
    """
    if isinstance(value, timedelta):
        return max(value.seconds, 1)
    return value


class BlendedCfg(object):
    """Helper class to get at Virtual configuration options.

    Reads in non config flow settings from the external config file and merges
    them with flow data and options.
    """

    _main_config = {}
    _alarm_config = {}
    _binary_sensor_config = {}
    _sensor_config = {}
    _switch_config = {}

    @property
    def domain_config(self):
        return self._main_config

    @property
    def alarm_config(self):
        return self._alarm_config

    @property
    def binary_sensor_config(self):
        return self._binary_sensor_config

    @property
    def sensor_config(self):
        return self._sensor_config

    @property
    def switch_config(self):
        return self._switch_config


def upgrade_name(name: str):
    """We're making the non virtual prefix the default so this flips the naming.
    """
    if name.startswith("!"):
        return name[1:]
    elif name.startswith("virtual_"):
        return f"+{name[8:]}"
    else:
        return f"+{name}"


def parse_old_config(devices, configs, platform):
    """Parse out config into different devices.

    We invert the sense so we can support multiple virtual devices per
    platform.
    """
    for config in configs:
        if config[CONF_PLATFORM] != COMPONENT_DOMAIN:
            continue

        # Copy and fix up config.
        config = copy.deepcopy(config)
        config[CONF_PLATFORM] = platform
        name = upgrade_name(config.pop(CONF_NAME))

        # Insert or create a device for it.
        if name in devices:
            devices[name].append(config)
        else:
            devices[name] = [config]

    return devices


class UpgradeCfg(object):
    """Read in the old YAML config and convert it to the new format.
    """

    _devices_ = {}
    _devices_meta_data = {}
    _orphaned_devices = {}
    _changed: bool = False

    def _make_original_unique_id(self, name):
        if name.startswith("+"):
            return slugify(name[1:])
        else:
            return slugify(name)

    def _make_original_entity_id(self, platform, name):
        if name.startswith("+"):
            return f'{platform}.{COMPONENT_DOMAIN}_{slugify(name[1:])}'
        else:
            return f'{platform}.{slugify(name)}'

    def save_meta_data(self):

        # Make sure we have the global lock for this.
        with DB_LOCK:

            # Read in current meta data
            devices = {}
            try:
                with open(CFG_DEFAULT_META_FILE, 'r') as meta_file:
                    devices = json.load(meta_file).get(ATTR_DEVICES, {})
            except Exception as e:
                _LOGGER.debug(f"no meta data yet {str(e)}")

            # Update (or add) the group piece.
            _LOGGER.debug(f"meta before {devices}")
            devices.update({
                "imported": self._devices_meta_data
            })
            _LOGGER.debug(f"meta after {devices}")

            # Write it back out.
            try:
                with open(CFG_DEFAULT_META_FILE, 'w') as meta_file:
                    json.dump({
                        ATTR_VERSION: 1,
                        ATTR_DEVICES: devices
                    }, meta_file, indent=4)
            except Exception as e:
                _LOGGER.debug(f"couldn't save meta data {str(e)}")

        self._changed = False

    def save_user_data(self):
        try:
            save_yaml(CFG_DEFAULT_FILE, {
                ATTR_VERSION: 1,
                ATTR_DEVICES: self._devices
            })
        except Exception as e:
            _LOGGER.debug(f"couldn't save user data {str(e)}")

    def import_yaml(self, config):
        """ Take the current virtual config and make the new yaml file.

        Virtual needs a lot of fine tuning so rather than get rid of the
        options or clutter up the config flow system I'm adding a text file
        where the user can configure things.
        """

        self._devices = {}

        # Add in the easily formatted devices.
        for platform in [Platform.BINARY_SENSOR, Platform.SENSOR,
                         Platform.FAN, Platform.LIGHT,
                         Platform.LOCK, Platform.SWITCH]:
            self._devices = parse_old_config(self._devices, config.get(platform, []), str(platform))

        # Device tracker is awkward, we have to split it out and fake looking
        # like the other entities.
        all_device_trackers = config.get(Platform.DEVICE_TRACKER, [])
        for device_trackers in all_device_trackers:
            if device_trackers[CONF_PLATFORM] != COMPONENT_DOMAIN:
                continue
            for device_tracker in device_trackers.get("self._devices", []):
                _LOGGER.debug(f"trying {device_tracker}")
                self._devices = parse_old_config(self._devices, [{
                    CONF_PLATFORM: COMPONENT_DOMAIN,
                    "name": device_tracker["name"]
                }], str(Platform.DEVICE_TRACKER))

        _LOGGER.info(f"devices={self._devices}")

        # Here we have all the original devices we build the meta data.
        # For import
        #  - we can only have one entity per device, which means...
        #  - devices are their own parent
        for name, values in self._devices.items():
            unique_id = self._make_original_unique_id(name)
            entity_id = self._make_original_entity_id(values[0][CONF_PLATFORM], name)

            _LOGGER.debug(f"uid={unique_id}")
            _LOGGER.debug(f"eid={entity_id}")
            self._devices_meta_data.update({name: {
                ATTR_UNIQUE_ID: unique_id,
                ATTR_PARENT_ID: unique_id,
                ATTR_ENTITY_ID: entity_id
            }})

        _LOGGER.debug(f"devices-meta-data={self._devices_meta_data}")

        self.save_user_data()
        self.save_meta_data()

    @staticmethod
    def create_flow_data(config):
        """ Take the current aarlo config and make the new flow configuration.
        """
        pass
