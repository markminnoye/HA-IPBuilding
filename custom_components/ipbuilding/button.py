"""Button platform for IPBuilding."""
import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, TYPE_BUTTON
from .api import IPBuildingAPI

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the IPBuilding button platform."""
    api: IPBuildingAPI = hass.data[DOMAIN][entry.entry_id]

    try:
        devices = await api.get_devices(TYPE_BUTTON)
    except Exception as e:
        _LOGGER.error("Failed to fetch buttons: %s", e)
        return

    entities = []
    for device in devices:
        entities.append(IPBuildingButton(api, device))

    async_add_entities(entities, True)


class IPBuildingButton(ButtonEntity):
    """Representation of an IPBuilding Button."""

    _attr_has_entity_name = True

    def __init__(self, api: IPBuildingAPI, device: dict) -> None:
        """Initialize the button."""
        self._api = api
        self._device = device
        self._attr_unique_id = f"ipbuilding_button_{device.get('ID') or device.get('id')}"
        self._attr_name = device.get("Description") or device.get("name") or f"Button {device.get('ID') or device.get('id')}"
        
        # Disabled by default
        self._attr_entity_registry_enabled_default = False
        
        # Hide state display by default
        self._attr_entity_registry_visible_default = False
        
        # Device Info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"button_{device.get('ID') or device.get('id')}")},
            "name": self._attr_name,
            "manufacturer": "IPBuilding",
            "model": "Button",
            "via_device": (DOMAIN, "hub_buttons"),
        }
        if group := device.get("Group"):
            self._attr_device_info["suggested_area"] = group.get("Name")
            
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

    async def async_press(self) -> None:
        """Handle the button press."""
        # Assumption: Pressing a button sends a '1' or triggers an action.
        # We'll try sending '1'.
        await self._api.set_value(self._device.get('ID') or self._device.get('id'), 1, "ON")
