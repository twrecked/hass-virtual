"""This component provides support for a virtual sensor with optional load simulation."""
from __future__ import annotations

import datetime
import logging
import random
from collections.abc import Callable
from typing import Any

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import (
    DOMAIN as PLATFORM_DOMAIN,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_UNIT_OF_MEASUREMENT,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, HomeAssistant, ServiceCall, callback
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util, slugify

from . import get_entity_from_domain, get_entity_configs
from .const import (
    ATTR_CONTROL_MODE,
    CONF_STATE_CLASS,
    ATTR_CYCLE_ACTIVE,
    ATTR_CYCLE_REMAINING,
    ATTR_GROUP_NAME,
    ATTR_LINKED_SWITCH,
    ATTR_LINKED_POWER,
    ATTR_LOAD_STATE,
    ATTR_NEXT_CYCLE_START,
    ATTR_VALUE,
    COMPONENT_CONFIG,
    COMPONENT_DOMAIN,
    COMPONENT_SERVICES,
    CONF_ACTIVE_POWER,
    CONF_CLASS,
    CONF_CYCLE_ALIGN,
    CONF_CYCLE_DURATION,
    CONF_CYCLE_INTERVAL,
    CONF_INITIAL_LOAD,
    CONF_INITIAL_VALUE,
    CONF_BATTERY_LIFE_DAYS,
    CONF_DRAIN_RATE,
    CONF_LINKED_SWITCH,
    CONF_LINKED_POWER,
    CONF_SIM_SPEED,
    CONF_STANDBY_POWER,
    CONF_VARIANCE,
    CONF_YAML_CONFIG,
    DEFAULT_ACTIVE_POWER,
    DEFAULT_CYCLE_ALIGN,
    DEFAULT_INITIAL_LOAD,
    DEFAULT_STANDBY_POWER,
    DEVICE_CLASS_UNITS,
    SERVICE_RUN_CYCLE,
    SERVICE_SET_LOAD,
)
from .entity import VirtualEntity, virtual_schema

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_SENSOR_VALUE = "0"

SERVICE_SET = "set"

SENSOR_LOAD_SCHEMA = {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_STATE_CLASS): cv.string,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=""): cv.string,
    vol.Optional(CONF_LINKED_SWITCH): cv.string,
    vol.Optional(CONF_LINKED_POWER): cv.string,
    vol.Optional(CONF_BATTERY_LIFE_DAYS): vol.Coerce(float),
    vol.Optional(CONF_DRAIN_RATE): vol.Coerce(float),
    vol.Optional(CONF_SIM_SPEED, default=1.0): vol.Coerce(float),
    vol.Optional(CONF_STANDBY_POWER, default=DEFAULT_STANDBY_POWER): vol.Coerce(float),
    vol.Optional(CONF_ACTIVE_POWER, default=DEFAULT_ACTIVE_POWER): vol.Coerce(float),
    vol.Optional(CONF_INITIAL_LOAD, default=DEFAULT_INITIAL_LOAD): cv.string,
    vol.Optional(CONF_VARIANCE, default=0.0): vol.Coerce(float),
    vol.Optional(CONF_CYCLE_DURATION): vol.Coerce(float),
    vol.Optional(CONF_CYCLE_INTERVAL): vol.Coerce(float),
    vol.Optional(CONF_CYCLE_ALIGN, default=DEFAULT_CYCLE_ALIGN): cv.string,
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_SENSOR_VALUE, SENSOR_LOAD_SCHEMA))
SENSOR_SCHEMA = vol.Schema(virtual_schema(DEFAULT_SENSOR_VALUE, SENSOR_LOAD_SCHEMA))

SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required(ATTR_VALUE): cv.string,
})

SERVICE_SET_LOAD_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required("state"): cv.string,
    vol.Optional("power"): vol.Coerce(float),
})

SERVICE_RUN_CYCLE_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Optional("duration"): vol.Coerce(float),
})


