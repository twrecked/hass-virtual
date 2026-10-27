"""This component provides support for a virtual climate entity with thermal simulation."""
from __future__ import annotations

import datetime
import logging
from collections.abc import Callable
from typing import Any

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_FAN_MODE,
    ATTR_HVAC_ACTION,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    ClimateEntity,
    ClimateEntityFeature,
    DOMAIN as PLATFORM_DOMAIN,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    PRECISION_HALVES,
    PRECISION_TENTHS,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import Event, HomeAssistant, ServiceCall, callback
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util, slugify

from . import get_entity_from_domain, get_entity_configs
from .const import (
    ATTR_GROUP_NAME,
    ATTR_HVAC_POWER,
    ATTR_HVAC_STAGE,
    ATTR_INDOOR_SENSOR,
    ATTR_OUTDOOR_SENSOR,
    ATTR_OUTDOOR_TEMPERATURE,
    ATTR_POWER_SENSOR,
    ATTR_SIM_SPEED,
    COMPONENT_CONFIG,
    COMPONENT_DOMAIN,
    COMPONENT_SERVICES,
    CONF_COOL_POWER_STAGE1,
    CONF_COOL_POWER_STAGE2,
    CONF_COOL_RATE_STAGE1,
    CONF_COOL_RATE_STAGE2,
    CONF_FAN_COOL_RATE,
    CONF_FAN_MODES,
    CONF_FAN_POWER,
    CONF_HEAT_POWER_STAGE1,
    CONF_HEAT_POWER_STAGE2,
    CONF_HEAT_RATE_STAGE1,
    CONF_HEAT_RATE_STAGE2,
    CONF_HOUSE_LEAKAGE_RATE,
    CONF_HVAC_MODES,
    CONF_INDOOR_SENSOR,
    CONF_INITIAL_CURRENT_TEMPERATURE,
    CONF_INITIAL_TEMPERATURE,
    CONF_INITIAL_VALUE,
    CONF_MAX,
    CONF_MIN,
    CONF_OUTDOOR_SENSOR,
    CONF_POWER_SENSOR,
    CONF_PRESET_MODES,
    CONF_SIM_SPEED,
    CONF_STANDBY_POWER,
    CONF_TARGET_TEMP_STEP,
    CONF_TICK_INTERVAL,
    CONF_YAML_CONFIG,
    DEFAULT_CLIMATE_STANDBY_POWER,
    DEFAULT_COOL_POWER_STAGE1,
    DEFAULT_COOL_POWER_STAGE2,
    DEFAULT_COOL_RATE_STAGE1,
    DEFAULT_COOL_RATE_STAGE2,
    DEFAULT_FAN_COOL_RATE,
    DEFAULT_FAN_POWER,
    DEFAULT_HEAT_POWER_STAGE1,
    DEFAULT_HEAT_POWER_STAGE2,
    DEFAULT_HEAT_RATE_STAGE1,
    DEFAULT_HEAT_RATE_STAGE2,
    DEFAULT_HOUSE_LEAKAGE_RATE,
    DEFAULT_SIM_SPEED,
    DEFAULT_TICK_INTERVAL,
    SERVICE_SET_CURRENT_TEMPERATURE,
    SERVICE_SET_SIM_SPEED,
)
from .entity import VirtualEntity, virtual_schema

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_CLIMATE_VALUE = "heat"
DEFAULT_TARGET_TEMP = 21.0
DEFAULT_CURRENT_TEMP = 20.0
DEFAULT_MIN_TEMP = 7.0
DEFAULT_MAX_TEMP = 35.0
DEFAULT_TARGET_TEMP_STEP = 0.5

HVAC_MODE_MAP = {
    "off": HVACMode.OFF,
    "heat": HVACMode.HEAT,
    "cool": HVACMode.COOL,
    "heat_cool": HVACMode.HEAT_COOL,
    "auto": HVACMode.AUTO,
    "dry": HVACMode.DRY,
    "fan_only": HVACMode.FAN_ONLY,
}

CONF_MIN_TEMP = "min_temp"
CONF_MAX_TEMP = "max_temp"


def _normalize_mode_list(modes: Any) -> list[str]:
    result = []
    for m in cv.ensure_list(modes):
        if m is False:
            result.append("off")
        elif m is True:
            result.append("on")
        elif m is not None:
            result.append(str(m))
    return result


