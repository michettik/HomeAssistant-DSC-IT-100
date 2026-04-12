"""Constants for the Hubitat Alarm integration."""

DOMAIN = "hubitat_alarm"

# Config flow
CONF_HOST = "host"
CONF_PORT = "port"
CONF_ALARM_CODE = "alarm_code"
CONF_ALARM_TYPE = "alarm_type"
CONF_CONNECTION_TYPE = "connection_type"
CONF_NUM_ZONES = "num_zones"

# Defaults
DEFAULT_PORT = 3000
DEFAULT_CONNECTION_TYPE = "wss"
DEFAULT_ALARM_TYPE = "DSC"

# Connection types
CONNECTION_WSS = "wss"
CONNECTION_API = "api"

# Alarm types
ALARM_TYPE_DSC = "DSC"
ALARM_TYPE_HONEYWELL = "Honeywell"

# Alarm states (from HubitatAlarm protocol)
ALARM_STATE_ARMED_AWAY = "armedAway"
ALARM_STATE_ARMED_HOME = "armedHome"
ALARM_STATE_ARMED_NIGHT = "armedNight"
ALARM_STATE_DISARMED = "disarmed"
ALARM_STATE_TRIGGERED = "IN_ALARM"

# Zone states
ZONE_STATE_OPEN = "open"
ZONE_STATE_CLOSED = "close"
ZONE_STATE_ALARM = "alarm"

# Commands
CMD_ARM_AWAY = "alarmArmAway"
CMD_ARM_STAY = "alarmArmStay"
CMD_ARM_NIGHT = "alarmArmNight"
CMD_DISARM = "alarmDisarm"
CMD_UPDATE = "alarmUpdate"
CMD_CHIME_TOGGLE = "alarmChimeToggle"

# Event types
EVENT_TYPE_PARTITION = "partition"
EVENT_TYPE_ZONE = "zone"
