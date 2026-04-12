from __future__ import annotations

"""Alarm control panel platform for Hubitat Alarm."""
import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_ALARM_CODE,
    ALARM_STATE_ARMED_AWAY,
    ALARM_STATE_ARMED_HOME,
    ALARM_STATE_ARMED_NIGHT,
    ALARM_STATE_DISARMED,
    ALARM_STATE_TRIGGERED,
    CMD_ARM_AWAY,
    CMD_ARM_STAY,
    CMD_ARM_NIGHT,
    CMD_DISARM,
)
from .coordinator import HubitatAlarmCoordinator

_LOGGER = logging.getLogger(__name__)

# Map HubitatAlarm states to HA states
STATE_MAP = {
    ALARM_STATE_ARMED_AWAY: AlarmControlPanelState.ARMED_AWAY,
    ALARM_STATE_ARMED_HOME: AlarmControlPanelState.ARMED_HOME,
    ALARM_STATE_ARMED_NIGHT: AlarmControlPanelState.ARMED_NIGHT,
    ALARM_STATE_DISARMED: AlarmControlPanelState.DISARMED,
    ALARM_STATE_TRIGGERED: AlarmControlPanelState.TRIGGERED,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hubitat Alarm control panel from a config entry."""
    coordinator: HubitatAlarmCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    async_add_entities([HubitatAlarmPanel(coordinator, entry)], True)


class HubitatAlarmPanel(AlarmControlPanelEntity):
    """Representation of a Hubitat Alarm Panel."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_NIGHT
    )

    def __init__(
        self, coordinator: HubitatAlarmCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the alarm panel."""
        self.coordinator = coordinator
        self._entry = entry
        self._alarm_code = entry.data[CONF_ALARM_CODE]
        self._attr_unique_id = f"{entry.entry_id}_alarm_panel"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "DSC Alarm Panel",
            "manufacturer": "HomeAssistant-DSC-IT-100",
            "model": entry.data.get("alarm_type", "DSC IT-100"),
            "sw_version": "1.0.2",
        }

    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.is_connected

    @property
    def state(self) -> str | None:
        """Return the state of the alarm."""
        partition_state = self.coordinator.get_partition_state("1")
        if not partition_state:
            return None
        
        alarm_state = partition_state.get("hsmstate") or partition_state.get("state")
        return STATE_MAP.get(alarm_state, AlarmControlPanelState.DISARMED)

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes."""
        partition_state = self.coordinator.get_partition_state("1")
        if not partition_state:
            return {}
        
        return {
            "partition": partition_state.get("partition"),
            "description": partition_state.get("description"),
            "raw_state": partition_state.get("state"),
        }

    @property
    def code_arm_required(self) -> bool:
        """Whether the code is required for arm actions."""
        return False

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        _LOGGER.info("Disarm button clicked - sending command: %s with code", CMD_DISARM)
        alarm_code = code or self._alarm_code
        await self.coordinator.async_send_command(CMD_DISARM, code=alarm_code)
        _LOGGER.info("Disarm command sent with code: %s", alarm_code)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        _LOGGER.info("Arm Home button clicked - sending command: %s with code", CMD_ARM_STAY)
        alarm_code = code or self._alarm_code
        await self.coordinator.async_send_command(CMD_ARM_STAY, code=alarm_code)
        _LOGGER.info("Arm Home command sent with code: %s", alarm_code)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        _LOGGER.info("Arm Away button clicked - sending command: %s with code", CMD_ARM_AWAY)
        alarm_code = code or self._alarm_code
        await self.coordinator.async_send_command(CMD_ARM_AWAY, code=alarm_code)
        _LOGGER.info("Arm Away command sent with code: %s", alarm_code)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night command."""
        _LOGGER.info("Arm Night button clicked - sending command: %s with code", CMD_ARM_NIGHT)
        alarm_code = code or self._alarm_code
        await self.coordinator.async_send_command(CMD_ARM_NIGHT, code=alarm_code)
        _LOGGER.info("Arm Night command sent with code: %s", alarm_code)
