"""
Hubitat Alarm Integration for Home Assistant.
Connects to the HubitatAlarm Docker container running on a remote server.
"""
import logging
import asyncio
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import HubitatAlarmCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Hubitat Alarm component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hubitat Alarm from a config entry."""
    coordinator = HubitatAlarmCoordinator(hass, entry)
    
    try:
        await coordinator.async_connect()
    except Exception as err:
        _LOGGER.error("Failed to connect to Hubitat Alarm server: %s", err)
        raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        coordinator: HubitatAlarmCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_disconnect()

    return unload_ok
