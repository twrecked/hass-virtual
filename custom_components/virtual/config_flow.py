"""Config flow for Aarlo"""

import logging
import voluptuous as vol
from typing import Any

from homeassistant import config_entries
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME
)
from homeassistant.core import callback

from .const import (
    COMPONENT_DOMAIN
)
from .cfg import UpgradeCfg

_LOGGER = logging.getLogger(__name__)


class AarloFlowHandler(config_entries.ConfigFlow, domain=COMPONENT_DOMAIN):
    """Aarlo config flow."""

    VERSION = 1

    async def async_step_import(self, import_data):
        """Import momentary config from configuration.yaml."""

        _LOGGER.info("importing aarlo YAML")
        UpgradeCfg.create_file_config(import_data)
        data = UpgradeCfg.create_flow_data(import_data)

        return self.async_create_entry(
            title=f"Imported Virtual Group",
            data=data
        )
