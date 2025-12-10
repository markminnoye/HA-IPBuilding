"""Button platform for IPBuilding."""
import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, TYPE_BUTTON
from .api import IPBuildingAPI

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the IPBuilding button platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    api: IPBuildingAPI = data["api"]
    coordinator_slow: DataUpdateCoordinator = data["coordinator_slow"]

    try:
        devices = await api.get_devices(TYPE_BUTTON)
    except Exception as e:
        _LOGGER.error("Failed to fetch buttons: %s", e)
        return

    entities = []
    for device in devices:
        entities.append(IPBuildingButton(coordinator_slow, api, device))

    async_add_entities(entities)


class IPBuildingButton(CoordinatorEntity, ButtonEntity):
    """Representation of an IPBuilding Button."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DataUpdateCoordinator, api: IPBuildingAPI, device: dict) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device.get("ID") or device.get("id")
        self._initial_device_data = device
        
        self._attr_unique_id = f"ipbuilding_button_{self._device_id}"
        self._attr_name = device.get("Description") or device.get("name") or f"Button {self._device_id}"
        
        # Disabled by default
        self._attr_entity_registry_enabled_default = False
        
        # Hide state display by default
        self._attr_entity_registry_visible_default = False
        
        # Device Info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"button_{self._device_id}")},
            "name": self._attr_name,
            "manufacturer": "IPBuilding",
            "model": "Button",
            "via_device": (DOMAIN, "hub_buttons"),
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
        # Use Visible property from API, default to True
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

    async def async_press(self) -> None:
        """Handle the button press."""
        # Assumption: Pressing a button sends a '1' or triggers an action.
        # We'll try sending '1'.
        await self._api.set_value(self._device_id, 1, "ON")

