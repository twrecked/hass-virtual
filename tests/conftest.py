"""Run the integration tests with native Home Assistant fixtures."""

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def enable_virtual(enable_custom_integrations):
    """Allow the local custom integration in Home Assistant."""
