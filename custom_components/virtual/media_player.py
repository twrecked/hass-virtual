"""This component provides support for a virtual media player."""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.media_player import (
    DOMAIN as PLATFORM_DOMAIN,
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import get_entity_configs
from .const import (
    ATTR_GROUP_NAME,
    COMPONENT_CONFIG,
    COMPONENT_DOMAIN,
    CONF_CLASS,
    CONF_INITIAL_VALUE,
    CONF_INITIAL_VOLUME,
    CONF_SOUND_MODE_LIST,
    CONF_SOURCE_LIST,
    CONF_YAML_CONFIG,
)
from .entity import VirtualEntity, virtual_schema


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [COMPONENT_DOMAIN]

DEFAULT_MEDIA_PLAYER_VALUE = "idle"
DEFAULT_VOLUME = 0.5

STATE_MAP = {
    "off": MediaPlayerState.OFF,
    "on": MediaPlayerState.ON,
    "idle": MediaPlayerState.IDLE,
    "playing": MediaPlayerState.PLAYING,
    "paused": MediaPlayerState.PAUSED,
    "standby": MediaPlayerState.OFF,
    "buffering": MediaPlayerState.BUFFERING,
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(virtual_schema(DEFAULT_MEDIA_PLAYER_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_INITIAL_VOLUME, default=DEFAULT_VOLUME): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
    vol.Optional(CONF_SOURCE_LIST, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_SOUND_MODE_LIST, default=[]): vol.All(cv.ensure_list, [cv.string]),
}))
MEDIA_PLAYER_SCHEMA = vol.Schema(virtual_schema(DEFAULT_MEDIA_PLAYER_VALUE, {
    vol.Optional(CONF_CLASS): cv.string,
    vol.Optional(CONF_INITIAL_VOLUME, default=DEFAULT_VOLUME): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
    vol.Optional(CONF_SOURCE_LIST, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_SOUND_MODE_LIST, default=[]): vol.All(cv.ensure_list, [cv.string]),
}))


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    if hass.data[COMPONENT_CONFIG].get(CONF_YAML_CONFIG, False):
        _LOGGER.debug("setting up old config...")

        players = [VirtualMediaPlayer(config, True)]
        async_add_entities(players, True)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the entries...")

    entities = []
    for entity in get_entity_configs(hass, entry.data[ATTR_GROUP_NAME], PLATFORM_DOMAIN):
        entity = MEDIA_PLAYER_SCHEMA(entity)
        entities.append(VirtualMediaPlayer(entity, False))
    async_add_entities(entities)


