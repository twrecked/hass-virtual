"""Generic Solar Inverter & Energy Hub Simulation Engine."""
from __future__ import annotations

import datetime
import logging
import math
from collections.abc import Callable
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util, slugify

from ..const import COMPONENT_DOMAIN

_LOGGER = logging.getLogger(__name__)

DEFAULT_PEAK_SOLAR_POWER = 11000.0  # 11 kW
DEFAULT_BASE_LOAD = 250.0            # 250 W
DEFAULT_BATTERY_CAPACITY = 15.0      # 15 kWh
DEFAULT_BATTERY_MIN_SOC = 20.0       # 20 %
DEFAULT_BATTERY_MAX_POWER = 5000.0   # 5 kW
DEFAULT_TICK_INTERVAL = 10.0         # 10 seconds
DEFAULT_SIM_SPEED = 1.0


class SolarInverterSimulation:
    """Simulates a hybrid solar inverter, battery storage, and grid power flow balancing."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]):
        self.hass = hass
        self._config = config
        self.name: str = config.get("name", "Solar Inverter")

        self._peak_solar_power: float = float(config.get("peak_solar_power", DEFAULT_PEAK_SOLAR_POWER))
        self._base_load: float = float(config.get("base_load", DEFAULT_BASE_LOAD))
        self._battery_capacity: float = float(config.get("battery_capacity", DEFAULT_BATTERY_CAPACITY))
        self._battery_min_soc: float = float(config.get("battery_min_soc", DEFAULT_BATTERY_MIN_SOC))
        self._battery_max_power: float = float(config.get("battery_max_power", DEFAULT_BATTERY_MAX_POWER))
        self._tick_interval: float = max(1.0, float(config.get("tick_interval", DEFAULT_TICK_INTERVAL)))
        self._sim_speed: float = max(0.1, float(config.get("sim_speed", DEFAULT_SIM_SPEED)))

        # Linked sensors
        self._pv_power_sensor: str | None = config.get("pv_power_sensor")
        self._pv_energy_sensor: str | None = config.get("pv_energy_sensor")
        self._grid_power_sensor: str | None = config.get("grid_power_sensor")
        self._grid_energy_in_sensor: str | None = config.get("grid_energy_in_sensor")
        self._grid_energy_out_sensor: str | None = config.get("grid_energy_out_sensor")
        self._load_power_sensor: str | None = config.get("load_power_sensor")
        self._load_energy_sensor: str | None = config.get("load_energy_sensor")
        self._battery_power_sensor: str | None = config.get("battery_power_sensor")
        self._battery_soc_sensor: str | None = config.get("battery_soc_sensor")
        self._battery_voltage_sensor: str | None = config.get("battery_voltage_sensor")
        self._battery_energy_in_sensor: str | None = config.get("battery_energy_in_sensor")
        self._battery_energy_out_sensor: str | None = config.get("battery_energy_out_sensor")

        self._linked_loads: list[str] = config.get("linked_loads", [])

        # Simulation states
        self._solar_power_override: float | None = None
        self._battery_soc: float = 85.0
        self._battery_energy_stored: float = (85.0 / 100.0) * self._battery_capacity

        # Cumulative energy accumulators (kWh)
        self._pv_energy: float = 0.0
        self._grid_energy_in: float = 0.0
        self._grid_energy_out: float = 0.0
        self._load_energy: float = 0.0
        self._battery_energy_in: float = 0.0
        self._battery_energy_out: float = 0.0

        self._last_tick_time: datetime.datetime | None = None
        self._unsub_timer: Callable[[], None] | None = None

        _LOGGER.info(f"SolarInverterSimulation created: {self.name} (peak_solar={self._peak_solar_power}W)")

    def _resolve_sensor_id(self, sensor_config: str | None) -> str | None:
        """Resolve friendly sensor name to entity_id."""
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

    def _update_sensor(self, sensor_config: str | None, value_str: str) -> None:
        """Update a virtual sensor entity directly."""
        eid = self._resolve_sensor_id(sensor_config)
        if not eid:
            return
        try:
            from .. import get_entity_from_domain
            entity = get_entity_from_domain(self.hass, "sensor", eid)
            entity.set(value_str)
        except Exception as err:
            _LOGGER.debug(f"Could not update sensor {eid}: {err}")

    def _calculate_solar_power(self, now: datetime.datetime) -> float:
        """Calculate current solar PV output based on diurnal sun curve."""
        if self._solar_power_override is not None:
            return self._solar_power_override

        local_now = dt_util.as_local(now)
        hour = local_now.hour + (local_now.minute / 60.0) + (local_now.second / 3600.0)

        # Solar window: sunrise at 06:00, sunset at 19:30 (13.5 hours daylight)
        sunrise = 6.0
        sunset = 19.5
        if sunrise <= hour <= sunset:
            progress = (hour - sunrise) / (sunset - sunrise)
            solar_fraction = math.sin(progress * math.pi)
            return max(0.0, round(self._peak_solar_power * solar_fraction, 1))

        return 0.0

    def _calculate_total_load(self) -> float:
        """Calculate total instantaneous house load (baseload + linked virtual appliances)."""
        total = self._base_load
        for item in self._linked_loads:
            eid = self._resolve_sensor_id(item)
            if not eid:
                continue
            st = self.hass.states.get(eid)
            if st and st.state:
                try:
                    val = float(st.state)
                    total += max(0.0, val)
                except (ValueError, TypeError):
                    pass
        return round(total, 1)

    def _step_simulation(self) -> None:
        """Perform one simulation step balancing solar, battery, grid, and load."""
        now = dt_util.utcnow()
        if self._last_tick_time is None:
            self._last_tick_time = now
            return

        dt_seconds = (now - self._last_tick_time).total_seconds()
        self._last_tick_time = now
        if dt_seconds <= 0:
            return

        dt_hours = (dt_seconds * self._sim_speed) / 3600.0

        solar_power = self._calculate_solar_power(now)
        load_power = self._calculate_total_load()
        delta_power = solar_power - load_power

        min_stored_kwh = self._battery_capacity * (self._battery_min_soc / 100.0)
        max_stored_kwh = self._battery_capacity

        battery_power = 0.0
        grid_power = 0.0

        if delta_power > 0:
            # Surplus solar: powers house, charges battery, exports remaining excess
            surplus = delta_power
            room_kwh = max(0.0, max_stored_kwh - self._battery_energy_stored)
            max_charge_watts = min(self._battery_max_power, (room_kwh / dt_hours) * 1000.0) if dt_hours > 0 else self._battery_max_power

            charge_watts = min(surplus, max_charge_watts) if room_kwh > 0 else 0.0
            battery_power = charge_watts  # Positive = charging
            grid_power = -(surplus - charge_watts)  # Negative = exporting to grid

        elif delta_power < 0:
            # Deficit: solar provides what it can, battery discharges down to 20%, grid supplies rest
            deficit = abs(delta_power)
            avail_kwh = max(0.0, self._battery_energy_stored - min_stored_kwh)
            max_discharge_watts = min(self._battery_max_power, (avail_kwh / dt_hours) * 1000.0) if dt_hours > 0 else self._battery_max_power

            discharge_watts = min(deficit, max_discharge_watts) if avail_kwh > 0 else 0.0
            battery_power = -discharge_watts  # Negative = discharging
            grid_power = deficit - discharge_watts  # Positive = importing from grid

        else:
            battery_power = 0.0
            grid_power = 0.0

        # Energy accumulation (kWh)
        delta_e_pv = (solar_power * dt_hours) / 1000.0
        self._pv_energy += delta_e_pv

        delta_e_load = (load_power * dt_hours) / 1000.0
        self._load_energy += delta_e_load

        if battery_power > 0:
            delta_e_batt = (battery_power * dt_hours) / 1000.0
            self._battery_energy_stored = min(max_stored_kwh, self._battery_energy_stored + delta_e_batt)
            self._battery_energy_in += delta_e_batt
        elif battery_power < 0:
            delta_e_batt = (abs(battery_power) * dt_hours) / 1000.0
            self._battery_energy_stored = max(min_stored_kwh, self._battery_energy_stored - delta_e_batt)
            self._battery_energy_out += delta_e_batt

        self._battery_soc = round(max(0.0, min(100.0, (self._battery_energy_stored / self._battery_capacity) * 100.0)), 1)
        battery_voltage = round(48.0 + (6.0 * (self._battery_soc / 100.0)), 1)

        if grid_power > 0:
            delta_e_grid = (grid_power * dt_hours) / 1000.0
            self._grid_energy_in += delta_e_grid
        elif grid_power < 0:
            delta_e_grid = (abs(grid_power) * dt_hours) / 1000.0
            self._grid_energy_out += delta_e_grid

        _LOGGER.debug(
            f"{self.name}: tick - pv={solar_power}W, load={load_power}W, "
            f"battery={battery_power}W (soc={self._battery_soc}%), grid={grid_power}W"
        )

        # Push updates to linked virtual sensors
        self._update_sensor(self._pv_power_sensor, str(round(solar_power, 1)))
        self._update_sensor(self._pv_energy_sensor, str(round(self._pv_energy, 2)))
        self._update_sensor(self._load_power_sensor, str(round(load_power, 1)))
        self._update_sensor(self._load_energy_sensor, str(round(self._load_energy, 2)))
        self._update_sensor(self._battery_power_sensor, str(round(battery_power, 1)))
        self._update_sensor(self._battery_soc_sensor, str(round(self._battery_soc, 1)))
        self._update_sensor(self._battery_voltage_sensor, str(battery_voltage))
        self._update_sensor(self._battery_energy_in_sensor, str(round(self._battery_energy_in, 2)))
        self._update_sensor(self._battery_energy_out_sensor, str(round(self._battery_energy_out, 2)))
        self._update_sensor(self._grid_power_sensor, str(round(grid_power, 1)))
        self._update_sensor(self._grid_energy_in_sensor, str(round(self._grid_energy_in, 2)))
        self._update_sensor(self._grid_energy_out_sensor, str(round(self._grid_energy_out, 2)))

    @callback
    def _on_tick(self, _now=None) -> None:
        """Timer callback for simulation step."""
        self._step_simulation()

    def start(self) -> None:
        """Start the simulation timer."""
        if self._unsub_timer:
            return
        self._last_tick_time = dt_util.utcnow()
        self._unsub_timer = async_track_time_interval(
            self.hass, self._on_tick, datetime.timedelta(seconds=self._tick_interval)
        )
        self._step_simulation()
        _LOGGER.info(f"Started simulation: {self.name}")

    def stop(self) -> None:
        """Stop the simulation timer."""
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
        _LOGGER.info(f"Stopped simulation: {self.name}")

    def set_battery_soc(self, soc: float) -> None:
        """Manually set battery State of Charge percentage for testing."""
        self._battery_soc = max(0.0, min(100.0, float(soc)))
        self._battery_energy_stored = (self._battery_soc / 100.0) * self._battery_capacity
        _LOGGER.debug(f"{self.name}: Set battery SoC to {self._battery_soc}%")
        self._step_simulation()

    def set_solar_power(self, power: float | str) -> None:
        """Manually set solar power wattage, or 'auto' to resume diurnal curve."""
        if str(power).lower() == "auto":
            self._solar_power_override = None
            _LOGGER.debug(f"{self.name}: Solar power set to auto curve")
        else:
            self._solar_power_override = max(0.0, float(power))
            _LOGGER.debug(f"{self.name}: Solar power overridden to {self._solar_power_override}W")
        self._step_simulation()
