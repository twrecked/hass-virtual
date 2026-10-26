"""This component provides support for a virtual camera."""
from __future__ import annotations

import base64
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.camera import (
    DOMAIN as PLATFORM_DOMAIN,
    Camera,
    CameraEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import get_entity_configs, get_entity_from_domain
from .const import (
    ATTR_GROUP_NAME,
    ATTR_IMAGE_URL,
    ATTR_STREAM_URL,
    COMPONENT_CONFIG,
    CONF_CLASS,
    CONF_INITIAL_VALUE,
    COMPONENT_DOMAIN,
    COMPONENT_SERVICES,
    CONF_IMAGE_URL,
    CONF_STREAM_URL,
    CONF_YAML_CONFIG,
    DEFAULT_CAMERA_VALUE,
    DEFAULT_IMAGE_URL,
    DEFAULT_STREAM_URL,
    SERVICE_SET_IMAGE_URL,
    SERVICE_SET_STREAM_URL,
)
from .entity import VirtualEntity, virtual_schema

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

# Minimal valid 1x1 gray JPEG image buffer used as offline / fallback placeholder
DEFAULT_FALLBACK_IMAGE_BYTES: bytes = base64.b64decode(
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
)

BASE_SCHEMA = virtual_schema(DEFAULT_CAMERA_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_IMAGE_URL, default=DEFAULT_IMAGE_URL): cv.string,
    vol.Optional(CONF_STREAM_URL, default=DEFAULT_STREAM_URL): cv.string,
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(BASE_SCHEMA)
CAMERA_SCHEMA = vol.Schema(BASE_SCHEMA)

SERVICE_IMAGE_URL_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required(CONF_IMAGE_URL): cv.string,
})

SERVICE_STREAM_URL_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids,
    vol.Required(CONF_STREAM_URL): cv.string,
})