def setup_services(hass: HomeAssistant) -> None:
    """Register virtual sensor services."""

    async def async_virtual_service(call: ServiceCall) -> None:
        """Call virtual service handler."""
        _LOGGER.debug(f"{call.service} service called")
        for entity_id in call.data[ATTR_ENTITY_ID]:
            sensor = get_entity_from_domain(hass, PLATFORM_DOMAIN, entity_id)
            if call.service == SERVICE_SET:
                sensor.set(call.data[ATTR_VALUE])
            elif call.service == SERVICE_SET_LOAD:
                await sensor.async_set_load(
                    call.data["state"],
                    call.data.get("power"),
                )
            elif call.service == SERVICE_RUN_CYCLE:
                await sensor.async_run_cycle(call.data.get("duration"))

    if PLATFORM_DOMAIN not in hass.data[COMPONENT_SERVICES]:
        _LOGGER.debug("installing sensor handlers")
        hass.data[COMPONENT_SERVICES][PLATFORM_DOMAIN] = "installed"
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_SET, async_virtual_service, schema=SERVICE_SCHEMA,
        )
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_SET_LOAD, async_virtual_service, schema=SERVICE_SET_LOAD_SCHEMA,
        )
        hass.services.async_register(
            COMPONENT_DOMAIN, SERVICE_RUN_CYCLE, async_virtual_service, schema=SERVICE_RUN_CYCLE_SCHEMA,
        )


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up virtual sensor from YAML configuration."""
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")
        sensors = [VirtualSensor(config, True)]
        async_add_entities(sensors, True)
        setup_services(hass)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable[[list], None],
) -> None:
    """Set up virtual sensor from config entry."""
    _LOGGER.debug("setting up the entries...")
    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = SENSOR_SCHEMA(entity)
        entities.append(VirtualSensor(entity, False))
    async_add_entities(entities)
    setup_services(hass)


class VirtualSensor(VirtualEntity, SensorEntity):
    """An implementation of a Virtual Sensor with load simulation capabilities."""

    def __init__(self, config: dict[str, Any], old_style: bool):
        """Initialize a Virtual Sensor."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_device_class = config.get(CONF_CLASS)

        # Set unit of measurement
        unit = config.get(CONF_UNIT_OF_MEASUREMENT)
        if unit in ("C", "c", "Â°C", "Â°c") and self._attr_device_class == SensorDeviceClass.TEMPERATURE:
            unit = DEVICE_CLASS_UNITS["temperature"]
        elif not unit and self._attr_device_class:
            unit = DEVICE_CLASS_UNITS.get(str(self._attr_device_class))
        elif unit and "Â°" in unit:
            unit = unit.replace("Â°", "°")

        self._attr_native_unit_of_measurement = unit

        # Determine state class (crucial for Home Assistant Energy Dashboard & statistics)
        raw_state_class = config.get(CONF_STATE_CLASS)
        if raw_state_class:
            try:
                self._attr_state_class = SensorStateClass(str(raw_state_class).lower())
            except ValueError:
                self._attr_state_class = None
        elif self._attr_device_class in (SensorDeviceClass.ENERGY, "energy", "gas"):
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        elif self._attr_device_class in (
            SensorDeviceClass.POWER,
            SensorDeviceClass.TEMPERATURE,
            SensorDeviceClass.HUMIDITY,
            SensorDeviceClass.PRESSURE,
            SensorDeviceClass.VOLTAGE,
            SensorDeviceClass.CURRENT,
            SensorDeviceClass.BATTERY,
            SensorDeviceClass.ILLUMINANCE,
            "power",
            "temperature",
            "humidity",
            "pressure",
            "voltage",
            "current",
            "battery",
            "illuminance",
        ):
            self._attr_state_class = SensorStateClass.MEASUREMENT

        # Load simulation properties
        self._linked_switch_config: str | None = config.get(CONF_LINKED_SWITCH)
        self._standby_power: float = float(config.get(CONF_STANDBY_POWER, DEFAULT_STANDBY_POWER))
        self._active_power: float = float(config.get(CONF_ACTIVE_POWER, DEFAULT_ACTIVE_POWER))
        self._initial_load: str = str(config.get(CONF_INITIAL_LOAD, DEFAULT_INITIAL_LOAD)).lower()
        self._variance: float = float(config.get(CONF_VARIANCE, 0.0))

        raw_duration = config.get(CONF_CYCLE_DURATION)
        self._cycle_duration: float | None = float(raw_duration) if raw_duration is not None else None

        raw_interval = config.get(CONF_CYCLE_INTERVAL)
        self._cycle_interval: float | None = float(raw_interval) if raw_interval is not None else None

        self._cycle_align: str = str(config.get(CONF_CYCLE_ALIGN, DEFAULT_CYCLE_ALIGN)).lower()

        self._is_load_simulation: bool = bool(
            self._linked_switch_config or self._cycle_interval is not None
        )

        self._linked_switch_id: str | None = None
        self._linked_switch_state: str = STATE_ON
        self._load_state: str = self._initial_load
        self._control_mode: str = "auto" if self._cycle_interval else "override"
        self._cycle_end_time: datetime.datetime | None = None
        self._next_cycle_start: datetime.datetime | None = None
        self._cycle_timer_cancel: Callable[[], None] | None = None
        self._schedule_timer_cancel: Callable[[], None] | None = None
        self._switch_unsub: Callable[[], None] | None = None

        # Energy accumulation properties (for energy sensors integrating power)
        self._linked_power_config: str | None = config.get(CONF_LINKED_POWER)
        self._linked_power_id: str | None = None
        self._last_power_reading: float = 0.0
        self._last_energy_calc_time: datetime.datetime | None = None
        self._power_unsub: Callable[[], None] | None = None
        self._energy_interval_unsub: Callable[[], None] | None = None

        try:
            self._energy_accumulator: float = float(config.get(CONF_INITIAL_VALUE, DEFAULT_SENSOR_VALUE))
        except (ValueError, TypeError):
            self._energy_accumulator = 0.0

        # Battery drain simulation properties
        raw_life_days = config.get(CONF_BATTERY_LIFE_DAYS)
        self._battery_life_days: float | None = float(raw_life_days) if raw_life_days is not None else None

        raw_drain_rate = config.get(CONF_DRAIN_RATE)
        self._drain_rate: float | None = float(raw_drain_rate) if raw_drain_rate is not None else None

        self._sim_speed: float = max(0.1, float(config.get(CONF_SIM_SPEED, 1.0)))

        self._is_battery_simulation: bool = bool(
            (self._attr_device_class in (SensorDeviceClass.BATTERY, "battery") or self._battery_life_days is not None or self._drain_rate is not None)
            and (self._battery_life_days is not None or self._drain_rate is not None)
        )

        try:
            self._sim_battery_level: float = float(config.get(CONF_INITIAL_VALUE, 100))
        except (ValueError, TypeError):
            self._sim_battery_level = 100.0

        self._last_battery_calc_time: datetime.datetime | None = None
        self._battery_interval_unsub: Callable[[], None] | None = None

        _LOGGER.info(f"VirtualSensor: {self.name} created (load_sim={self._is_load_simulation}, linked_pwr={self._linked_power_config}, battery_sim={self._is_battery_simulation})")

    def _create_state(self, config: dict[str, Any]) -> None:
        """Create initial state."""
        super()._create_state(config)

        if self._is_battery_simulation:
            try:
                self._sim_battery_level = float(config.get(CONF_INITIAL_VALUE, 100))
            except (ValueError, TypeError):
                self._sim_battery_level = 100.0
            self._attr_native_value = str(round(self._sim_battery_level, 1))
        elif self._is_load_simulation:
            self._load_state = self._initial_load
            self._control_mode = "auto" if self._cycle_interval else "override"
            self._attr_native_value = str(self._calculate_power())
        else:
            self._attr_native_value = config.get(CONF_INITIAL_VALUE, DEFAULT_SENSOR_VALUE)

    def _restore_state(self, state, config: dict[str, Any]) -> None:
        """Restore state from persistent storage."""
        super()._restore_state(state, config)

        if self._is_battery_simulation:
            if state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN, None):
                try:
                    self._sim_battery_level = float(state.state)
                except (ValueError, TypeError):
                    self._sim_battery_level = 100.0
            else:
                try:
                    self._sim_battery_level = float(config.get(CONF_INITIAL_VALUE, 100))
                except (ValueError, TypeError):
                    self._sim_battery_level = 100.0
            self._attr_native_value = str(round(self._sim_battery_level, 1))
            return

        if self._linked_power_config:
            if state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN, None):
                try:
                    self._energy_accumulator = float(state.state)
                except (ValueError, TypeError):
                    self._energy_accumulator = 0.0
            self._attr_native_value = str(round(self._energy_accumulator, 3))
            return

        if not self._is_load_simulation:
            if state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN, None):
                self._attr_native_value = state.state
            else:
                self._attr_native_value = config.get(CONF_INITIAL_VALUE, DEFAULT_SENSOR_VALUE)
            return

        # Restore load simulation state with null safety (per AGENTS.local.md)
        restored_load = state.attributes.get(ATTR_LOAD_STATE)
        if restored_load in ("active", "standby", "off", "auto"):
            self._load_state = restored_load
        else:
            self._load_state = self._initial_load

        restored_mode = state.attributes.get(ATTR_CONTROL_MODE)
        if restored_mode in ("auto", "override"):
            self._control_mode = restored_mode
        else:
            self._control_mode = "auto" if self._cycle_interval else "override"

        if state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN, None):
            try:
                self._attr_native_value = str(float(state.state))
            except (ValueError, TypeError):
                self._attr_native_value = str(self._calculate_power())
        else:
            self._attr_native_value = str(self._calculate_power())

    def _calculate_power(self) -> float:
        """Calculate current power consumption."""
        if self._linked_switch_state != STATE_ON:
            return 0.0

        if self._load_state == "off":
            base_power = 0.0
        elif self._load_state == "active":
            base_power = self._active_power
        else:
            base_power = self._standby_power

        if self._variance > 0 and base_power > 0:
            jitter = random.uniform(-self._variance, self._variance)
            return max(0.0, round(base_power + jitter, 1))

        return round(base_power, 1)

    def _update_attributes(self) -> None:
        """Update entity attributes."""
        super()._update_attributes()

        if not self._is_load_simulation:
            return

        now = dt_util.utcnow()
        effective_load = self._load_state if self._linked_switch_state == STATE_ON else "off"

        attrs: dict[str, Any] = {
            ATTR_LOAD_STATE: effective_load,
            ATTR_CONTROL_MODE: self._control_mode,
            ATTR_LINKED_SWITCH: self._linked_switch_id or self._linked_switch_config,
        }

        if self._cycle_end_time:
            remaining = max(0, int((self._cycle_end_time - now).total_seconds()))
            attrs[ATTR_CYCLE_ACTIVE] = self._linked_switch_state == STATE_ON
            attrs[ATTR_CYCLE_REMAINING] = remaining
        elif self._cycle_interval and self._load_state == "active" and self._linked_switch_state == STATE_ON:
            attrs[ATTR_CYCLE_ACTIVE] = True
            attrs[ATTR_CYCLE_REMAINING] = 0
        else:
            attrs[ATTR_CYCLE_ACTIVE] = False
            attrs[ATTR_CYCLE_REMAINING] = 0

        if self._next_cycle_start:
            attrs[ATTR_NEXT_CYCLE_START] = self._next_cycle_start.isoformat()

        self._attr_extra_state_attributes.update(attrs)
        if self._linked_power_config:
            self._attr_extra_state_attributes[ATTR_LINKED_POWER] = self._linked_power_id or self._linked_power_config
        if self._is_battery_simulation:
            if self._battery_life_days is not None:
                self._attr_extra_state_attributes["battery_life_days"] = self._battery_life_days
            self._attr_extra_state_attributes["sim_speed"] = self._sim_speed

    def _recalculate_power_and_update(self) -> None:
        """Recalculate power value and write state to Home Assistant."""
        self._attr_native_value = str(self._calculate_power())
        self._update_attributes()
        self.async_write_ha_state()

    def _resolve_sensor_id(self, sensor_config: str | None) -> str | None:
        """Resolve sensor name to entity_id."""
        if not sensor_config:
            return None
        if "." in sensor_config:
            return sensor_config

        slug = slugify(sensor_config)
        candidates = [
            f"sensor.{slug}",
            f"sensor.{COMPONENT_DOMAIN}_{slug}",
        ]
        for c in candidates:
            if self.hass.states.get(c):
                return c
        return candidates[0]

    def _resolve_switch_id(self) -> str | None:
        """Resolve switch name to entity_id."""
        if not self._linked_switch_config:
            return None
        if "." in self._linked_switch_config:
            return self._linked_switch_config

        candidates = [
            f"switch.{slugify(self._linked_switch_config)}",
            f"switch.{COMPONENT_DOMAIN}_{slugify(self._linked_switch_config)}",
        ]
        for candidate in candidates:
            if self.hass.states.get(candidate):
                return candidate
        return candidates[0]

    def _evaluate_schedule(self, now: datetime.datetime) -> None:
        """Evaluate recurring cycle schedule for current time."""
        if not self._cycle_interval or not self._cycle_duration:
            return

        if self._schedule_timer_cancel:
            self._schedule_timer_cancel()
            self._schedule_timer_cancel = None

        if self._cycle_align in ("hour", "clock"):
            seconds_into_hour = (now.minute * 60) + now.second + (now.microsecond / 1_000_000)
            offset_in_interval = seconds_into_hour % self._cycle_interval
        else:
            # Interval relative to epoch
            offset_in_interval = now.timestamp() % self._cycle_interval

        if offset_in_interval < self._cycle_duration:
            # Currently active in cycle window
            self._load_state = "active"
            time_until_active_ends = self._cycle_duration - offset_in_interval
            time_until_next_start = self._cycle_interval - offset_in_interval
            self._next_cycle_start = now + datetime.timedelta(seconds=time_until_next_start)
            delay = time_until_active_ends
        else:
            # Standby window
            self._load_state = "standby"
            time_until_next_start = self._cycle_interval - offset_in_interval
            self._next_cycle_start = now + datetime.timedelta(seconds=time_until_next_start)
            delay = time_until_next_start

        self._schedule_timer_cancel = async_call_later(self.hass, max(1.0, delay), self._on_schedule_tick)

    def _on_switch_state_change(self, new_state: str) -> None:
        """Handle state transition of linked switch."""
        _LOGGER.debug(f"{self.name}: linked switch {self._linked_switch_id} changed to {new_state}")
        self._linked_switch_state = new_state
        self._recalculate_power_and_update()

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to Home Assistant."""
        await super().async_added_to_hass()

        # Set up automatic energy accumulation if linked to a power sensor
        if self._linked_power_config:
            self._linked_power_id = self._resolve_sensor_id(self._linked_power_config)
            if self._linked_power_id:
                st = self.hass.states.get(self._linked_power_id)
                if st and st.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN, None):
                    try:
                        self._last_power_reading = max(0.0, float(st.state))
                    except (ValueError, TypeError):
                        self._last_power_reading = 0.0

                self._last_energy_calc_time = dt_util.utcnow()

                @callback
                def _handle_power_change(event: Event) -> None:
                    new_st = event.data.get("new_state")
                    if new_st is None or new_st.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                        return
                    try:
                        new_p = max(0.0, float(new_st.state))
                        self._accumulate_energy(new_p)
                    except (ValueError, TypeError):
                        pass

                self._power_unsub = async_track_state_change_event(
                    self.hass, [self._linked_power_id], _handle_power_change
                )

                self._energy_interval_unsub = async_track_time_interval(
                    self.hass, self._on_energy_interval, datetime.timedelta(seconds=30)
                )

        # Set up battery drain simulation timer
        if self._is_battery_simulation:
            self._last_battery_calc_time = dt_util.utcnow()
            self._battery_interval_unsub = async_track_time_interval(
                self.hass, self._on_battery_interval, datetime.timedelta(seconds=30)
            )

        if not self._is_load_simulation:
            return

        self._linked_switch_id = self._resolve_switch_id()
        if self._linked_switch_id:
            current_state = self.hass.states.get(self._linked_switch_id)
            if current_state:
                self._linked_switch_state = current_state.state

            @callback
            def _handle_switch_change(event: Event) -> None:
                new_state = event.data.get("new_state")
                if new_state is None:
                    return
                self._on_switch_state_change(new_state.state)

            self._switch_unsub = async_track_state_change_event(
                self.hass, [self._linked_switch_id], _handle_switch_change
            )

        if self._control_mode == "auto" and self._cycle_interval:
            self._evaluate_schedule(dt_util.utcnow())
        self._recalculate_power_and_update()

    async def async_will_remove_from_hass(self) -> None:
        """Clean up timers and subscriptions when entity is removed."""
        if self._switch_unsub:
            self._switch_unsub()
            self._switch_unsub = None
        if self._cycle_timer_cancel:
            self._cycle_timer_cancel()
            self._cycle_timer_cancel = None
        if self._schedule_timer_cancel:
            self._schedule_timer_cancel()
            self._schedule_timer_cancel = None
        if self._power_unsub:
            self._power_unsub()
            self._power_unsub = None
        if self._energy_interval_unsub:
            self._energy_interval_unsub()
            self._energy_interval_unsub = None
        if self._battery_interval_unsub:
            self._battery_interval_unsub()
            self._battery_interval_unsub = None
        await super().async_will_remove_from_hass()

    def _drain_battery(self) -> None:
        """Calculate battery drain over elapsed time."""
        now = dt_util.utcnow()
        if self._last_battery_calc_time is None:
            self._last_battery_calc_time = now
            return

        dt_seconds = (now - self._last_battery_calc_time).total_seconds()
        self._last_battery_calc_time = now
        if dt_seconds <= 0:
            return

        # Calculate drain rate per hour (% / hour)
        if self._battery_life_days and self._battery_life_days > 0:
            drain_per_hour = (100.0 / self._battery_life_days) / 24.0
        elif self._drain_rate and self._drain_rate > 0:
            drain_per_hour = self._drain_rate / 24.0
        else:
            return

        dt_hours = (dt_seconds * self._sim_speed) / 3600.0
        loss = drain_per_hour * dt_hours
        self._sim_battery_level = max(0.0, self._sim_battery_level - loss)
        self._attr_native_value = str(round(self._sim_battery_level, 1))
        self._update_attributes()
        self.async_write_ha_state()

    @callback
    def _on_battery_interval(self, _now=None) -> None:
        """Periodic battery drain step."""
        self._drain_battery()

    def set_sim_speed(self, speed: float) -> None:
        """Set simulation acceleration multiplier."""
        self._sim_speed = max(0.1, float(speed))
        self._update_attributes()
        self.async_write_ha_state()

    def _accumulate_energy(self, new_power: float | None = None) -> None:
        """Integrate power over time into cumulative kWh."""
        now = dt_util.utcnow()
        if self._last_energy_calc_time is None:
            self._last_energy_calc_time = now
            if new_power is not None:
                self._last_power_reading = new_power
            return

        dt_seconds = (now - self._last_energy_calc_time).total_seconds()
        self._last_energy_calc_time = now
        if dt_seconds > 0 and self._last_power_reading > 0:
            dt_hours = dt_seconds / 3600.0
            delta_kwh = (self._last_power_reading * dt_hours) / 1000.0
            self._energy_accumulator += delta_kwh
            self._attr_native_value = str(round(self._energy_accumulator, 3))
            _LOGGER.debug(
                f"{self.name}: accumulated {delta_kwh:.6f} kWh from {self._last_power_reading}W over {dt_seconds:.1f}s -> total {self._energy_accumulator:.3f} kWh"
            )
            self._update_attributes()
            self.async_write_ha_state()

        if new_power is not None:
            self._last_power_reading = new_power

    @callback
    def _on_energy_interval(self, _now=None) -> None:
        """Periodic energy calculation for constant power draws."""
        self._accumulate_energy()

    @callback
    def _on_schedule_tick(self, _tick_time=None) -> None:
        """Handle recurring schedule timer tick."""
        self._schedule_timer_cancel = None
        if self._control_mode == "auto":
            self._evaluate_schedule(dt_util.utcnow())
            self._recalculate_power_and_update()

    @callback
    def _on_cycle_end(self, _now=None) -> None:
        """Handle expiration of a manual cycle timer."""
        self._cycle_timer_cancel = None
        self._cycle_end_time = None
        _LOGGER.debug(f"{self.name}: manual cycle ended")
        if self._cycle_interval:
            self._control_mode = "auto"
            self._evaluate_schedule(dt_util.utcnow())
        else:
            self._control_mode = "override"
            self._load_state = "standby"
        self._recalculate_power_and_update()

    def set(self, value) -> None:
        """Set sensor state value directly."""
        _LOGGER.debug(f"set {self.name} to {value}")
        self._attr_native_value = str(value)
        if self._is_battery_simulation:
            try:
                self._sim_battery_level = max(0.0, min(100.0, float(value)))
                self._last_battery_calc_time = dt_util.utcnow()
            except (ValueError, TypeError):
                pass
        if self._linked_power_config:
            try:
                self._energy_accumulator = float(value)
            except (ValueError, TypeError):
                pass
        self._update_attributes()
        self.async_write_ha_state()

    async def async_run_cycle(self, duration: float | None = None) -> None:
        """Run an active load cycle for a specified duration."""
        if self._cycle_timer_cancel:
            self._cycle_timer_cancel()
            self._cycle_timer_cancel = None

        effective_duration = duration if duration is not None else (self._cycle_duration or 60.0)
        _LOGGER.debug(f"{self.name}: running cycle for {effective_duration}s")

        self._control_mode = "override"
        self._load_state = "active"
        self._cycle_end_time = dt_util.utcnow() + datetime.timedelta(seconds=effective_duration)

        self._cycle_timer_cancel = async_call_later(self.hass, effective_duration, self._on_cycle_end)
        self._recalculate_power_and_update()

    async def async_set_load(self, state: str, power: float | None = None) -> None:
        """Set load state or override power directly."""
        _LOGGER.debug(f"{self.name}: set_load state={state}, power={power}")

        if self._cycle_timer_cancel:
            self._cycle_timer_cancel()
            self._cycle_timer_cancel = None
        self._cycle_end_time = None

        state_lower = state.lower()
        if state_lower == "auto":
            self._control_mode = "auto"
            if self._cycle_interval:
                self._evaluate_schedule(dt_util.utcnow())
            else:
                self._load_state = "standby"
        else:
            self._control_mode = "override"
            self._load_state = state_lower
            if power is not None:
                self._active_power = float(power)

        self._recalculate_power_and_update()
