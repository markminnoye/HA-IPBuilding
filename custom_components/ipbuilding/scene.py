"""Scene platform for IPBuilding."""
import logging
from typing import Any

from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, TYPE_SPHERE, TYPE_TEMP_SPHERE
from .api import IPBuildingAPI

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the IPBuilding scene platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    api: IPBuildingAPI = data["api"]
    coordinator_slow: DataUpdateCoordinator = data["coordinator_slow"]
    
    entities = []
    
    # Fetch Sphere scenes (Slow)
    try:
        sphere_devices = await api.get_devices(TYPE_SPHERE)
        for device in sphere_devices:
            entities.append(IPBuildingScene(coordinator_slow, api, device))
    except Exception as e:
        _LOGGER.error("Failed to fetch spheres: %s", e)

    # Fetch TempSphere scenes (Slow)
    try:
        temp_sphere_devices = await api.get_devices(TYPE_TEMP_SPHERE)
        for device in temp_sphere_devices:
            entities.append(IPBuildingScene(coordinator_slow, api, device))
    except Exception as e:
        _LOGGER.error("Failed to fetch temp spheres: %s", e)

    async_add_entities(entities, True)


class IPBuildingScene(CoordinatorEntity, Scene):
    """Representation of an IPBuilding Scene (Sphere)."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DataUpdateCoordinator, api: IPBuildingAPI, device: dict) -> None:
        """Initialize the scene."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device.get("ID") or device.get("id")
        self._initial_device_data = device
        
        self._attr_unique_id = f"ipbuilding_scene_{self._device_id}"
        self._attr_name = device.get("Description") or device.get("name") or f"Scene {self._device_id}"
        
        # Device Info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"scene_{self._device_id}")},
            "name": self._attr_name,
            "manufacturer": "IPBuilding",
            "model": "Scene",
            "via_device": (DOMAIN, "hub_scenes"),
        }
        if group := device.get("Group"):
            self._attr_device_info["suggested_area"] = group.get("Name")

    @property
    def _device_data(self) -> dict:
        """Get the latest device data from coordinator."""
        return self.coordinator.data.get(self._device_id, self._initial_device_data)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self._device_data.get("Visible", True)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        d = self._device_data
        return {
            "IpAddress": d.get("IpAddress"),
            "Port": d.get("Port"),
            "Protocol": d.get("Protocol"),
            "ID": self._device_id,
            "Status": d.get("Status"),
            "Output": d.get("Output"),
            "Kind": d.get("Kind"),
        }

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        await self._api.set_value(self._device_id, 1, "ON")
