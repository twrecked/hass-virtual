"""Constants for the virtual component."""
from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import (
    ATTR_ENTITY_ID,
    LIGHT_LUX,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS,
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfPressure,
    UnitOfReactivePower,
    UnitOfTemperature,
    UnitOfVolume,
)
try:
    from homeassistant.const import UnitOfDensity, UnitOfRatio
    MICROGRAMS_PER_CUBIC_METER = UnitOfDensity.MICROGRAMS_PER_CUBIC_METER
    PARTS_PER_MILLION = UnitOfRatio.PARTS_PER_MILLION
except ImportError:
    from homeassistant.const import (
        CONCENTRATION_MICROGRAMS_PER_CUBIC_METER as MICROGRAMS_PER_CUBIC_METER,
        CONCENTRATION_PARTS_PER_MILLION as PARTS_PER_MILLION,
    )

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

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
CONF_OPTIONS = "options"
CONF_MODE = "mode"
CONF_PATTERN = "pattern"
CONF_CODE = "code"
CONF_CODE_ARM_REQUIRED = "code_arm_required"
CONF_ARMING_TIME = "arming_time"
CONF_TRIGGER_TIME = "trigger_time"
CONF_INITIAL_TEMPERATURE = "initial_temperature"
CONF_INITIAL_CURRENT_TEMPERATURE = "initial_current_temperature"
CONF_HVAC_MODES = "hvac_modes"
CONF_PRESET_MODES = "preset_modes"
CONF_FAN_MODES = "fan_modes"
CONF_TARGET_TEMP_STEP = "target_temperature_step"
CONF_OPEN_CLOSE_DURATION = "open_close_duration"
CONF_OPEN_CLOSE_TICK = "open_close_tick"
CONF_PERSISTENT = "persistent"
CONF_YAML_CONFIG = "yaml_config"
CONF_EDITOR_URL = "editor_url"

SERVICE_SET_CURRENT_TEMPERATURE = "set_current_temperature"

DEFAULT_AVAILABILITY = True
DEFAULT_PERSISTENT = True
DEFAULT_EDITOR_URL = "https://virtual-dot-twrecked-tools.nn.r.appspot.com"

IMPORTED_GROUP_NAME = "imported"

DEVICE_CLASS_UNITS: dict[str, str] = {
    "apparent_power": UnitOfApparentPower.VOLT_AMPERE,
    "battery": PERCENTAGE,
    "carbon_monoxide": PARTS_PER_MILLION,
    "carbon_dioxide": PARTS_PER_MILLION,
    "co": PARTS_PER_MILLION,
    "co2": PARTS_PER_MILLION,
    "humidity": PERCENTAGE,
    "illuminance": LIGHT_LUX,
    "nitrogen_dioxide": MICROGRAMS_PER_CUBIC_METER,
    "nitrogen_monoxide": MICROGRAMS_PER_CUBIC_METER,
    "nitrous_oxide": MICROGRAMS_PER_CUBIC_METER,
    "ozone": MICROGRAMS_PER_CUBIC_METER,
    "pm1": MICROGRAMS_PER_CUBIC_METER,
    "pm10": MICROGRAMS_PER_CUBIC_METER,
    "pm25": MICROGRAMS_PER_CUBIC_METER,
    "signal_strength": SIGNAL_STRENGTH_DECIBELS,
    "sulphur_dioxide": MICROGRAMS_PER_CUBIC_METER,
    "temperature": UnitOfTemperature.CELSIUS,
    "pressure": UnitOfPressure.HPA,
    "power": UnitOfPower.KILO_WATT,
    "current": UnitOfElectricCurrent.AMPERE,
    "energy": UnitOfEnergy.KILO_WATT_HOUR,
    "frequency": UnitOfFrequency.GIGAHERTZ,
    "power_factor": PERCENTAGE,
    "reactive_power": UnitOfReactivePower.VOLT_AMPERE_REACTIVE,
    "volatile_organic_compounds": MICROGRAMS_PER_CUBIC_METER,
    "voltage": UnitOfElectricPotential.VOLT,
    "gas": UnitOfVolume.CUBIC_METERS,
}

UNITS_OF_MEASUREMENT = DEVICE_CLASS_UNITS


def default_config_file(hass: HomeAssistant) -> str:
    return hass.config.path("virtual.yaml")


def default_meta_file(hass: HomeAssistant) -> str:
    return hass.config.path(".storage/virtual.meta.json")
