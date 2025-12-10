"""Switch platform for IPBuilding."""
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, TYPE_RELAY
from .api import IPBuildingAPI

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the IPBuilding switch platform."""
    api: IPBuildingAPI = hass.data[DOMAIN][entry.entry_id]

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
        entities.append(IPBuildingSwitch(api, device))

    async_add_entities(entities, True)


class IPBuildingSwitch(SwitchEntity):
    """Representation of an IPBuilding Switch (Relay)."""
        
    _attr_has_entity_name = True

    def __init__(self, api: IPBuildingAPI, device: dict) -> None:
        """Initialize the switch."""
        self._api = api
        self._device = device
        self._attr_unique_id = f"ipbuilding_relay_{device.get('ID') or device.get('id')}"
        self._attr_name = device.get("Description") or device.get("name") or f"Relay {device.get('ID') or device.get('id')}"
        self._state = False
        
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
        elif kind == 52: # Detector (Smoke?) - Check if this is correct mapping or if it needs to be specific
             # User requested smoke detector icon. Assuming Kind 52 might be detector or specific device.
             # If Kind is not enough, we might need to check Description or Type.
             # But user said "relais die een licht bedienen... rookmelder = smoke detector".
             # If smoke detector is a relay (Type 1), we check here.
             pass

        # Check for smoke detector in description or kind if applicable
        if "smoke" in self._attr_name.lower() or "rook" in self._attr_name.lower():
             self._attr_icon = "mdi:smoke-detector-variant"
        
        # Device Info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"output_{device.get('ID') or device.get('id')}")},
            "name": self._attr_name,
            "manufacturer": "IPBuilding",
            "model": "Relay",
            "via_device": (DOMAIN, "hub_relays"),
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

    async def async_update(self) -> None:
        """Fetch new state data for this switch."""
        try:
            devices = await self._api.get_devices(TYPE_RELAY)
            for d in devices:
                dev_id = d.get('ID') or d.get('id')
                cur_id = self._device.get('ID') or self._device.get('id')
                if dev_id == cur_id:
                    self._device = d
                    break
            
            # Assumption: 'value' is 0 or 1 (or >0)
            # Check Status (boolean) or Value (int)
            val = self._device.get("Status")
            if val is None:
                val = self._device.get("status")
            if val is None:
                val = self._device.get("Value")
            if val is None:
                val = self._device.get("value")
            
            # Convert to int/bool
            if isinstance(val, bool):
                self._state = val
            else:
                self._state = int(val or 0) > 0
            
        except Exception as e:
            _LOGGER.error("Error updating switch %s: %s", self.entity_id, e)

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._api.set_value(self._device.get('ID') or self._device.get('id'), 1, "ON") # Assuming 1 is ON
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._api.set_value(self._device.get('ID') or self._device.get('id'), 0, "OFF") # Assuming 0 is OFF
        self._state = False
        self.async_write_ha_state()