CLIMATE_BASE_SCHEMA = virtual_schema(DEFAULT_CLIMATE_VALUE, {
    vol.Optional(CONF_INITIAL_TEMPERATURE, default=DEFAULT_TARGET_TEMP): vol.Coerce(float),
    vol.Optional(CONF_INITIAL_CURRENT_TEMPERATURE, default=DEFAULT_CURRENT_TEMP): vol.Coerce(float),
    vol.Optional(CONF_MIN): vol.Coerce(float),
    vol.Optional(CONF_MAX): vol.Coerce(float),
    vol.Optional(CONF_MIN_TEMP): vol.Coerce(float),
    vol.Optional(CONF_MAX_TEMP): vol.Coerce(float),
    vol.Optional(CONF_TARGET_TEMP_STEP, default=DEFAULT_TARGET_TEMP_STEP): vol.Coerce(float),
    vol.Optional(CONF_HVAC_MODES, default=["off", "heat", "cool", "auto"]): _normalize_mode_list,
    vol.Optional(CONF_PRESET_MODES, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_FAN_MODES, default=[]): vol.All(cv.ensure_list, [cv.string]),
    # Thermal Simulation
    vol.Optional(CONF_INDOOR_SENSOR): cv.string,
    vol.Optional(CONF_OUTDOOR_SENSOR): cv.string,
    vol.Optional(CONF_POWER_SENSOR): cv.string,
    vol.Optional(CONF_HEAT_RATE_STAGE1, default=DEFAULT_HEAT_RATE_STAGE1): vol.Coerce(float),
    vol.Optional(CONF_HEAT_RATE_STAGE2, default=DEFAULT_HEAT_RATE_STAGE2): vol.Coerce(float),
    vol.Optional(CONF_COOL_RATE_STAGE1, default=DEFAULT_COOL_RATE_STAGE1): vol.Coerce(float),
    vol.Optional(CONF_COOL_RATE_STAGE2, default=DEFAULT_COOL_RATE_STAGE2): vol.Coerce(float),
    vol.Optional(CONF_FAN_COOL_RATE, default=DEFAULT_FAN_COOL_RATE): vol.Coerce(float),
    vol.Optional(CONF_HEAT_POWER_STAGE1, default=DEFAULT_HEAT_POWER_STAGE1): vol.Coerce(float),
    vol.Optional(CONF_HEAT_POWER_STAGE2, default=DEFAULT_HEAT_POWER_STAGE2): vol.Coerce(float),
    vol.Optional(CONF_COOL_POWER_STAGE1, default=DEFAULT_COOL_POWER_STAGE1): vol.Coerce(float),
    vol.Optional(CONF_COOL_POWER_STAGE2, default=DEFAULT_COOL_POWER_STAGE2): vol.Coerce(float),
    vol.Optional(CONF_FAN_POWER, default=DEFAULT_FAN_POWER): vol.Coerce(float),
    vol.Optional(CONF_STANDBY_POWER, default=DEFAULT_CLIMATE_STANDBY_POWER): vol.Coerce(float),
    vol.Optional(CONF_HOUSE_LEAKAGE_RATE, default=DEFAULT_HOUSE_LEAKAGE_RATE): vol.Coerce(float),
    vol.Optional(CONF_TICK_INTERVAL, default=DEFAULT_TICK_INTERVAL): vol.Coerce(float),
    vol.Optional(CONF_SIM_SPEED, default=DEFAULT_SIM_SPEED): vol.Coerce(float),
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(CLIMATE_BASE_SCHEMA)
CLIMATE_SCHEMA = vol.Schema(CLIMATE_BASE_SCHEMA)

SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required(ATTR_TEMPERATURE): vol.Coerce(float),
})

SERVICE_SIM_SPEED_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required("speed"): vol.Coerce(float),
})


