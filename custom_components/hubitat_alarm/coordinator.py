from __future__ import annotations

"""Coordinator for Hubitat Alarm integration."""
import asyncio
import json
import logging
from typing import Any

import aiohttp
import websockets

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    CONF_ALARM_CODE,
    CONF_CONNECTION_TYPE,
    CONNECTION_WSS,
    EVENT_TYPE_PARTITION,
    EVENT_TYPE_ZONE,
)

_LOGGER = logging.getLogger(__name__)

RECONNECT_DELAY = 10  # seconds


class HubitatAlarmCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Hubitat Alarm connection."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )
        self.entry = entry
        self.host = entry.data[CONF_HOST]
        self.port = entry.data[CONF_PORT]
        self.alarm_code = entry.data[CONF_ALARM_CODE]
        self.connection_type = entry.data[CONF_CONNECTION_TYPE]
        
        self.websocket: websockets.WebSocketClientProtocol | None = None
        self._reconnect_task: asyncio.Task | None = None
        self._listen_task: asyncio.Task | None = None
        
        # Store alarm state
        self.partition_data: dict[str, Any] = {}
        self.zone_data: dict[str, Any] = {}

    @property
    def is_connected(self) -> bool:
        """Return True if connected."""
        if self.connection_type == CONNECTION_WSS:
            return self.websocket is not None
        return True  # API mode doesn't maintain persistent connection

    async def async_connect(self) -> None:
        """Connect to the Hubitat Alarm server."""
        # Sync alarm code to Docker container
        await self.async_sync_alarm_config()
        
        if self.connection_type == CONNECTION_WSS:
            await self._async_connect_websocket()
        else:
            # API mode - just verify connection
            await self._async_verify_api_connection()

    async def async_sync_alarm_config(self) -> None:
        """Sync alarm configuration to Docker container."""
        url = f"http://{self.host}:{self.port}/config"
        
        config_data = {
            "alarmpassword": self.alarm_code,
            "SHM": True,
            "alarmType": "DSC",
            "connectionType": "DSC-IT100",
            "communicationType": "WSS"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"alarm": config_data}) as response:
                    if response.status == 200:
                        _LOGGER.info("Successfully synced alarm code to Docker container")
                    else:
                        _LOGGER.warning("Failed to sync alarm config: HTTP %s", response.status)
        except Exception as err:
            _LOGGER.error("Failed to sync alarm config to Docker: %s", err)

    async def _async_connect_websocket(self) -> None:
        """Connect via WebSocket."""
        url = f"ws://{self.host}:{self.port}/wss"
        
        try:
            self.websocket = await websockets.connect(url, ping_interval=60)
            _LOGGER.info("Connected to Hubitat Alarm WebSocket at %s", url)
            
            # Start listening for messages
            if self._listen_task is None or self._listen_task.done():
                self._listen_task = asyncio.create_task(self._async_listen_websocket())
            
            # Request initial status update
            await self.async_send_command("alarmUpdate")
            
        except Exception as err:
            _LOGGER.error("Failed to connect to WebSocket: %s", err)
            # Schedule reconnection
            self._schedule_reconnect()
            raise

    async def _async_listen_websocket(self) -> None:
        """Listen for WebSocket messages."""
        _LOGGER.info("WebSocket listener started")
        try:
            async for message in self.websocket:
                try:
                    _LOGGER.info("Received WebSocket message: %s", message)
                    data = json.loads(message)
                    await self._async_handle_message(data)
                except json.JSONDecodeError as err:
                    _LOGGER.error("Failed to decode JSON message: %s", err)
                except Exception as err:
                    _LOGGER.exception("Error handling message: %s", err)
        except websockets.ConnectionClosed:
            _LOGGER.warning("WebSocket connection closed")
            self._schedule_reconnect()
        except Exception as err:
            _LOGGER.exception("WebSocket listener error: %s", err)
            self._schedule_reconnect()

    async def _async_verify_api_connection(self) -> None:
        """Verify API connection."""
        url = f"http://{self.host}:{self.port}/"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ConnectionError(f"HTTP {response.status}")
                text = await response.text()
                if "Hubitat Alarm Running" not in text:
                    raise ConnectionError("Invalid response from server")
        
        _LOGGER.info("Verified API connection to Hubitat Alarm at %s:%s", self.host, self.port)

    def _schedule_reconnect(self) -> None:
        """Schedule a reconnection attempt."""
        if self._reconnect_task is None or self._reconnect_task.done():
            self._reconnect_task = asyncio.create_task(self._async_reconnect())

    async def _async_reconnect(self) -> None:
        """Reconnect after a delay."""
        await asyncio.sleep(RECONNECT_DELAY)
        _LOGGER.info("Attempting to reconnect to Hubitat Alarm...")
        try:
            await self._async_connect_websocket()
        except Exception as err:
            _LOGGER.error("Reconnection failed: %s", err)

    async def async_disconnect(self) -> None:
        """Disconnect from the server."""
        if self._listen_task:
            self._listen_task.cancel()
            
        if self._reconnect_task:
            self._reconnect_task.cancel()
            
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def _async_handle_message(self, data: dict[str, Any]) -> None:
        """Handle incoming message from alarm system."""
        event_type = data.get("type")
        _LOGGER.info("Handling message - type: %s, data: %s", event_type, data)
        
        if event_type == EVENT_TYPE_PARTITION:
            # Update partition state
            partition = data.get("partition", "1")
            self.partition_data[partition] = data
            _LOGGER.info("Updated partition %s state: %s", partition, data)
            
        elif event_type == EVENT_TYPE_ZONE:
            # Update zone state
            zone = data.get("zone")
            if zone:
                self.zone_data[zone] = data
                _LOGGER.debug("Zone %s update: %s", zone, data)
        
        # Notify all listeners
        _LOGGER.info("Notifying listeners of update")
        self.async_set_updated_data(data)

    async def async_send_command(self, command: str, code: str | None = None) -> None:
        """Send command to alarm system."""
        if self.connection_type == CONNECTION_WSS:
            await self._async_send_command_websocket(command, code)
        else:
            await self._async_send_command_api(command, code)

    async def _async_send_command_websocket(self, command: str, code: str | None = None) -> None:
        """Send command via WebSocket."""
        if not self.websocket:
            _LOGGER.error("WebSocket not connected")
            return
        
        message_data = {"command": command}
        if code is not None:
            message_data["code"] = code
        message = json.dumps(message_data)
        try:
            await self.websocket.send(message)
            _LOGGER.info("Sent command via WebSocket: %s (message: %s)", command, message)
        except Exception as err:
            _LOGGER.error("Failed to send WebSocket command: %s", err)
            self._schedule_reconnect()

    async def _async_send_command_api(self, command: str, code: str | None = None) -> None:
        """Send command via API."""
        url = f"http://{self.host}:{self.port}/api/{command}"
        if code is not None:
            url += f"?code={code}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        _LOGGER.error("API command failed with status %s", response.status)
                    _LOGGER.debug("Sent command via API: %s", url)
        except Exception as err:
            _LOGGER.error("Failed to send API command: %s", err)

    def get_partition_state(self, partition: str = "1") -> dict[str, Any] | None:
        """Get current state of a partition."""
        return self.partition_data.get(partition)

    def get_zone_state(self, zone: str) -> dict[str, Any] | None:
        """Get current state of a zone."""
        return self.zone_data.get(zone)
