# IPBuilding Home Assistant Integration Plan

## Goal
Integrate the IPBuilding home automation system into Home Assistant using its REST API. The integration will support Relays (Switches), Dimmers (Lights), Buttons, and potentially Regimes.

## User Review Required
- **Access**: The integration requires network access to the IPBuilding controller (default port 30200).
- **Authentication**: Need to confirm if the API requires an API key or authentication. (User provided URL implies open access or IP-based trust).
- **Location**: Since the current workspace is `ESPHome`, I will generate the custom component files in a new directory `ipbuilding_integration` which you can then copy to your Home Assistant `custom_components` directory.

## Proposed Changes

### Structure
We will create a standard Home Assistant Custom Component structure:

```text
ipbuilding/
  __init__.py
  manifest.json
  const.py
  config_flow.py
  api.py
  light.py
  switch.py
  button.py
  sensor.py
```

## Proposed Changes

### Structure
We will create a standard Home Assistant Custom Component structure in a local directory `ipbuilding_integration/custom_components/ipbuilding`. You will need to copy the `ipbuilding` folder to your Home Assistant `config/custom_components/` directory.

### Component Details

#### [NEW] [api.py](file:///Users/markminnoye/git/HA IPBuilding/custom_components/ipbuilding/api.py)
- **Assumptions**:
    - API is accessible without auth.
    - `GET /api/v1/comp/items` returns a list of devices.
    - `GET /api/v1/action/action?id={id}&actionType={ACTION}&value={value}` (or similar) sets device state. See https://www.postman.com/soft-techbv/ipbrestapi-s-public-workspace/request/6uctjo4/send-an-action for details. Actions include ON, OFF, TOGGLE, DIM.
- **Functionality**:
    - `get_devices(type_ids)`: Fetch devices.
    - `set_value(device_id, value)`: Control device.

#### [NEW] [config_flow.py](file:///Users/markminnoye/git/HA IPBuilding/custom_components/ipbuilding/config_flow.py)
- Standard config flow to input Host (e.g., `192.168.0.185`) and Port (e.g., `30200`).

#### [NEW] [light.py](file:///Users/markminnoye/git/HA IPBuilding/custom_components/ipbuilding/light.py)
- **Type 2 (Dimmer)**.
- Maps 0-100% brightness to API values (likely 0-100 or 0-255).

#### [NEW] [switch.py](file:///Users/markminnoye/git/HA IPBuilding/custom_components/ipbuilding/switch.py)
- **Type 1 (Relais)**.
- Simple On/Off control.

#### [NEW] [button.py](file:///Users/markminnoye/git/HA IPBuilding/custom_components/ipbuilding/button.py)
- **Type 50 (Button)**.
- Stateless button press.

#### [NEW] [sensor.py](file:///Users/markminnoye/git/HA IPBuilding/custom_components/ipbuilding/sensor.py)
- **Type 56 (Time)**, **Type 200 (Regime)**.
- Read-only state.

#### [NEW] [const.py](file:///Users/markminnoye/git/HA IPBuilding/custom_components/ipbuilding/const.py)
- Constants for domain, default port, etc.

#### [NEW] [manifest.json](file:///Users/markminnoye/git/HA IPBuilding/custom_components/ipbuilding/manifest.json)
- Component metadata.

## Verification Plan
### Manual Verification
1.  Copy `ipbuilding_integration/custom_components/ipbuilding` to your Home Assistant `custom_components/` folder.
2.  Restart Home Assistant.
3.  Go to Settings -> Devices & Services -> Add Integration -> Search "IPBuilding".
4.  Enter IP `192.168.0.185` and Port `30200`.
5.  Check if devices are discovered.
6.  **Critical**: Test controlling a light. If it fails, check logs for API errors (404/400) which would indicate my assumption about the `POST` endpoint is wrong.