class VirtualMediaPlayer(VirtualEntity, MediaPlayerEntity):
    """Representation of a Virtual media player."""

    def __init__(self, config: dict[str, Any], old_style: bool):
        """Initialize the Virtual media player device."""
        super().__init__(config, PLATFORM_DOMAIN, old_style)

        self._attr_device_class = config.get(CONF_CLASS)
        self._attr_source_list = config.get(CONF_SOURCE_LIST, [])
        self._attr_sound_mode_list = config.get(CONF_SOUND_MODE_LIST, [])

        features = (
            MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.STOP
            | MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.PLAY_MEDIA
        )
        if self._attr_source_list:
            features |= MediaPlayerEntityFeature.SELECT_SOURCE
        if self._attr_sound_mode_list:
            features |= MediaPlayerEntityFeature.SELECT_SOUND_MODE

        self._attr_supported_features = features
        _LOGGER.info(f"VirtualMediaPlayer: {self.name} created")

    def _create_state(self, config: dict[str, Any]) -> None:
        super()._create_state(config)

        raw_state = str(config.get(CONF_INITIAL_VALUE, DEFAULT_MEDIA_PLAYER_VALUE)).lower()
        self._attr_state = STATE_MAP.get(raw_state, MediaPlayerState.IDLE)
        self._attr_volume_level = float(config.get(CONF_INITIAL_VOLUME, DEFAULT_VOLUME))
        self._attr_is_volume_muted = False
        self._attr_source = self._attr_source_list[0] if self._attr_source_list else None
        self._attr_sound_mode = self._attr_sound_mode_list[0] if self._attr_sound_mode_list else None
        self._attr_media_title = None
        self._attr_media_artist = None

    def _restore_state(self, state, config: dict[str, Any]) -> None:
        super()._restore_state(state, config)

        if state.state and state.state.lower() in STATE_MAP:
            self._attr_state = STATE_MAP[state.state.lower()]
        else:
            self._attr_state = MediaPlayerState.IDLE

        vol_val = state.attributes.get("volume_level")
        if vol_val is not None:
            try:
                self._attr_volume_level = max(0.0, min(1.0, float(vol_val)))
            except (ValueError, TypeError):
                self._attr_volume_level = float(config.get(CONF_INITIAL_VOLUME, DEFAULT_VOLUME))
        else:
            self._attr_volume_level = float(config.get(CONF_INITIAL_VOLUME, DEFAULT_VOLUME))

        self._attr_is_volume_muted = bool(state.attributes.get("is_volume_muted", False))
        self._attr_source = state.attributes.get("source") or (self._attr_source_list[0] if self._attr_source_list else None)
        self._attr_sound_mode = state.attributes.get("sound_mode") or (self._attr_sound_mode_list[0] if self._attr_sound_mode_list else None)
        self._attr_media_title = state.attributes.get("media_title")
        self._attr_media_artist = state.attributes.get("media_artist")

    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        _LOGGER.debug(f"turning {self.name} on")
        self._attr_state = MediaPlayerState.IDLE
        self._update_attributes()
        self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        _LOGGER.debug(f"turning {self.name} off")
        self._attr_state = MediaPlayerState.OFF
        self._update_attributes()
        self.async_write_ha_state()

    async def async_media_play(self) -> None:
        """Send play command."""
        _LOGGER.debug(f"playing {self.name}")
        self._attr_state = MediaPlayerState.PLAYING
        self._update_attributes()
        self.async_write_ha_state()

    async def async_media_pause(self) -> None:
        """Send pause command."""
        _LOGGER.debug(f"pausing {self.name}")
        self._attr_state = MediaPlayerState.PAUSED
        self._update_attributes()
        self.async_write_ha_state()

    async def async_media_stop(self) -> None:
        """Send stop command."""
        _LOGGER.debug(f"stopping {self.name}")
        self._attr_state = MediaPlayerState.IDLE
        self._update_attributes()
        self.async_write_ha_state()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        _LOGGER.debug(f"setting {self.name} volume to {volume}")
        self._attr_volume_level = max(0.0, min(1.0, float(volume)))
        self._update_attributes()
        self.async_write_ha_state()

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute (true) or unmute (false) media player."""
        _LOGGER.debug(f"setting {self.name} mute to {mute}")
        self._attr_is_volume_muted = bool(mute)
        self._update_attributes()
        self.async_write_ha_state()

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        if source in self._attr_source_list:
            _LOGGER.debug(f"setting {self.name} source to {source}")
            self._attr_source = source
            self._update_attributes()
            self.async_write_ha_state()
        else:
            raise ValueError(f"Invalid source: {source}")

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        """Select sound mode."""
        if sound_mode in self._attr_sound_mode_list:
            _LOGGER.debug(f"setting {self.name} sound mode to {sound_mode}")
            self._attr_sound_mode = sound_mode
            self._update_attributes()
            self.async_write_ha_state()
        else:
            raise ValueError(f"Invalid sound mode: {sound_mode}")

    async def async_play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs: Any
    ) -> None:
        """Play a piece of media or announcement."""
        _LOGGER.debug(f"playing media {media_type}:{media_id} on {self.name}")
        self._attr_media_content_type = media_type
        self._attr_media_content_id = media_id

        # Extract title from extra or URL/text
        extra = kwargs.get("extra", {})
        title = extra.get("title") or media_id.split("/")[-1].split("?")[0]
        self._attr_media_title = title if title else "Media"

        self._attr_state = MediaPlayerState.PLAYING
        self._update_attributes()
        self.async_write_ha_state()
