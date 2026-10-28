"""Thermal HVAC Simulation Engine supporting electric and gas heating."""
from __future__ import annotations

import datetime
import logging
from collections.abc import Callable
from typing import Any

from homeassistant.components.climate import HVACMode
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.util import dt as dt_util, slugify

from ..const import (
    COMPONENT_DOMAIN,
    CONF_BLOWER_POWER,
    CONF_CLIMATE_ENTITY,
    CONF_COOL_POWER_STAGE1,
    CONF_COOL_POWER_STAGE2,
    CONF_COOL_RATE_STAGE1,
    CONF_COOL_RATE_STAGE2,
    CONF_FAN_COOL_RATE,
    CONF_FAN_POWER,
    CONF_GAS_ENERGY_SENSOR,
    CONF_GAS_FLOW_STAGE1,
    CONF_GAS_FLOW_STAGE2,
    CONF_GAS_SENSOR,
    CONF_HEAT_POWER_STAGE1,
    CONF_HEAT_POWER_STAGE2,
    CONF_HEAT_RATE_STAGE1,
    CONF_HEAT_RATE_STAGE2,
    CONF_HEATING_TYPE,
    CONF_HOUSE_LEAKAGE_RATE,
    CONF_INDOOR_SENSOR,
    CONF_OUTDOOR_SENSOR,
    CONF_POWER_SENSOR,
    CONF_SIM_SPEED,
    CONF_STANDBY_POWER,
    CONF_TICK_INTERVAL,
    DEFAULT_BLOWER_POWER,
    DEFAULT_CLIMATE_STANDBY_POWER,
    DEFAULT_COOL_POWER_STAGE1,
    DEFAULT_COOL_POWER_STAGE2,
    DEFAULT_COOL_RATE_STAGE1,
    DEFAULT_COOL_RATE_STAGE2,
    DEFAULT_FAN_COOL_RATE,
    DEFAULT_FAN_POWER,
    DEFAULT_GAS_FLOW_STAGE1,
    DEFAULT_GAS_FLOW_STAGE2,
    DEFAULT_HEAT_POWER_STAGE1,
    DEFAULT_HEAT_POWER_STAGE2,
    DEFAULT_HEAT_RATE_STAGE1,
    DEFAULT_HEAT_RATE_STAGE2,
    DEFAULT_HOUSE_LEAKAGE_RATE,
    DEFAULT_SIM_SPEED,
    DEFAULT_TICK_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class ThermalHvacSimulation:
    """Simulates physical house thermal dynamics and HVAC conditioning with electric or gas heat."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]):
        self.hass = hass
        self._config = config
        self.name: str = config.get("name", "Thermal HVAC Engine")
        self._heating_type: str = str(config.get(CONF_HEATING_TYPE, "electric")).lower()

        # Linked entities
        self._climate_entity_config: str | None = config.get(CONF_CLIMATE_ENTITY)
        self._indoor_sensor_config: str | None = config.get(CONF_INDOOR_SENSOR)
        self._outdoor_sensor_config: str | None = config.get(CONF_OUTDOOR_SENSOR)
        self._power_sensor_config: str | None = config.get(CONF_POWER_SENSOR)
        self._gas_sensor_config: str | None = config.get(CONF_GAS_SENSOR)
        self._gas_energy_sensor_config: str | None = config.get(CONF_GAS_ENERGY_SENSOR)

        # Performance rates (°C / hour)
        self._heat_rate_stage1: float = float(config.get(CONF_HEAT_RATE_STAGE1, DEFAULT_HEAT_RATE_STAGE1))
        self._heat_rate_stage2: float = float(config.get(CONF_HEAT_RATE_STAGE2, DEFAULT_HEAT_RATE_STAGE2))
        self._cool_rate_stage1: float = float(config.get(CONF_COOL_RATE_STAGE1, DEFAULT_COOL_RATE_STAGE1))
        self._cool_rate_stage2: float = float(config.get(CONF_COOL_RATE_STAGE2, DEFAULT_COOL_RATE_STAGE2))
        self._fan_cool_rate: float = float(config.get(CONF_FAN_COOL_RATE, DEFAULT_FAN_COOL_RATE))

        # Electric power ratings (Watts)
        self._heat_power_stage1: float = float(config.get(CONF_HEAT_POWER_STAGE1, DEFAULT_HEAT_POWER_STAGE1))
        self._heat_power_stage2: float = float(config.get(CONF_HEAT_POWER_STAGE2, DEFAULT_HEAT_POWER_STAGE2))
        self._cool_power_stage1: float = float(config.get(CONF_COOL_POWER_STAGE1, DEFAULT_COOL_POWER_STAGE1))
        self._cool_power_stage2: float = float(config.get(CONF_COOL_POWER_STAGE2, DEFAULT_COOL_POWER_STAGE2))
        self._fan_power: float = float(config.get(CONF_FAN_POWER, DEFAULT_FAN_POWER))
        self._standby_power: float = float(config.get(CONF_STANDBY_POWER, DEFAULT_CLIMATE_STANDBY_POWER))
        self._blower_power: float = float(config.get(CONF_BLOWER_POWER, DEFAULT_BLOWER_POWER))

        # Gas furnace flow ratings (m³/hr)
        self._gas_flow_stage1: float = float(config.get(CONF_GAS_FLOW_STAGE1, DEFAULT_GAS_FLOW_STAGE1))
        self._gas_flow_stage2: float = float(config.get(CONF_GAS_FLOW_STAGE2, DEFAULT_GAS_FLOW_STAGE2))

        # House leakage and timing
        self._house_leakage_rate: float = float(config.get(CONF_HOUSE_LEAKAGE_RATE, DEFAULT_HOUSE_LEAKAGE_RATE))
        self._tick_interval: float = max(1.0, float(config.get(CONF_TICK_INTERVAL, DEFAULT_TICK_INTERVAL)))
        self._sim_speed: float = max(0.1, float(config.get(CONF_SIM_SPEED, DEFAULT_SIM_SPEED)))

        # Internal simulation states
        self._sim_current_temp: float = 20.0
        self._outdoor_temp: float = 20.0
        self._hvac_stage: str = "idle"
        self._hvac_power: float = 0.0
        self._gas_flow: float = 0.0
        self._cumulative_gas: float = 0.0
        self._cumulative_power_kwh: float = 0.0

        self._last_tick_time: datetime.datetime | None = None
        self._unsub_timer: Callable[[], None] | None = None
        self._unsub_outdoor: Callable[[], None] | None = None

        _LOGGER.info(
            f"ThermalHvacSimulation created: {self.name} (type={self._heating_type}, speed={self._sim_speed}x)"
        )

    def _resolve_id(self, domain: str, config_name: str | None) -> str | None:
        """Resolve entity name to entity_id."""
        if not config_name:
            return None
        if "." in config_name:
            return config_name

        slug = slugify(config_name)
        candidates = [
            f"{domain}.{slug}",
            f"{domain}.{COMPONENT_DOMAIN}_{slug}",
        ]
        for c in candidates:
            if self.hass.states.get(c):
                return c
        return candidates[0]

    def _update_sensor(self, sensor_config: str | None, value_str: str) -> None:
        """Update a virtual sensor entity."""
        eid = self._resolve_id("sensor", sensor_config)
        if not eid:
            return
        try:
            from .. import get_entity_from_domain
            entity = get_entity_from_domain(self.hass, "sensor", eid)
            entity.set(value_str)
        except Exception as err:
            _LOGGER.debug(f"Could not update sensor {eid}: {err}")

    def _evaluate_hvac_stage(
        self, hvac_mode: str, cur_temp: float, target_temp: float
    ) -> tuple[str, float, float, float]:
        """Determine active stage, temperature delta rate (°C/hr), electric power (W), and gas flow (m³/hr)."""
        mode = hvac_mode.lower()
        if mode in ("off", "none"):
            return ("off", 0.0, 0.0, 0.0)

        # Cooling
        if mode == "cool" or (mode in ("auto", "heat_cool") and cur_temp > target_temp + 0.5):
            if cur_temp > target_temp:
                if (cur_temp - target_temp) > 1.5 or self._outdoor_temp > 30.0:
                    return ("stage2_cool", -self._cool_rate_stage2, self._cool_power_stage2, 0.0)
                return ("stage1_cool", -self._cool_rate_stage1, self._cool_power_stage1, 0.0)
            return ("idle", 0.0, self._standby_power, 0.0)

        # Heating
        if mode == "heat" or (mode in ("auto", "heat_cool") and cur_temp < target_temp - 0.5):
            if cur_temp < target_temp:
                is_stage2 = (target_temp - cur_temp) > 1.5 or self._outdoor_temp < 0.0
                rate = self._heat_rate_stage2 if is_stage2 else self._heat_rate_stage1
                stage = "stage2_heat" if is_stage2 else "stage1_heat"

                if self._heating_type == "gas":
                    gas = self._gas_flow_stage2 if is_stage2 else self._gas_flow_stage1
                    power = self._blower_power
                else:
                    gas = 0.0
                    power = self._heat_power_stage2 if is_stage2 else self._heat_power_stage1

                return (stage, rate, power, gas)
            return ("idle", 0.0, self._standby_power, 0.0)

        # Fan only
        if mode == "fan_only":
            return ("fan", -self._fan_cool_rate, self._fan_power, 0.0)

        return ("idle", 0.0, self._standby_power, 0.0)

    def _step_simulation(self) -> None:
        """Execute one step of the thermal physics loop."""
        now = dt_util.utcnow()
        if self._last_tick_time is None:
            self._last_tick_time = now
            return

        dt_seconds = (now - self._last_tick_time).total_seconds()
        self._last_tick_time = now
        if dt_seconds <= 0:
            return

        dt_hours = (dt_seconds * self._sim_speed) / 3600.0

        # Read thermostat state
        climate_id = self._resolve_id("climate", self._climate_entity_config)
        hvac_mode = "heat"
        target_temp = 21.0
        if climate_id:
            st = self.hass.states.get(climate_id)
            if st:
                hvac_mode = st.state
                raw_target = st.attributes.get("temperature")
                if raw_target is not None:
                    try:
                        target_temp = float(raw_target)
                    except (ValueError, TypeError):
                        pass

        # Passive heat leakage towards outdoor temperature
        cur_temp = self._sim_current_temp
        delta_ambient = self._outdoor_temp - cur_temp
        leak_rate = self._house_leakage_rate * (delta_ambient / 10.0)
        dt_leak = leak_rate * dt_hours

        # Active HVAC conditioning
        stage, hvac_rate, power, gas_flow = self._evaluate_hvac_stage(hvac_mode, cur_temp, target_temp)
        self._hvac_stage = stage
        self._hvac_power = power
        self._gas_flow = gas_flow
        dt_hvac = hvac_rate * dt_hours

        # Compute net unrounded temperature
        new_temp = cur_temp + dt_leak + dt_hvac

        # Clamp: passive leakage alone cannot cross ambient outdoor temp
        if hvac_rate == 0.0:
            if delta_ambient > 0 and new_temp > self._outdoor_temp:
                new_temp = self._outdoor_temp
            elif delta_ambient < 0 and new_temp < self._outdoor_temp:
                new_temp = self._outdoor_temp

        new_temp = max(5.0, min(40.0, new_temp))
        self._sim_current_temp = new_temp
        reported_temp = round(new_temp, 1)

        # Integrate energy & gas
        if power > 0:
            self._cumulative_power_kwh += (power * dt_hours) / 1000.0
        if gas_flow > 0:
            self._cumulative_gas += gas_flow * dt_hours

        # Update climate entity
        if climate_id:
            try:
                from .. import get_entity_from_domain
                clim_ent = get_entity_from_domain(self.hass, "climate", climate_id)
                clim_ent.set_current_temperature(reported_temp)
            except Exception as err:
                _LOGGER.debug(f"Could not update climate {climate_id}: {err}")

        # Update linked sensors
        self._update_sensor(self._indoor_sensor_config, str(reported_temp))
        self._update_sensor(self._power_sensor_config, str(round(power, 1)))
        self._update_sensor(self._gas_sensor_config, str(round(gas_flow, 2)))
        self._update_sensor(self._gas_energy_sensor_config, str(round(self._cumulative_gas, 3)))

    @callback
    def _on_tick(self, _now=None) -> None:
        """Timer callback for simulation step."""
        self._step_simulation()

    def start(self) -> None:
        """Start the simulation timers and subscriptions."""
        if self._unsub_timer:
            return

        # Initialize outdoor temp from outdoor sensor if present
        outdoor_id = self._resolve_id("sensor", self._outdoor_sensor_config)
        if outdoor_id:
            st = self.hass.states.get(outdoor_id)
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
                try:
                    self._outdoor_temp = float(new_state.state)
                    self._step_simulation()
                except (ValueError, TypeError):
                    pass

            self._unsub_outdoor = async_track_state_change_event(
                self.hass, [outdoor_id], _handle_outdoor_change
            )

        # Initialize current temperature from indoor sensor or climate
        indoor_id = self._resolve_id("sensor", self._indoor_sensor_config)
        if indoor_id:
            st = self.hass.states.get(indoor_id)
            if st and st.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN, None):
                try:
                    self._sim_current_temp = float(st.state)
                except (ValueError, TypeError):
                    pass

        self._last_tick_time = dt_util.utcnow()
        self._unsub_timer = async_track_time_interval(
            self.hass, self._on_tick, datetime.timedelta(seconds=self._tick_interval)
        )
        self._step_simulation()
        _LOGGER.info(f"Started Thermal HVAC simulation: {self.name}")

    def stop(self) -> None:
        """Stop the simulation timer and subscriptions."""
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
        if self._unsub_outdoor:
            self._unsub_outdoor()
            self._unsub_outdoor = None
        _LOGGER.info(f"Stopped Thermal HVAC simulation: {self.name}")

    def set_sim_speed(self, speed: float) -> None:
        """Set simulation acceleration multiplier."""
        self._sim_speed = max(0.1, float(speed))
        _LOGGER.debug(f"{self.name}: Set sim speed to {self._sim_speed}x")
        self._step_simulation()
