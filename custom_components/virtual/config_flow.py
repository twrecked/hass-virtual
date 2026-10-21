"""Config flow for Virtual components."""
from __future__ import annotations

import base64
import logging
import os
from typing import Any
from urllib.parse import quote
import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.components import webhook
from homeassistant.core import callback

from .const import (
    ATTR_FILE_NAME,
    ATTR_GROUP_NAME,
    COMPONENT_DOMAIN,
    CONF_EDITOR_URL,
    DEFAULT_EDITOR_URL,
    IMPORTED_GROUP_NAME,
    default_config_file,
)
from .cfg import UpgradeCfg

_LOGGER = logging.getLogger(__name__)


class VirtualFlowHandler(config_entries.ConfigFlow, domain=COMPONENT_DOMAIN):
    """Virtual config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return VirtualOptionsFlowHandler()

    async def validate_input(self, user_input: dict[str, Any]) -> dict[str, str]:
        for group, values in self.hass.data.get(COMPONENT_DOMAIN, {}).items():
            _LOGGER.debug(f"checking {group}")
            if group == user_input[ATTR_GROUP_NAME]:
                raise GroupNameAlreadyUsed
            if values[ATTR_FILE_NAME] == user_input[ATTR_FILE_NAME]:
                raise FileNameAlreadyUsed
        return {
            "title": f"{user_input[ATTR_GROUP_NAME]} - {COMPONENT_DOMAIN}"
        }

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        _LOGGER.debug(f"step user {user_input}")

        errors = {}
        if user_input is not None:
            try:
                info = await self.validate_input(user_input)
                return self.async_create_entry(title=info["title"], data={
                    ATTR_GROUP_NAME: user_input[ATTR_GROUP_NAME],
                    ATTR_FILE_NAME: user_input[ATTR_FILE_NAME],
                })
            except GroupNameAlreadyUsed:
                errors["base"] = "group_name_used"
            except FileNameAlreadyUsed:
                errors["base"] = "file_name_used"

        else:
            # Fill in some defaults.
            user_input = {
                ATTR_GROUP_NAME: IMPORTED_GROUP_NAME,
                ATTR_FILE_NAME: default_config_file(self.hass)
            }

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({
                vol.Required(ATTR_GROUP_NAME, default=user_input[ATTR_GROUP_NAME]): str,
                vol.Required(ATTR_FILE_NAME, default=user_input[ATTR_FILE_NAME]): str
            }),
            errors=errors
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> config_entries.ConfigFlowResult:
        """Import momentary config from configuration.yaml."""

        _LOGGER.debug(f"importing virtual YAML {import_data}")
        await UpgradeCfg.async_import_yaml(self.hass, import_data)
        data = UpgradeCfg.create_flow_data(self.hass, import_data)

        return self.async_create_entry(
            title="Imported Virtual Group",
            data=data
        )


class GroupNameAlreadyUsed(exceptions.HomeAssistantError):
    """ Error indicating group name already used. """


class FileNameAlreadyUsed(exceptions.HomeAssistantError):
    """ Error indicating file name already used. """


class VirtualOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Virtual integration."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        entry = self.config_entry
        editor_url = entry.options.get(CONF_EDITOR_URL, DEFAULT_EDITOR_URL)

        if user_input is not None:
            new_editor_url = user_input.get(CONF_EDITOR_URL, editor_url)
            return self.async_create_entry(
                title="",
                data={CONF_EDITOR_URL: new_editor_url},
            )

        file_name = entry.data.get(ATTR_FILE_NAME, default_config_file(self.hass))
        group_name = entry.data.get(ATTR_GROUP_NAME, "virtual")

        yaml_content = ""
        def _read() -> str:
            if os.path.exists(file_name):
                with open(file_name, "r", encoding="utf-8") as f:
                    return f.read()
            return ""

        try:
            yaml_content = await self.hass.async_add_executor_job(_read)
        except Exception as err:
            _LOGGER.debug("Could not read %s: %s", file_name, err)

        webhook_id = f"virtual_{entry.entry_id}"
        token = (
            self.hass.data.get(COMPONENT_DOMAIN, {})
            .get(entry.entry_id, {})
            .get("webhook_token", "")
        )

        try:
            webhook_url = webhook.async_generate_url(self.hass, webhook_id, allow_internal=True, allow_external=True)
        except Exception:
            webhook_url = f"/api/webhook/{webhook_id}"

        cb_param = f"{webhook_url}?token={token}" if "?" not in webhook_url else f"{webhook_url}&token={token}"

        encoded_yaml = base64.b64encode(yaml_content.encode("utf-8")).decode("ascii")
        builder_url = (
            f"{editor_url}/?cb={quote(cb_param, safe='')}"
            f"&token={quote(token)}"
            f"&name={quote(group_name)}"
            f"#data={encoded_yaml}"
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_EDITOR_URL, default=editor_url): str,
            }),
            description_placeholders={
                "builder_url": builder_url,
                "group_name": group_name,
                "file_name": file_name,
            },
        )
