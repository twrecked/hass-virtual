"""Simulation engine manager for Virtual components."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .solar_inverter import SolarInverterSimulation
from .thermal_hvac import ThermalHvacSimulation

_LOGGER = logging.getLogger(__name__)


class SimulationManager:
    """Manages lifecycle of all active virtual simulations."""

    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self._simulations: dict[str, list[Any]] = {}

    async def async_setup_simulations(
        self, entry: ConfigEntry, simulations_config: list[dict[str, Any]]
    ) -> None:
        """Instantiate and start simulations configured for an entry."""
        if not simulations_config:
            return

        active_list = []
        for sim_cfg in simulations_config:
            sim_type = sim_cfg.get("type", "").lower()
            if sim_type in ("solar_inverter", "solark", "sol_ark", "inverter", "energy_hub"):
                sim = SolarInverterSimulation(self.hass, sim_cfg)
                sim.start()
                active_list.append(sim)
            elif sim_type in ("thermal_hvac", "hvac", "house_thermal", "climate_sim", "furnace"):
                sim = ThermalHvacSimulation(self.hass, sim_cfg)
                sim.start()
                active_list.append(sim)
            else:
                _LOGGER.warning(f"Unknown simulation type: {sim_type}")

        self._simulations[entry.entry_id] = active_list

    async def async_unload_simulations(self, entry: ConfigEntry) -> None:
        """Stop and unload simulations for an entry."""
        active_list = self._simulations.pop(entry.entry_id, [])
        for sim in active_list:
            sim.stop()

    def set_battery_soc(self, soc: float, name: str | None = None) -> None:
        """Set battery SoC across active inverter simulations."""
        for sim_list in self._simulations.values():
            for sim in sim_list:
                if isinstance(sim, SolarInverterSimulation):
                    if name is None or sim.name.lower() == name.lower():
                        sim.set_battery_soc(soc)

    def set_solar_power(self, power: float | str, name: str | None = None) -> None:
        """Set solar power across active inverter simulations."""
        for sim_list in self._simulations.values():
            for sim in sim_list:
                if isinstance(sim, SolarInverterSimulation):
                    if name is None or sim.name.lower() == name.lower():
                        sim.set_solar_power(power)

    def set_sim_speed(self, speed: float, name: str | None = None) -> None:
        """Set simulation speed across active simulations."""
        for sim_list in self._simulations.values():
            for sim in sim_list:
                if hasattr(sim, "set_sim_speed"):
                    if name is None or sim.name.lower() == name.lower():
                        sim.set_sim_speed(speed)
