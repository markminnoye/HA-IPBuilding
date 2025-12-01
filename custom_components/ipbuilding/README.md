# IPBuilding Custom Component

## Overview

This Home Assistant custom component provides integration with the IPBuilding system. It allows you to control dimmers, retrieve sensor data, and trigger custom actions via the IPBuilding REST API.

## Important API Endpoints

### Dimmer Control

- **Endpoint**: `GET http://192.168.0.185:30200/api/v1/action/action?id=571&actionType=DIM&value=10`
- **Description**: Sets the dimmer with ID `571` to a value of `10` (range depends on your device).

### Other Useful Endpoints

- **Send an Action**: https://www.postman.com/soft-techbv/ipbrestapi-s-public-workspace/request/6uctjo4/send-an-action
- **Client Command**: https://www.postman.com/soft-techbv/ipbrestapi-s-public-workspace/request/mgu7sxs/client-commando
- **Temperature Deviation**: https://www.postman.com/soft-techbv/ipbrestapi-s-public-workspace/request/51zmehz/temperature-deviation
- **Trigger Custom Item Action**: https://www.postman.com/soft-techbv/ipbrestapi-s-public-workspace/request/h59aed0/trigger-customitem-action
- **Get Version**: https://www.postman.com/soft-techbv/ipbrestapi-s-public-workspace/request/2ygfarm/get-version

These links point to the official Postman documentation for the IPBuilding REST API and provide detailed request/response examples.

## Usage in Home Assistant

The component exposes services that wrap these API calls. Refer to the component's `services.yaml` (if present) or the code in `api.py` for the exact service names and parameters.

## Development

For local development, see the top‑level `DEVELOPMENT.md` which contains instructions on setting up a virtual environment and running Home Assistant locally.
