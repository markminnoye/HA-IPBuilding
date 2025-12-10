# IPBuilding Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/markminnoye/ipbuilding?include_prereleases&style=flat-square)](https://github.com/markminnoye/ipbuilding/releases)

The `ipbuilding` component allows you to integrate your [IPBuilding](https://ipbuilding.com/) home automation system into Home Assistant. It automatically discovers and controls lights, switches, scenes, sensors, and more.

## Features

*   **Automatic Discovery**: Automatically finds all configured devices in your IPBuilding system.
*   **Device Support**:
    *   **Lights**: Dimmers and Relays (configured as lights).
    *   **Switches**: Outlets, locks, fans, valves, and other relay-based devices.
    *   **Sensors**: Temperature, Motion, Energy, Weather, Time, and Regime.
    *   **Covers/Screens**: (Future support planned).
    *   **Climate**: Thermostats (Future support planned).
*   **Scene Support**: Activates Spheres and TempSpheres directly from Home Assistant.
*   **Grouping**: Devices are automatically organized into Hubs (e.g., "IPBuilding Dimmers", "IPBuilding Relays") while maintaining their Room/Area assignments.
*   **Power Monitoring**: Automatically creates power sensors for devices that have a configured wattage in IPBuilding.
*   **Real-time Updates**: States are updated via polling (configurable).

## Installation

### Option 1: HACS (Recommended)

1.  Open **HACS** in Home Assistant.
2.  Go to **Integrations** > **Three dots (top right)** > **Custom repositories**.
3.  Add `https://github.com/markminnoye/ipbuilding` with category **Integration**.
4.  Click **Add** and then install the **IPBuilding** integration.
5.  Restart Home Assistant.

### Option 2: Manual Installation

1.  Download the latest release.
2.  Copy the `custom_components/ipbuilding` directory to your Home Assistant's `custom_components` directory.
3.  Restart Home Assistant.

## Configuration

1.  Go to **Settings** > **Devices & Services**.
2.  Click **Add Integration** in the bottom right corner.
3.  Search for **IPBuilding**.
4.  Enter the **Host** (IP address) and **Port** of your IPBuilding system (e.g., `192.168.0.185` and `30200`).
5.  Click **Submit**.

Your devices will immediately appear in Home Assistant.

## Supported Devices

The integration maps IPBuilding "Types" and "Kinds" to Home Assistant entities:

| IPBuilding Type      | HA Entity      | Description                                           |
| :------------------- | :------------- | :---------------------------------------------------- |
| **Relay (1)**        | Light / Switch | Mapped to Light if Kind is 'Light', otherwise Switch. |
| **Dimmer (2)**       | Light          | Supports brightness control.                          |
| **Button (50)**      | Button         | Stateless button to trigger events.                   |
| **Time (56)**        | Sensor         | System time sensor.                                   |
| **Regime (200)**     | Sensor         | Current regime (Day/Night/Away/etc).                  |
| **Sphere (100)**     | Scene          | Activates a pre-defined scene.                        |
| **TempSphere (101)** | Scene          | Temporary scene.                                      |
| **Energy (40/41)**   | Sensor         | Energy counters and meters.                           |
| **Analog (53)**      | Sensor         | Generic analog sensors.                               |

### Device Organization

Devices are organized in two ways:
1.  **By Room**: Each device tells Home Assistant which room it belongs to (via the IPBuilding "Group" property).
2.  **By Category**: Devices are also linked to virtual Hubs (e.g., "IPBuilding Dimmers") to easily view all devices of a certain type.

## Advanced Usage

### Entity Visibility
*   **Visible Property**: If a device is hidden in IPBuilding (Visible=False), it will be marked as `unavailable` in Home Assistant.
*   **Buttons**: Button entities are disabled by default to avoid clutter. You can enable them in the entity settings.

### Power Sensors
For every device that has a `Watt` value configured in IPBuilding, a corresponding power sensor (sensor.device_name_power) is created. This allows for easy integration with the Home Assistant Energy Dashboard.

## Troubleshooting

Enable debug logging to see what's happening under the hood:

```yaml
logger:
  default: info
  logs:
    custom_components.ipbuilding: debug
```

## Credits

Created by [Mark Minnoye](https://github.com/markminnoye).