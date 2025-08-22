"""Constants for the virtual component. """

COMPONENT_DOMAIN = "virtual"
COMPONENT_SERVICES = "virtual-services"
COMPONENT_CONFIG = "virtual-config"
COMPONENT_MANUFACTURER = "twrecked"
COMPONENT_MODEL = "virtual"

ATTR_AVAILABLE = 'available'
ATTR_DEVICES = "devices"
ATTR_DEVICE_ID = "device_id"
ATTR_ENTITIES = "entities"
ATTR_FILE_NAME = "file_name"
ATTR_GROUP_NAME = "group_name"
ATTR_PARENT_ID = "parent_id"
ATTR_PERSISTENT = 'persistent'
ATTR_UNIQUE_ID = 'unique_id'
ATTR_VALUE = "value"
ATTR_VERSION = "version"

CONF_CLASS = "class"
CONF_INITIAL_AVAILABILITY = "initial_availability"
CONF_INITIAL_VALUE = "initial_value"
CONF_MAX = "max"
CONF_MIN = "min"
CONF_NAME = "name"
CONF_OPEN_CLOSE_DURATION = "open_close_duration"
CONF_OPEN_CLOSE_TICK = "open_close_tick"
CONF_PERSISTENT = "persistent"
CONF_YAML_CONFIG = "yaml_config"

# Climate specific constants
CONF_HVAC_MODES = "hvac_modes"
CONF_FAN_MODES = "fan_modes"
CONF_PRESET_MODES = "preset_modes"
CONF_SWING_MODES = "swing_modes"
CONF_TARGET_TEMP_STEP = "target_temp_step"
CONF_CURRENT_TEMPERATURE = "current_temperature"
CONF_CURRENT_HUMIDITY = "current_humidity"
CONF_TARGET_TEMPERATURE = "target_temperature"
CONF_TARGET_TEMPERATURE_HIGH = "target_temperature_high"
CONF_TARGET_TEMPERATURE_LOW = "target_temperature_low"
CONF_HUMIDITY = "humidity"
CONF_FAN_MODE = "fan_mode"
CONF_PRESET_MODE = "preset_mode"
CONF_SWING_MODE = "swing_mode"
CONF_HVAC_ACTION = "hvac_action"

DEFAULT_AVAILABILITY = True
DEFAULT_PERSISTENT = True

IMPORTED_GROUP_NAME = "imported"


def default_config_file(hass) -> str:
    return hass.config.path("virtual.yaml")


def default_meta_file(hass) -> str:
    return hass.config.path(".storage/virtual.meta.json")
