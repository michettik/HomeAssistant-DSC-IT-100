from __future__ import annotations

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
    except async_timeout.TimeoutError as err:
        raise ConnectionError("Connection timeout") from err
    except aiohttp.ClientError as err:
        raise ConnectionError(f"Connection failed: {err}") from err


class HubitatAlarmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hubitat Alarm."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_connection(
                    self.hass,
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                )
            except ConnectionError as err:
                _LOGGER.error("Connection error: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Required(CONF_ALARM_CODE): cv.string,
                vol.Required(
                    CONF_CONNECTION_TYPE, default=DEFAULT_CONNECTION_TYPE
                ): vol.In([CONNECTION_WSS, CONNECTION_API]),
                vol.Required(CONF_ALARM_TYPE, default=DEFAULT_ALARM_TYPE): vol.In(
                    [ALARM_TYPE_DSC, ALARM_TYPE_HONEYWELL]
                ),
                vol.Optional(CONF_NUM_ZONES, default=8): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=64)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return HubitatAlarmOptionsFlowHandler(config_entry)


class HubitatAlarmOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Hubitat Alarm."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NUM_ZONES,
                        default=self.config_entry.data.get(CONF_NUM_ZONES, 8),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=64)),
                }
            ),
        )
