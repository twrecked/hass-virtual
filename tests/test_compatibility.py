"""Exercise supported units and tracker behavior across Home Assistant APIs."""

import importlib
import logging
from unittest.mock import AsyncMock, patch

import homeassistant.const as ha_const
import pytest
from homeassistant.core import State
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.setup import async_setup_component

from custom_components.virtual import device_tracker, number, sensor
from custom_components.virtual.const import ATTR_AVAILABLE


def test_units_without_removed_constants():
    """Current platforms must import even if legacy constants are unavailable."""
    if not hasattr(ha_const, "UnitOfDensity") or not hasattr(ha_const, "UnitOfRatio"):
        pytest.skip("This runtime uses the compatibility fallback")
    original = ha_const.__getattr__

    def without_legacy_constants(name):
        if name in {
            "CONCENTRATION_MICROGRAMS_PER_CUBIC_METER",
            "CONCENTRATION_PARTS_PER_MILLION",
        }:
            raise AttributeError(name)
        return original(name)

    with patch.object(ha_const, "__getattr__", without_legacy_constants):
        importlib.reload(sensor)
        importlib.reload(number)


@pytest.mark.parametrize("platform", [sensor, number])
@pytest.mark.parametrize(
    "class_name", ["CO", "CO2", "PM25", "VOLATILE_ORGANIC_COMPOUNDS"]
)
def test_concentration_unit_values(platform, class_name):
    """The enum migration must preserve existing units and stored values."""
    enum = sensor.SensorDeviceClass if platform is sensor else number.NumberDeviceClass
    density = getattr(ha_const, "UnitOfDensity", None)
    expected = (
        "ppm"
        if class_name in {"CO", "CO2"}
        else (density.MICROGRAMS_PER_CUBIC_METER if density else "µg/m³")
    )
    assert platform.UNITS_OF_MEASUREMENT[getattr(enum, class_name)] == expected


def test_tracker_import_without_location_deprecation(caplog):
    """Creating the tracker class must not register a removed property API."""
    with caplog.at_level(logging.WARNING):
        importlib.reload(device_tracker)
    assert "overriding the deprecated location_name" not in caplog.text


async def add_tracker(hass, *, initial="home", restored=None):
    """Register the actual entity and let its restore lifecycle run."""
    tracker = device_tracker.VirtualDeviceTracker(
        device_tracker.DEVICE_TRACKER_SCHEMA(
            {"name": "Test Tracker", "initial_value": initial}
        )
    )
    tracker.async_get_last_state = AsyncMock(return_value=restored)
    component = EntityComponent(logging.getLogger(__name__), "device_tracker", hass)
    await component.async_add_entities([tracker])
    await hass.async_block_till_done()
    assert hass.states.get(tracker.entity_id) is not None
    return tracker


@pytest.mark.parametrize("location", ["home", "not_home", "Test Location"])
async def test_named_location_initial_move_and_restore(hass, location):
    """Preserve virtual labels on initial setup, service moves and restore."""
    restored = State("device_tracker.test_tracker", location, {ATTR_AVAILABLE: True})
    tracker = await add_tracker(hass, initial=location, restored=restored)
    assert hass.states.get(tracker.entity_id).state == location
    tracker.move_to_location("Another Location")
    await hass.async_block_till_done()
    assert hass.states.get(tracker.entity_id).state == "Another Location"
    assert tracker.latitude is None
    assert tracker.longitude is None


async def test_initial_location_without_restore(hass):
    """A new entity uses its configured initial value."""
    tracker = await add_tracker(hass, initial="Test Location")
    assert hass.states.get(tracker.entity_id).state == "Test Location"


async def setup_zones(hass):
    """Use public synthetic coordinates for an actual Home Assistant zone."""
    hass.config.latitude = 0
    hass.config.longitude = 0
    assert await async_setup_component(
        hass,
        "zone",
        {
            "zone": [
                {
                    "name": "Test Work",
                    "latitude": 37.8267,
                    "longitude": -122.4233,
                    "radius": 100,
                }
            ]
        },
    )


async def test_gps_zone_transitions_and_named_location(hass):
    """Retain base-class GPS zone handling when replacing location_name."""
    await setup_zones(hass)
    tracker = await add_tracker(hass)
    for latitude, longitude, expected in [
        (37.8267, -122.4233, "Test Work"),
        (10, 10, "not_home"),
        (0, 0, "home"),
    ]:
        tracker.move_to_coords({"latitude": latitude, "longitude": longitude}, 5)
        await hass.async_block_till_done()
        state = hass.states.get(tracker.entity_id)
        assert state.state == expected
        assert state.attributes["gps_accuracy"] == 5
    tracker.move_to_location("Test Location")
    await hass.async_block_till_done()
    state = hass.states.get(tracker.entity_id)
    assert state.state == "Test Location"
    assert "latitude" not in state.attributes


async def test_gps_restore_keeps_coordinates_and_accuracy(hass):
    """GPS restore must keep its accuracy and use current zone matching."""
    await setup_zones(hass)
    restored = State(
        "device_tracker.test_tracker",
        "Test Work",
        {
            ATTR_AVAILABLE: True,
            "latitude": 37.8267,
            "longitude": -122.4233,
            "gps_accuracy": 17,
        },
    )
    tracker = await add_tracker(hass, restored=restored)
    state = hass.states.get(tracker.entity_id)
    assert state.state == "Test Work"
    assert state.attributes["latitude"] == 37.8267
    assert state.attributes["longitude"] == -122.4233
    assert state.attributes["gps_accuracy"] == 17


async def test_old_restore_format_uses_configured_initial_value(hass):
    """Preserve the existing fallback for records without virtual metadata."""
    tracker = await add_tracker(
        hass,
        initial="Test Location",
        restored=State("device_tracker.test_tracker", "old"),
    )
    assert hass.states.get(tracker.entity_id).state == "Test Location"
