# HA-IPBuilding

Home Assistant custom integration for **IPBuilding** smart living systems.

This integration lets you control IPBuilding-driven functions such as lights, scenes (sferen), ventilation, zone heating and other building automation features directly from Home Assistant.

> This integration communicates directly with the **IPBox** controller over its IP-based API.  
> Other IPBuilding hardware (switch modules, dimmers, etc.) is not accessed individually; all
> control happens via the IPBox.

## Features

- Discover and control IPBuilding **lights** and **switches**
- Trigger IPBuilding **scenes / sferen** from Home Assistant
- Control **ventilation** modes and other climate-related functions
- Map IPBuilding entities to Home Assistant entities for dashboards and automations
- Designed for both residential and assisted-living / workspace deployments

> IPBuilding provides a central IP-based platform for smart living, workspaces and assisted living (lighting, heating, access control, energy management, emergency call, etc.). This integration aims to bring that platform into Home Assistant.

## Requirements

- A working IPBuilding installation with an **IPBox** controller
- Network access from your Home Assistant instance to the IPBox
- API/controller access on the IPBox (IP address/hostname, port and credentials, depending on your setup)
- Home Assistant 2024.x or newer 

## Installation

### HACS (recommended – if/when published)

1. Add this repository as a **Custom repository** in HACS.
2. Search for **HA-IPBuilding** in HACS.
3. Install the integration and **restart Home Assistant**.

### Manual installation

1. Copy the `custom_components/ipbuilding` directory from this repository  
   into your Home Assistant `config/custom_components` folder.

   Final path:

   - `config/custom_components/ipbuilding`

2. Restart Home Assistant.

## Configuration

Configuration is done via `configuration.yaml` (or via the UI if you add a Config Flow later).

Basic example:

```yaml
ipbuilding:
  host: 192.168.1.50
  port: 12345
  username: "ha_integration"
  password: "your-password"
  # Optional filters / mappings
  include_lights: true
  include_switches: true
  include_scenes: true
  include_ventilation: true
