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
CONF_INITIAL_VOLUME = "initial_volume"
CONF_SOURCE_LIST = "source_list"
CONF_SOUND_MODE_LIST = "sound_mode_list"
CONF_OPEN_CLOSE_DURATION = "open_close_duration"
CONF_OPEN_CLOSE_TICK = "open_close_tick"
CONF_PERSISTENT = "persistent"
CONF_IMAGE_URL = "image_url"
CONF_STREAM_URL = "stream_url"
CONF_LINKED_SWITCH = "linked_switch"
CONF_STANDBY_POWER = "standby_power"
CONF_ACTIVE_POWER = "active_power"
CONF_INITIAL_LOAD = "initial_load"
CONF_VARIANCE = "variance"
CONF_CYCLE_DURATION = "cycle_duration"
CONF_CYCLE_INTERVAL = "cycle_interval"
CONF_CYCLE_ALIGN = "cycle_align"
CONF_OFF_DELAY = "off_delay"
CONF_LINKED_ENTITY = "linked_entity"
CONF_INDOOR_SENSOR = "indoor_sensor"
CONF_OUTDOOR_SENSOR = "outdoor_sensor"
CONF_POWER_SENSOR = "power_sensor"
CONF_HEATING_TYPE = "heating_type"
CONF_CLIMATE_ENTITY = "climate_entity"
CONF_GAS_SENSOR = "gas_sensor"
CONF_GAS_ENERGY_SENSOR = "gas_energy_sensor"
CONF_GAS_FLOW_STAGE1 = "gas_flow_stage1"
CONF_GAS_FLOW_STAGE2 = "gas_flow_stage2"
CONF_BLOWER_POWER = "blower_power"
CONF_HEAT_RATE_STAGE1 = "heat_rate_stage1"
CONF_HEAT_RATE_STAGE2 = "heat_rate_stage2"
CONF_COOL_RATE_STAGE1 = "cool_rate_stage1"
CONF_COOL_RATE_STAGE2 = "cool_rate_stage2"
CONF_FAN_COOL_RATE = "fan_cool_rate"
CONF_HEAT_POWER_STAGE1 = "heat_power_stage1"
CONF_HEAT_POWER_STAGE2 = "heat_power_stage2"
CONF_COOL_POWER_STAGE1 = "cool_power_stage1"
CONF_COOL_POWER_STAGE2 = "cool_power_stage2"
CONF_FAN_POWER = "fan_power"
CONF_HOUSE_LEAKAGE_RATE = "house_leakage_rate"
CONF_TICK_INTERVAL = "tick_interval"
CONF_SIM_SPEED = "sim_speed"
CONF_SIMULATIONS = "simulations"
CONF_YAML_CONFIG = "yaml_config"
CONF_EDITOR_URL = "editor_url"

ATTR_IMAGE_URL = "image_url"
ATTR_STREAM_URL = "stream_url"
ATTR_LOAD_STATE = "load_state"
ATTR_CONTROL_MODE = "control_mode"
ATTR_CYCLE_ACTIVE = "cycle_active"
ATTR_CYCLE_REMAINING = "cycle_remaining"
ATTR_NEXT_CYCLE_START = "next_cycle_start"
ATTR_LINKED_SWITCH = "linked_switch"
ATTR_OFF_DELAY = "off_delay"
ATTR_LINKED_ENTITY = "linked_entity"
ATTR_TIME_REMAINING = "time_remaining"
ATTR_HVAC_STAGE = "hvac_stage"
ATTR_HVAC_POWER = "hvac_power"
ATTR_OUTDOOR_TEMPERATURE = "outdoor_temperature"
ATTR_INDOOR_SENSOR = "indoor_sensor"
ATTR_OUTDOOR_SENSOR = "outdoor_sensor"
ATTR_POWER_SENSOR = "power_sensor"
ATTR_SIM_SPEED = "sim_speed"
ATTR_BATTERY_SOC = "battery_soc"

SERVICE_SET_CURRENT_TEMPERATURE = "set_current_temperature"
SERVICE_SET_IMAGE_URL = "set_image_url"
SERVICE_SET_STREAM_URL = "set_stream_url"
SERVICE_SET_LOAD = "set_load"
SERVICE_RUN_CYCLE = "run_cycle"
SERVICE_SET_SIM_SPEED = "set_sim_speed"
SERVICE_SET_LIGHT = "set_light"
SERVICE_SET_BATTERY_SOC = "set_battery_soc"
SERVICE_SET_SOLAR_POWER = "set_solar_power"

DEFAULT_AVAILABILITY = True
DEFAULT_PERSISTENT = True
DEFAULT_CAMERA_VALUE = "idle"
DEFAULT_IMAGE_URL = ""
DEFAULT_STREAM_URL = "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8"
DEFAULT_STANDBY_POWER = 0.0
DEFAULT_ACTIVE_POWER = 100.0
DEFAULT_INITIAL_LOAD = "standby"
DEFAULT_CYCLE_ALIGN = "hour"
DEFAULT_HEAT_RATE_STAGE1 = 1.5
DEFAULT_HEAT_RATE_STAGE2 = 3.0
DEFAULT_COOL_RATE_STAGE1 = 1.5
DEFAULT_COOL_RATE_STAGE2 = 3.0
DEFAULT_FAN_COOL_RATE = 0.2
DEFAULT_HEAT_POWER_STAGE1 = 1800.0
DEFAULT_HEAT_POWER_STAGE2 = 3800.0
DEFAULT_COOL_POWER_STAGE1 = 1400.0
DEFAULT_COOL_POWER_STAGE2 = 2800.0
DEFAULT_FAN_POWER = 120.0
DEFAULT_GAS_FLOW_STAGE1 = 1.2
DEFAULT_GAS_FLOW_STAGE2 = 2.4
DEFAULT_BLOWER_POWER = 120.0
DEFAULT_CLIMATE_STANDBY_POWER = 10.0
DEFAULT_HOUSE_LEAKAGE_RATE = 0.3
DEFAULT_TICK_INTERVAL = 10.0
DEFAULT_SIM_SPEED = 1.0
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
