"""Scene platform for IPBuilding."""
import logging
from typing import Any

from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, TYPE_SPHERE, TYPE_TEMP_SPHERE
from .api import IPBuildingAPI

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the IPBuilding scene platform."""
    api: IPBuildingAPI = hass.data[DOMAIN][entry.entry_id]

    entities = []
    
    # Fetch Sphere scenes
    try:
        sphere_devices = await api.get_devices(TYPE_SPHERE)
        for device in sphere_devices:
            entities.append(IPBuildingScene(api, device))
    except Exception as e:
        _LOGGER.error("Failed to fetch spheres: %s", e)

    # Fetch TempSphere scenes
    try:
        temp_sphere_devices = await api.get_devices(TYPE_TEMP_SPHERE)
        for device in temp_sphere_devices:
            entities.append(IPBuildingScene(api, device))
    except Exception as e:
        _LOGGER.error("Failed to fetch temp spheres: %s", e)

    async_add_entities(entities, True)


class IPBuildingScene(Scene):
    """Representation of an IPBuilding Scene (Sphere)."""

    _attr_has_entity_name = True

    def __init__(self, api: IPBuildingAPI, device: dict) -> None:
        """Initialize the scene."""
        self._api = api
        self._device = device
        self._attr_unique_id = f"ipbuilding_scene_{device.get('ID') or device.get('id')}"
        self._attr_name = device.get("Description") or device.get("name") or f"Scene {device.get('ID') or device.get('id')}"
        
        # Device Info
        if group := device.get("Group"):
            self._attr_device_info = {
                "identifiers": {(DOMAIN, f"group_{group.get('ID')}")},
                "name": group.get("Name"),
                "manufacturer": "IPBuilding",
                "model": "Group",
            }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Use Visible property from API, default to True
        return self._device.get("Visible", True)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "IpAddress": self._device.get("IpAddress"),
            "Port": self._device.get("Port"),
            "Protocol": self._device.get("Protocol"),
            "ID": self._device.get("ID") or self._device.get("id"),
            "Status": self._device.get("Status"),
            "Output": self._device.get("Output"),
            "Kind": self._device.get("Kind"),
        }

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        # Assuming activating a scene is done by setting its value to 1 or calling an action
        # Similar to buttons, we'll try setting value to 1 with actionType ON
        await self._api.set_value(self._device.get('ID') or self._device.get('id'), 1, "ON")
