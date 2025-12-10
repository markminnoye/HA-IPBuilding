"""DataUpdateCoordinator for IPBuilding."""
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IPBuildingAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class IPBuildingCoordinator(DataUpdateCoordinator):
    """Class to manage fetching IPBuilding data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: IPBuildingAPI,
        types: list[int],
        update_interval: int,
        name: str,
    ) -> None:
        """Initialize the coordinator."""
        self.api = api
        self.types = types
        
        if update_interval is not None:
            interval = timedelta(seconds=update_interval)
        else:
            interval = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{name}",
            update_interval=interval,
        )

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        """Fetch data from API."""
        try:
            # Fetch devices for the configured types
            # We assume api.get_devices accepts a list of types
            devices = await self.api.get_devices(self.types)
            
            # Map by ID for easy lookup O(1)
            # Both 'ID' and 'id' might be present
            data_map = {}
            for d in devices:
                dev_id = d.get("ID") or d.get("id")
                if dev_id:
                    data_map[dev_id] = d
                    
            return data_map
            
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
