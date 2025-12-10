"""Switch platform for IPBuilding."""
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, TYPE_RELAY
from .api import IPBuildingAPI

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the IPBuilding switch platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    api: IPBuildingAPI = data["api"]
    coordinator_fast: DataUpdateCoordinator = data["coordinator_fast"]

    try:
        devices = await api.get_devices(TYPE_RELAY)
    except Exception as e:
        _LOGGER.error("Failed to fetch relays: %s", e)
        return

    entities = []
    for device in devices:
        # Skip Kind 1 (Light) as they should be handled by the light platform
        if device.get("Kind") == 1:
            continue
        entities.append(IPBuildingSwitch(coordinator_fast, api, device))

    async_add_entities(entities)


class IPBuildingSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of an IPBuilding Switch (Relay)."""
        
    _attr_has_entity_name = True

    def __init__(self, coordinator: DataUpdateCoordinator, api: IPBuildingAPI, device: dict) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device.get("ID") or device.get("id")
        self._initial_device_data = device
        
        self._attr_unique_id = f"ipbuilding_relay_{self._device_id}"
        self._attr_name = device.get("Description") or device.get("name") or f"Relay {self._device_id}"
        
        # Default to disabled in registry, but enabled in HA logic
        #self._attr_entity_registry_enabled_default = False
        
        # Handle Kind
        kind = device.get("Kind")
        if kind == 2: # Socket
            self._attr_device_class = "outlet"
            self._attr_icon = "mdi:power-socket-eu"
        elif kind == 4: # Lock
            self._attr_icon = "mdi:lock"
        elif kind == 5: # Fan
            self._attr_icon = "mdi:fan"
        elif kind == 6: # Valve
            self._attr_icon = "mdi:valve"
        elif kind == 52: # Detector (Smoke?)
             pass

        # Check for smoke detector in description or kind if applicable
        if "smoke" in self._attr_name.lower() or "rook" in self._attr_name.lower():
             self._attr_icon = "mdi:smoke-detector-variant"
        
        # Device Info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"output_{self._device_id}")},
            "name": self._attr_name,
            "manufacturer": "IPBuilding",
            "model": "Relay",
            "model": "Relay",
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

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        d = self._device_data
        val = d.get("Status") or d.get("status") or d.get("Value") or d.get("value")
        if isinstance(val, bool):
            return val
        return int(val or 0) > 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._api.set_value(self._device_id, 1, "ON") # Assuming 1 is ON
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._api.set_value(self._device_id, 0, "OFF") # Assuming 0 is OFF
        await self.coordinator.async_request_refresh()
