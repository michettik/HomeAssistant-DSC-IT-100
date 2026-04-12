# Hubitat Alarm for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Home Assistant integration for Hubitat Alarm - connects to DSC and Honeywell alarm systems via the HubitatAlarm Docker container.

## Features

- 🔐 **Alarm Control Panel** - Arm/Disarm in Away, Home, and Night modes
- 🚪 **Zone Sensors** - Binary sensors for all alarm zones
- 🔌 **WebSocket or API** - Choose between real-time WebSocket or polling API
- 🏠 **Local Push** - No cloud required, all local communication
- 🔄 **Auto-Reconnect** - Automatic reconnection if connection is lost
- 🎯 **HACS Ready** - Easy installation and updates via HACS

## Prerequisites

You need the [HubitatAlarm Docker container](https://github.com/Welasco/HubitatAlarm) running on a server (e.g., Raspberry Pi) that has physical access to your alarm panel via:
- DSC IT-100 (Serial/USB)
- Envisalink (Network)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add this repository URL: `https://github.com/yourusername/hubitat_alarm_hacs`
5. Select category: "Integration"
6. Click "Add"
7. Click "Install" on the Hubitat Alarm card
8. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/hubitat_alarm` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Hubitat Alarm"
4. Enter your configuration:
   - **Host**: IP address of your Docker container (e.g., `192.168.1.100`)
   - **Port**: Port number (default: `3000`)
   - **~~Alarm Security Code~~**: ~~Your alarm panel code~~ (See Docker Container Setup below for manual configuration)
   - **Connection Type**: Choose `wss` (WebSocket - recommended) or `api`
   - **Alarm Type**: Choose `DSC` or `Honeywell`
   - **Number of Zones**: How many zones to create (1-64)

## Docker Container Setup

Make sure you have the HubitatAlarm Docker container running:

```bash
# For DSC IT-100
docker run --name=hubitatalarm -d -p 3000:3000 \
  -v /path/to/config:/opt/Alarm/config \
  --device=/dev/ttyUSB0 \
  -e TZ=America/Chicago \
  --restart always \
  welasco/hubitatalarm:latest

# For Envisalink
docker run --name=hubitatalarm -d -p 3000:3000 \
  -v /path/to/config:/opt/Alarm/config \
  -e TZ=America/Chicago \
  --restart always \
  welasco/hubitatalarm:latest
```

## Entities Created

### Alarm Control Panel
- **Entity ID**: `alarm_control_panel.hubitat_alarm_panel`
- **States**: Disarmed, Armed Home, Armed Away, Armed Night, Triggered
- **Services**: 
  - `alarm_control_panel.alarm_arm_home`
  - `alarm_control_panel.alarm_arm_away`
  - `alarm_control_panel.alarm_arm_night`
  - `alarm_control_panel.alarm_disarm`

### Binary Sensors (Zones)
- **Entity IDs**: `binary_sensor.zone_1` through `binary_sensor.zone_N`
- **States**: On (open/triggered), Off (closed)
- **Device Class**: Door

## Example Automation

```yaml
automation:
  - alias: "Alarm Triggered Notification"
    trigger:
      - platform: state
        entity_id: alarm_control_panel.hubitat_alarm_panel
        to: "triggered"
    action:
      - service: notify.mobile_app
        data:
          title: "🚨 ALARM TRIGGERED!"
          message: "The alarm system has been triggered!"

  - alias: "Front Door Opened When Armed"
    trigger:
      - platform: state
        entity_id: binary_sensor.zone_1
        to: "on"
    condition:
      - condition: not
        conditions:
          - condition: state
            entity_id: alarm_control_panel.hubitat_alarm_panel
            state: "disarmed"
    action:
      - service: notify.mobile_app
        data:
          message: "Front door opened while alarm is armed!"
```

## Lovelace Card Example

```yaml
type: alarm-panel
entity: alarm_control_panel.hubitat_alarm_panel
states:
  - arm_away
  - arm_home
  - arm_night
```

## Troubleshooting

### Connection Issues
- Verify the Docker container is running: `docker ps | grep hubitatalarm`
- Check Docker logs: `docker logs hubitatalarm`
- Test connectivity: `curl http://YOUR_IP:3000/`
- Ensure port 3000 is accessible from Home Assistant

### WebSocket Issues
- Try switching to API mode in the integration options
- Check firewall rules between Home Assistant and Docker host
- Verify no reverse proxy is interfering with WebSocket connections

### Zone Not Updating
- Verify the zone number is configured correctly
- Check if zones are properly configured in the Docker container
- Enable debug logging (see below)

## Debug Logging

Add to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.hubitat_alarm: debug
```

## Support

- [GitHub Issues](https://github.com/yourusername/hubitat_alarm_hacs/issues)
- [HubitatAlarm Docker Container](https://github.com/Welasco/HubitatAlarm)

## Credits

Based on the [HubitatAlarm](https://github.com/Welasco/HubitatAlarm) project by Victor Santana.

## License

MIT License