def setup_services(hass: HomeAssistant) -> None:
    """Register virtual climate services."""

    async def async_virtual_service(call: ServiceCall) -> None:
        """Call virtual climate service handler."""
        _LOGGER.debug(f"{call.service} service called")
        if call.service == SERVICE_SET_CURRENT_TEMPERATURE:
            await async_virtual_set_current_temp_service(hass, call)
        elif call.service == SERVICE_SET_SIM_SPEED:
            await async_virtual_set_sim_speed_service(hass, call)

    if PLATFORM_DOMAIN not in hass.data[COMPONENT_SERVICES]:
        _LOGGER.debug("installing climate handlers")
        hass.data[COMPONENT_SERVICES][PLATFORM_DOMAIN] = "installed"
        hass.services.async_register(
            COMPONENT_DOMAIN,
            SERVICE_SET_CURRENT_TEMPERATURE,
            async_virtual_service,
            schema=SERVICE_SCHEMA,
        )
        hass.services.async_register(
            COMPONENT_DOMAIN,
            SERVICE_SET_SIM_SPEED,
            async_virtual_service,
            schema=SERVICE_SIM_SPEED_SCHEMA,
        )


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up virtual climate entity from YAML."""
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")
        climates = [VirtualClimate(config, True)]
        async_add_entities(climates, True)
        setup_services(hass)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable[[list], None],
) -> None:
    """Set up virtual climate entity from config entry."""
    _LOGGER.debug("setting up the entries...")
    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = CLIMATE_SCHEMA(entity)
        entities.append(VirtualClimate(entity, False))
    async_add_entities(entities)
    setup_services(hass)


class VirtualClimate(VirtualEntity, ClimateEntity):
    """Representation of a Virtual climate entity with thermal simulation."""

    def __init__(self, config: dict[str, Any], old_style: bool):
        """Initialize the Virtual climate device."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_temperature_unit = UnitOfTemperature.CELSIUS

        min_val = config.get(CONF_MIN_TEMP)
        if min_val is None:
            min_val = config.get(CONF_MIN, DEFAULT_MIN_TEMP)
        self._attr_min_temp = float(min_val)

        max_val = config.get(CONF_MAX_TEMP)
        if max_val is None:
            max_val = config.get(CONF_MAX, DEFAULT_MAX_TEMP)
        self._attr_max_temp = float(max_val)

        self._attr_target_temperature_step = float(config.get(CONF_TARGET_TEMP_STEP, DEFAULT_TARGET_TEMP_STEP))
        self._attr_precision = PRECISION_HALVES if self._attr_target_temperature_step == 0.5 else PRECISION_TENTHS

        # HVAC modes
        raw_modes = _normalize_mode_list(config.get(CONF_HVAC_MODES, ["off", "heat", "cool", "auto"]))
        self._attr_hvac_modes = [HVAC_MODE_MAP[m.lower()] for m in raw_modes if m.lower() in HVAC_MODE_MAP]
        if not self._attr_hvac_modes:
            self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]

        self._attr_preset_modes = config.get(CONF_PRESET_MODES, [])
        self._attr_fan_modes = config.get(CONF_FAN_MODES, [])

        features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.TURN_OFF | ClimateEntityFeature.TURN_ON
        if self._attr_preset_modes:
            features |= ClimateEntityFeature.PRESET_MODE
        if self._attr_fan_modes:
            features |= ClimateEntityFeature.FAN_MODE
        self._attr_supported_features = features

        # Thermal Simulation Properties
        self._indoor_sensor_config: str | None = config.get(CONF_INDOOR_SENSOR)
        self._outdoor_sensor_config: str | None = config.get(CONF_OUTDOOR_SENSOR)
        self._power_sensor_config: str | None = config.get(CONF_POWER_SENSOR)

        self._heat_rate_stage1: float = float(config.get(CONF_HEAT_RATE_STAGE1, DEFAULT_HEAT_RATE_STAGE1))
        self._heat_rate_stage2: float = float(config.get(CONF_HEAT_RATE_STAGE2, DEFAULT_HEAT_RATE_STAGE2))
        self._cool_rate_stage1: float = float(config.get(CONF_COOL_RATE_STAGE1, DEFAULT_COOL_RATE_STAGE1))
        self._cool_rate_stage2: float = float(config.get(CONF_COOL_RATE_STAGE2, DEFAULT_COOL_RATE_STAGE2))
        self._fan_cool_rate: float = float(config.get(CONF_FAN_COOL_RATE, DEFAULT_FAN_COOL_RATE))

        self._heat_power_stage1: float = float(config.get(CONF_HEAT_POWER_STAGE1, DEFAULT_HEAT_POWER_STAGE1))
        self._heat_power_stage2: float = float(config.get(CONF_HEAT_POWER_STAGE2, DEFAULT_HEAT_POWER_STAGE2))
        self._cool_power_stage1: float = float(config.get(CONF_COOL_POWER_STAGE1, DEFAULT_COOL_POWER_STAGE1))
        self._cool_power_stage2: float = float(config.get(CONF_COOL_POWER_STAGE2, DEFAULT_COOL_POWER_STAGE2))
        self._fan_power: float = float(config.get(CONF_FAN_POWER, DEFAULT_FAN_POWER))
        self._standby_power: float = float(config.get(CONF_STANDBY_POWER, DEFAULT_CLIMATE_STANDBY_POWER))

        self._house_leakage_rate: float = float(config.get(CONF_HOUSE_LEAKAGE_RATE, DEFAULT_HOUSE_LEAKAGE_RATE))
        self._tick_interval: float = max(1.0, float(config.get(CONF_TICK_INTERVAL, DEFAULT_TICK_INTERVAL)))
        self._sim_speed: float = max(0.1, float(config.get(CONF_SIM_SPEED, DEFAULT_SIM_SPEED)))

        self._is_thermal_sim: bool = bool(
            self._indoor_sensor_config or self._outdoor_sensor_config or self._power_sensor_config
        )

        self._indoor_sensor_id: str | None = None
        self._outdoor_sensor_id: str | None = None
        self._power_sensor_id: str | None = None

        self._outdoor_temp: float = 20.0
        self._hvac_stage: str = "idle"
        self._hvac_power: float = 0.0
        self._last_tick_time: datetime.datetime | None = None
        self._tick_timer_cancel: Callable[[], None] | None = None
        self._outdoor_unsub: Callable[[], None] | None = None

        _LOGGER.info(f"VirtualClimate: {self.name} created (thermal_sim={self._is_thermal_sim})")

    def _calculate_hvac_action(self) -> HVACAction:
        """Calculate native Home Assistant HVAC action."""
        if self._attr_hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        if self._attr_current_temperature is None or self._attr_target_temperature is None:
            return HVACAction.IDLE

        if self._attr_hvac_mode == HVACMode.HEAT:
            if self._attr_current_temperature < self._attr_target_temperature:
                return HVACAction.HEATING
            return HVACAction.IDLE
        elif self._attr_hvac_mode == HVACMode.COOL:
            if self._attr_current_temperature > self._attr_target_temperature:
                return HVACAction.COOLING
            return HVACAction.IDLE
        elif self._attr_hvac_mode in (HVACMode.AUTO, HVACMode.HEAT_COOL):
            if self._attr_current_temperature < self._attr_target_temperature - 0.5:
                return HVACAction.HEATING
            elif self._attr_current_temperature > self._attr_target_temperature + 0.5:
                return HVACAction.COOLING
            return HVACAction.IDLE
        elif self._attr_hvac_mode == HVACMode.FAN_ONLY:
            return HVACAction.FAN
        return HVACAction.IDLE

    def _evaluate_hvac_stage_and_power(self) -> tuple[str, float, float]:
        """Determine active stage, temp change rate (°C/hr), and power consumption (W)."""
        if self._attr_hvac_mode == HVACMode.OFF:
            return ("off", 0.0, 0.0)

        cur = self._attr_current_temperature
        tgt = self._attr_target_temperature
        if cur is None or tgt is None:
            return ("idle", 0.0, self._standby_power)

        # Cooling
        if self._attr_hvac_mode == HVACMode.COOL or (
            self._attr_hvac_mode in (HVACMode.AUTO, HVACMode.HEAT_COOL) and cur > tgt + 0.5
        ):
            if cur > tgt:
                # Stage 2 cooling if delta > 1.5°C or outdoor ambient > 30°C
                if (cur - tgt) > 1.5 or self._outdoor_temp > 30.0:
                    return ("stage2_cool", -self._cool_rate_stage2, self._cool_power_stage2)
                return ("stage1_cool", -self._cool_rate_stage1, self._cool_power_stage1)
            return ("idle", 0.0, self._standby_power)

        # Heating
        if self._attr_hvac_mode == HVACMode.HEAT or (
            self._attr_hvac_mode in (HVACMode.AUTO, HVACMode.HEAT_COOL) and cur < tgt - 0.5
        ):
            if cur < tgt:
                # Stage 2 heating if delta > 1.5°C or outdoor ambient < 0°C
                if (tgt - cur) > 1.5 or self._outdoor_temp < 0.0:
                    return ("stage2_heat", self._heat_rate_stage2, self._heat_power_stage2)
                return ("stage1_heat", self._heat_rate_stage1, self._heat_power_stage1)
            return ("idle", 0.0, self._standby_power)

        if self._attr_hvac_mode == HVACMode.FAN_ONLY:
            return ("fan", -self._fan_cool_rate, self._fan_power)

        return ("idle", 0.0, self._standby_power)

    def _create_state(self, config: dict[str, Any]) -> None:
        """Create initial state."""
        super()._create_state(config)

        raw_mode = str(config.get(CONF_INITIAL_VALUE, DEFAULT_CLIMATE_VALUE)).lower()
        self._attr_hvac_mode = HVAC_MODE_MAP.get(raw_mode, self._attr_hvac_modes[0])
        self._attr_target_temperature = float(config.get(CONF_INITIAL_TEMPERATURE, DEFAULT_TARGET_TEMP))
        self._attr_current_temperature = float(config.get(CONF_INITIAL_CURRENT_TEMPERATURE, DEFAULT_CURRENT_TEMP))
        self._attr_preset_mode = self._attr_preset_modes[0] if self._attr_preset_modes else None
        self._attr_fan_mode = self._attr_fan_modes[0] if self._attr_fan_modes else None
        self._attr_hvac_action = self._calculate_hvac_action()
        self._hvac_stage, _, self._hvac_power = self._evaluate_hvac_stage_and_power()

    def _restore_state(self, state, config: dict[str, Any]) -> None:
        """Restore state from storage with null safety (per AGENTS.local.md)."""
        super()._restore_state(state, config)

        if state.state and state.state.lower() in HVAC_MODE_MAP:
            self._attr_hvac_mode = HVAC_MODE_MAP[state.state.lower()]
        else:
            self._attr_hvac_mode = self._attr_hvac_modes[0]

        target_temp = state.attributes.get(ATTR_TEMPERATURE)
        if target_temp is not None:
            try:
                self._attr_target_temperature = float(target_temp)
            except (ValueError, TypeError):
                self._attr_target_temperature = float(config.get(CONF_INITIAL_TEMPERATURE, DEFAULT_TARGET_TEMP))
        else:
            self._attr_target_temperature = float(config.get(CONF_INITIAL_TEMPERATURE, DEFAULT_TARGET_TEMP))

        current_temp = state.attributes.get(ATTR_CURRENT_TEMPERATURE)
        if current_temp is not None:
            try:
                self._attr_current_temperature = float(current_temp)
            except (ValueError, TypeError):
                self._attr_current_temperature = float(config.get(CONF_INITIAL_CURRENT_TEMPERATURE, DEFAULT_CURRENT_TEMP))
        else:
            self._attr_current_temperature = float(config.get(CONF_INITIAL_CURRENT_TEMPERATURE, DEFAULT_CURRENT_TEMP))

        self._attr_preset_mode = state.attributes.get(ATTR_PRESET_MODE)
        self._attr_fan_mode = state.attributes.get(ATTR_FAN_MODE)
        self._attr_hvac_action = self._calculate_hvac_action()

        restored_speed = state.attributes.get(ATTR_SIM_SPEED)
        if restored_speed is not None:
            try:
                self._sim_speed = max(0.1, float(restored_speed))
            except (ValueError, TypeError):
                self._sim_speed = float(config.get(CONF_SIM_SPEED, DEFAULT_SIM_SPEED))
        else:
            self._sim_speed = float(config.get(CONF_SIM_SPEED, DEFAULT_SIM_SPEED))

        self._hvac_stage, _, self._hvac_power = self._evaluate_hvac_stage_and_power()

    def _update_attributes(self) -> None:
        """Update entity extra state attributes."""
        super()._update_attributes()
        if self._is_thermal_sim:
            self._attr_extra_state_attributes.update({
                ATTR_HVAC_STAGE: self._hvac_stage,
                ATTR_HVAC_POWER: self._hvac_power,
                ATTR_OUTDOOR_TEMPERATURE: self._outdoor_temp,
                ATTR_SIM_SPEED: self._sim_speed,
                ATTR_INDOOR_SENSOR: self._indoor_sensor_id or self._indoor_sensor_config,
                ATTR_OUTDOOR_SENSOR: self._outdoor_sensor_id or self._outdoor_sensor_config,
                ATTR_POWER_SENSOR: self._power_sensor_id or self._power_sensor_config,
            })

    def _resolve_sensor_id(self, config_val: str | None) -> str | None:
        """Resolve sensor name to entity_id."""
        if not config_val:
            return None
        if "." in config_val:
            return config_val

        slug = slugify(config_val)
        candidates = [
            f"sensor.{slug}",
            f"sensor.{COMPONENT_DOMAIN}_{slug}",
        ]
        for c in candidates:
            if self.hass.states.get(c):
                return c
        return candidates[0]

    def _step_simulation(self) -> None:
        """Execute one step of the closed-loop thermal physics engine."""
        if not self._is_thermal_sim or self._attr_current_temperature is None:
            return

        now = dt_util.utcnow()
        if self._last_tick_time is None:
            self._last_tick_time = now
            return

        dt_seconds = (now - self._last_tick_time).total_seconds()
        self._last_tick_time = now
        if dt_seconds <= 0:
            return

        dt_hours = (dt_seconds * self._sim_speed) / 3600.0

        cur_temp = self._attr_current_temperature
        delta_ambient = self._outdoor_temp - cur_temp

        # Passive heat transfer toward outdoor temperature
        leak_rate = self._house_leakage_rate * (delta_ambient / 10.0)
        dt_leak = leak_rate * dt_hours

        # Active HVAC conditioning
        stage, hvac_rate, power = self._evaluate_hvac_stage_and_power()
        self._hvac_stage = stage
        self._hvac_power = power
        dt_hvac = hvac_rate * dt_hours

        # Net temperature computation
        new_temp = cur_temp + dt_leak + dt_hvac

        # Clamp: passive leakage alone cannot cross ambient outdoor temp
        if hvac_rate == 0.0:
            if delta_ambient > 0 and new_temp > self._outdoor_temp:
                new_temp = self._outdoor_temp
            elif delta_ambient < 0 and new_temp < self._outdoor_temp:
                new_temp = self._outdoor_temp

        # Clamp within thermostat hardware limits
        new_temp = max(self._attr_min_temp, min(self._attr_max_temp, new_temp))
        self._attr_current_temperature = round(new_temp, 2)
        self._attr_hvac_action = self._calculate_hvac_action()
        self._update_attributes()
        self.async_write_ha_state()

        # Synchronize linked indoor sensor
        if self._indoor_sensor_id:
            try:
                indoor_ent = get_entity_from_domain(self.hass, "sensor", self._indoor_sensor_id)
                indoor_ent.set(str(round(self._attr_current_temperature, 1)))
            except Exception:
                pass

        # Synchronize linked power sensor
        if self._power_sensor_id:
            try:
                power_ent = get_entity_from_domain(self.hass, "sensor", self._power_sensor_id)
                power_ent.set(str(round(self._hvac_power, 1)))
            except Exception:
                pass

    @callback
    def _on_simulation_tick(self, _now=None) -> None:
        """Timer callback for simulation tick."""
        self._step_simulation()

    def _on_outdoor_temp_change(self, new_state_str: str) -> None:
        """Handle temperature change from outdoor sensor."""
        try:
            self._outdoor_temp = float(new_state_str)
            self._attr_extra_state_attributes[ATTR_OUTDOOR_TEMPERATURE] = self._outdoor_temp
            self._step_simulation()
        except (ValueError, TypeError):
            pass

    async def async_added_to_hass(self) -> None:
        """Start thermal simulation when entity is added to Home Assistant."""
        await super().async_added_to_hass()

        if not self._is_thermal_sim:
            return

        self._indoor_sensor_id = self._resolve_sensor_id(self._indoor_sensor_config)
        self._outdoor_sensor_id = self._resolve_sensor_id(self._outdoor_sensor_config)
        self._power_sensor_id = self._resolve_sensor_id(self._power_sensor_config)

        # Initialize outdoor temp from outdoor sensor if present
        if self._outdoor_sensor_id:
            st = self.hass.states.get(self._outdoor_sensor_id)
            if st and st.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN, None):
                try:
                    self._outdoor_temp = float(st.state)
                except (ValueError, TypeError):
                    pass

            @callback
            def _handle_outdoor_change(event: Event) -> None:
                new_state = event.data.get("new_state")
                if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                    return
                self._on_outdoor_temp_change(new_state.state)

            self._outdoor_unsub = async_track_state_change_event(
                self.hass, [self._outdoor_sensor_id], _handle_outdoor_change
            )

        self._last_tick_time = dt_util.utcnow()
        self._tick_timer_cancel = async_track_time_interval(
            self.hass, self._on_simulation_tick, datetime.timedelta(seconds=self._tick_interval)
        )
        self._step_simulation()

    async def async_will_remove_from_hass(self) -> None:
        """Clean up timers and subscriptions."""
        if self._tick_timer_cancel:
            self._tick_timer_cancel()
            self._tick_timer_cancel = None
        if self._outdoor_unsub:
            self._outdoor_unsub()
            self._outdoor_unsub = None
        await super().async_will_remove_from_hass()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode | str) -> None:
        """Set new target hvac mode."""
        mode_val = HVAC_MODE_MAP.get(str(hvac_mode).lower(), hvac_mode)
        if mode_val in self._attr_hvac_modes:
            self._attr_hvac_mode = mode_val
            self._attr_hvac_action = self._calculate_hvac_action()
            self._hvac_stage, _, self._hvac_power = self._evaluate_hvac_stage_and_power()
            self._update_attributes()
            self.async_write_ha_state()
            if self._is_thermal_sim:
                self._step_simulation()
        else:
            raise ValueError(f"Unsupported HVAC mode: {hvac_mode}")

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is not None:
            self._attr_target_temperature = max(self._attr_min_temp, min(self._attr_max_temp, float(temp)))
            self._attr_hvac_action = self._calculate_hvac_action()
            self._hvac_stage, _, self._hvac_power = self._evaluate_hvac_stage_and_power()
            self._update_attributes()
            self.async_write_ha_state()
            if self._is_thermal_sim:
                self._step_simulation()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new target preset mode."""
        if preset_mode in self._attr_preset_modes:
            self._attr_preset_mode = preset_mode
            self._update_attributes()
            self.async_write_ha_state()
        else:
            raise ValueError(f"Unsupported preset mode: {preset_mode}")

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        if fan_mode in self._attr_fan_modes:
            self._attr_fan_mode = fan_mode
            self._update_attributes()
            self.async_write_ha_state()
        else:
            raise ValueError(f"Unsupported fan mode: {fan_mode}")

    async def async_turn_on(self) -> None:
        """Turn on the climate entity."""
        for mode in (HVACMode.HEAT, HVACMode.AUTO, HVACMode.COOL):
            if mode in self._attr_hvac_modes:
                await self.async_set_hvac_mode(mode)
                return
        await self.async_set_hvac_mode(self._attr_hvac_modes[0])

    async def async_turn_off(self) -> None:
        """Turn off the climate entity."""
        if HVACMode.OFF in self._attr_hvac_modes:
            await self.async_set_hvac_mode(HVACMode.OFF)

    def set_current_temperature(self, temperature: float) -> None:
        """Update current ambient temperature directly."""
        _LOGGER.debug(f"Setting current temperature of {self.name} to {temperature}")
        self._attr_current_temperature = float(temperature)
        self._attr_hvac_action = self._calculate_hvac_action()
        self._hvac_stage, _, self._hvac_power = self._evaluate_hvac_stage_and_power()
        self._update_attributes()
        self.async_write_ha_state()

        if self._indoor_sensor_id:
            try:
                indoor_ent = get_entity_from_domain(self.hass, "sensor", self._indoor_sensor_id)
                indoor_ent.set(str(round(self._attr_current_temperature, 1)))
            except Exception:
                pass

    def set_sim_speed(self, speed: float) -> None:
        """Update simulation speed multiplier."""
        _LOGGER.debug(f"Setting simulation speed of {self.name} to {speed}")
        self._sim_speed = max(0.1, float(speed))
        self._update_attributes()
        self.async_write_ha_state()


async def async_virtual_set_current_temp_service(hass: HomeAssistant, call: ServiceCall) -> None:
    temp = call.data[ATTR_TEMPERATURE]
    for entity_id in call.data[ATTR_ENTITY_ID]:
        _LOGGER.debug(f"setting current temp of {entity_id} to {temp}")
        get_entity_from_domain(hass, PLATFORM_DOMAIN, entity_id).set_current_temperature(temp)


async def async_virtual_set_sim_speed_service(hass: HomeAssistant, call: ServiceCall) -> None:
    speed = call.data["speed"]
    for entity_id in call.data[ATTR_ENTITY_ID]:
        _LOGGER.debug(f"setting sim speed of {entity_id} to {speed}")
        get_entity_from_domain(hass, PLATFORM_DOMAIN, entity_id).set_sim_speed(speed)
