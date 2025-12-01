"""API Client for IPBuilding."""
import logging
import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)

class IPBuildingAPI:
    """IPBuilding API Client."""

    def __init__(self, host: str, port: int, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._host = host
        self._port = port
        self._session = session
        self._base_url = f"http://{host}:{port}/api/v1"

    async def get_devices(self, type_id: int = None):
        """Get devices, optionally filtered by type."""
        url = f"{self._base_url}/comp/items"
        params = {}
        if type_id is not None:
            params["types"] = type_id

        try:
            async with async_timeout.timeout(10):
                async with self._session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Ensure we have a list
                    if not isinstance(data, list):
                        # If the API returns a wrapper, try to extract the list. 
                        # But based on jq output it seems to be a list.
                        if isinstance(data, dict) and "items" in data:
                            data = data["items"]
                        else:
                            # If it's a single object or unknown, wrap it
                            data = [data] if data else []

                    # Client-side filtering to be safe
                    if type_id is not None:
                        filtered = []
                        for d in data:
                            # Check 'Type' or 'type'
                            dtype = d.get("Type") or d.get("type")
                            if dtype is not None and int(dtype) == type_id:
                                filtered.append(d)
                        return filtered
                    
                    return data
        except Exception as e:
            _LOGGER.error("Error fetching devices: %s", e)
            raise

    async def set_value(self, device_id: int, value: int, action_type: str = None):
        """Set a value for a device using the proper action endpoint.
        For dimmers we use actionType=DIM, for relays ON/OFF.
        """
        # Determine action type based on value if not provided
        if action_type is None:
            if value == 0:
                action_type = "OFF"
            else:
                action_type = "DIM"

        # Build URL according to the documented endpoint
        url = f"{self._base_url}/action/action"
        params = {
            "id": device_id,
            "actionType": action_type,
            "value": value,
        }
        try:
            async with async_timeout.timeout(10):
                async with self._session.get(url, params=params) as response:
                    response.raise_for_status()
                    return await response.json(content_type=None)
        except Exception as e:
            _LOGGER.error("Error setting value for device %s: %s", device_id, e)
            raise

