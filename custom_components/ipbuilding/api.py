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

    async def get_devices(self, types: list[int] | int = None):
        """Get devices, optionally filtered by type(s)."""
        url = f"{self._base_url}/comp/items"
        params = {}
        if types is not None:
            if isinstance(types, list):
                # Join types with comma if API supports it, otherwise this might need multiple calls or loop
                # Assuming API supports "types=1,2" or similar. If not, client side filtering on full list is fallback.
                # Based on user request, let's try comma separated.
                params["types"] = ",".join(map(str, types))
            else:
                params["types"] = types

        try:
            async with async_timeout.timeout(10):
                async with self._session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Ensure we have a list
                    if not isinstance(data, list):
                        if isinstance(data, dict) and "items" in data:
                            data = data["items"]
                        else:
                            data = [data] if data else []

                    # Client-side filtering to be safe
                    if types is not None:
                        target_types = types if isinstance(types, list) else [types]
                        filtered = []
                        for d in data:
                            dtype = d.get("Type") or d.get("type")
                            if dtype is not None and int(dtype) in target_types:
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

