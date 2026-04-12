"""Config flow for Hubitat Alarm integration."""
import logging
from typing import Any

import voluptuous as vol
import aiohttp
import async_timeout

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_ALARM_CODE,
    CONF_ALARM_TYPE,
    CONF_CONNECTION_TYPE,
    CONF_NUM_ZONES,
    DEFAULT_PORT,
    DEFAULT_CONNECTION_TYPE,
    DEFAULT_ALARM_TYPE,
    CONNECTION_WSS,
    CONNECTION_API,
    ALARM_TYPE_DSC,
    ALARM_TYPE_HONEYWELL,
)

_LOGGER = logging.getLogger(__name__)


async def validate_connection(hass: HomeAssistant, host: str, port: int) -> dict[str, Any]:
    """Validate the connection to the Hubitat Alarm server."""
    url = f"http://{host}:{port}/"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(10):
                async with session.get(url) as response:
                    if response.status == 200:
                        text = await response.text()
                        if "Hubitat Alarm Running" in text:
                            return {"title": f"Hubitat Alarm ({host})"}
                    raise ConnectionError("Invalid response from server")
    except Exception as err:
        raise ConnectionError(f"Connection failed: {err}") from err