def setup_services(hass: HomeAssistant) -> None:
    """Register virtual camera services."""

    async def async_virtual_service(call: ServiceCall) -> None:
        """Call virtual camera service handler."""
        _LOGGER.debug(f"{call.service} service called")
        for entity_id in call.data[ATTR_ENTITY_ID]:
            entity = get_entity_from_domain(hass, PLATFORM_DOMAIN, entity_id)
            if call.service == SERVICE_SET_IMAGE_URL:
                await entity.async_set_image_url(call.data[CONF_IMAGE_URL])
            elif call.service == SERVICE_SET_STREAM_URL:
                await entity.async_set_stream_url(call.data[CONF_STREAM_URL])

    if PLATFORM_DOMAIN not in hass.data[COMPONENT_SERVICES]:
        _LOGGER.debug("installing camera handlers")
        hass.data[COMPONENT_SERVICES][PLATFORM_DOMAIN] = "installed"
        hass.services.async_register(
            COMPONENT_DOMAIN,
            SERVICE_SET_IMAGE_URL,
            async_virtual_service,
            schema=SERVICE_IMAGE_URL_SCHEMA,
        )
        hass.services.async_register(
            COMPONENT_DOMAIN,
            SERVICE_SET_STREAM_URL,
            async_virtual_service,
            schema=SERVICE_STREAM_URL_SCHEMA,
        )


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up virtual camera from YAML configuration."""
    setup_services(hass)
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")
        cameras = [VirtualCamera(config, True)]
        async_add_entities(cameras, True)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable[[list], None],
) -> None:
    """Set up virtual camera from a config entry."""
    setup_services(hass)
    _LOGGER.debug("setting up the entries...")
    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = CAMERA_SCHEMA(entity)
        entities.append(VirtualCamera(entity, False))
    async_add_entities(entities)


class VirtualCamera(VirtualEntity, Camera):
    """Representation of a Virtual camera."""

    def __init__(self, config: dict[str, Any], old_style: bool):
        """Initialize the Virtual camera device."""
        Camera.__init__(self)
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_device_class = config.get(CONF_CLASS)
        self._image_url: str = config.get(CONF_IMAGE_URL, DEFAULT_IMAGE_URL)
        self._stream_url: str = config.get(CONF_STREAM_URL, DEFAULT_STREAM_URL)
        self._last_image: bytes | None = None

        self._update_features()
        _LOGGER.info(f"VirtualCamera: {self.name} created")

    def _update_features(self) -> None:
        """Update supported features based on stream URL availability."""
        features = CameraEntityFeature.ON_OFF
        if self._stream_url and self._stream_url.strip().lower() not in ("", "none", "null"):
            features |= CameraEntityFeature.STREAM
        self._attr_supported_features = features

    def _create_state(self, config: dict[str, Any]) -> None:
        """Create initial state for a new camera entity."""
        super()._create_state(config)
        raw_state = str(config.get(CONF_INITIAL_VALUE, DEFAULT_CAMERA_VALUE)).lower()
        self._attr_is_on = raw_state != STATE_OFF
        self._image_url = config.get(CONF_IMAGE_URL, DEFAULT_IMAGE_URL)
        self._stream_url = config.get(CONF_STREAM_URL, DEFAULT_STREAM_URL)
        self._update_features()

    def _restore_state(self, state, config: dict[str, Any]) -> None:
        """Restore state from persistent storage across Home Assistant restarts."""
        super()._restore_state(state, config)

        if state.state and state.state.lower() == STATE_OFF:
            self._attr_is_on = False
        else:
            self._attr_is_on = str(config.get(CONF_INITIAL_VALUE, DEFAULT_CAMERA_VALUE)).lower() != STATE_OFF

        image_url = state.attributes.get(ATTR_IMAGE_URL)
        if image_url is not None and isinstance(image_url, str):
            self._image_url = image_url
        else:
            self._image_url = config.get(CONF_IMAGE_URL, DEFAULT_IMAGE_URL)

        stream_url = state.attributes.get(ATTR_STREAM_URL)
        if stream_url is not None and isinstance(stream_url, str):
            self._stream_url = stream_url
        else:
            self._stream_url = config.get(CONF_STREAM_URL, DEFAULT_STREAM_URL)

        self._update_features()

    def _update_attributes(self) -> None:
        """Update entity extra attributes."""
        super()._update_attributes()
        self._attr_extra_state_attributes.update({
            ATTR_IMAGE_URL: self._image_url,
            ATTR_STREAM_URL: self._stream_url,
        })

    async def async_turn_on(self) -> None:
        """Turn the camera on."""
        _LOGGER.debug(f"turning {self.name} on")
        self._attr_is_on = True
        self._update_attributes()
        self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        """Turn the camera off."""
        _LOGGER.debug(f"turning {self.name} off")
        self._attr_is_on = False
        self._update_attributes()
        self.async_write_ha_state()

    async def async_set_image_url(self, image_url: str) -> None:
        """Set the still image URL."""
        _LOGGER.debug(f"setting {self.name} image_url to {image_url}")
        self._image_url = image_url
        self._last_image = None
        self._update_attributes()
        self.async_write_ha_state()

    async def async_set_stream_url(self, stream_url: str) -> None:
        """Set the stream URL."""
        _LOGGER.debug(f"setting {self.name} stream_url to {stream_url}")
        self._stream_url = stream_url
        self._update_features()
        self._update_attributes()
        self.async_write_ha_state()

    async def stream_source(self) -> str | None:
        """Return the stream source URL."""
        if not self._attr_is_on:
            return None
        if self._stream_url and self._stream_url.strip().lower() not in ("", "none", "null"):
            return self._stream_url
        return None

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image for picture entity cards."""
        if not self._attr_is_on:
            return None

        url = self._image_url.strip() if self._image_url else ""
        if not url:
            return DEFAULT_FALLBACK_IMAGE_BYTES

        # HTTP / HTTPS remote URL
        if url.startswith(("http://", "https://")):
            try:
                session = async_get_clientsession(self.hass)
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        content_type = response.headers.get("content-type", "")
                        if "image/png" in content_type:
                            self.content_type = "image/png"
                        elif "image/jpeg" in content_type or "image/jpg" in content_type:
                            self.content_type = "image/jpeg"
                        self._last_image = await response.read()
                        return self._last_image
                    _LOGGER.warning(
                        "Failed to fetch image for %s from %s, HTTP %d",
                        self.name,
                        url,
                        response.status,
                    )
            except Exception as err:
                _LOGGER.warning("Error fetching image for %s from %s: %s", self.name, url, err)

            return self._last_image or DEFAULT_FALLBACK_IMAGE_BYTES

        # Local file path
        if url.startswith("/local/"):
            file_path = Path(self.hass.config.path("www", url[7:]))
        elif url.startswith("/"):
            file_path = Path(url)
        else:
            file_path = Path(self.hass.config.path(url))

        try:
            resolved = file_path.resolve()
            config_dir = Path(self.hass.config.config_dir).resolve()
            # Security: ensure file resides inside the HA config directory
            if config_dir not in resolved.parents and resolved != config_dir:
                _LOGGER.warning("Access to local path outside config dir denied: %s", url)
                return self._last_image or DEFAULT_FALLBACK_IMAGE_BYTES

            def _read_file() -> bytes | None:
                if resolved.is_file():
                    with open(resolved, "rb") as f:
                        return f.read()
                return None

            image_data = await self.hass.async_add_executor_job(_read_file)
            if image_data:
                if resolved.suffix.lower() == ".png":
                    self.content_type = "image/png"
                elif resolved.suffix.lower() in (".jpg", ".jpeg"):
                    self.content_type = "image/jpeg"
                self._last_image = image_data
                return self._last_image
            _LOGGER.warning("File not found or unreadable: %s", resolved)
        except Exception as err:
            _LOGGER.warning("Error reading local image file %s: %s", url, err)

        return self._last_image or DEFAULT_FALLBACK_IMAGE_BYTES
