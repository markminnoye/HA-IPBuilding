"""Light platform for IPBuilding."""
import logging
from typing import Any

from homeassistant.components.light import LightEntity, ColorMode, ATTR_BRIGHTNESS
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, TYPE_DIMMER, TYPE_RELAY
from .api import IPBuildingAPI

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the IPBuilding light platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    api: IPBuildingAPI = data["api"]
    coordinator_fast: DataUpdateCoordinator = data["coordinator_fast"]
    
    entities = []
    
    # Fetch Dimmers (Fast)
    try:
        devices = await api.get_devices(TYPE_DIMMER)
        for device in devices:
            entities.append(IPBuildingLight(coordinator_fast, api, device))
    except Exception as e:
        _LOGGER.error("Failed to fetch dimmers: %s", e)

    # Fetch Relays that are Lights (Fast)
    try:
        devices = await api.get_devices(TYPE_RELAY)
        for device in devices:
            if device.get("Kind") == 1:
                entities.append(IPBuildingLight(coordinator_fast, api, device))
    except Exception as e:
        _LOGGER.error("Failed to fetch relays for lights: %s", e)

    async_add_entities(entities, True)


class IPBuildingLight(CoordinatorEntity, LightEntity):
    """Representation of an IPBuilding Light (Dimmer)."""

    _attr_has_entity_name = True
    # _attr_color_mode and _attr_supported_color_modes are set in __init__

    def __init__(self, coordinator: DataUpdateCoordinator, api: IPBuildingAPI, device: dict) -> None:
        """Initialize the light."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device.get("ID") or device.get("id")
        # Store initial device data, but use proper key for lookups
        self._initial_device_data = device
        
        self._attr_unique_id = f"ipbuilding_dimmer_{self._device_id}"
        self._attr_name = device.get("Description") or device.get("name") or f"Dimmer {self._device_id}"
        
        # Determine color mode
        if device.get("Type") == TYPE_DIMMER:
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        else:
            self._attr_color_mode = ColorMode.ONOFF
            self._attr_supported_color_modes = {ColorMode.ONOFF}
            
        # Device Info setup...
        hub = "hub_dimmers" if device.get("Type") == TYPE_DIMMER else "hub_relays"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"output_{self._device_id}")},
            "name": self._attr_name,
            "manufacturer": "IPBuilding",
            "model": "Dimmer" if device.get("Type") == TYPE_DIMMER else "Relay",
            "via_device": (DOMAIN, hub),
        }
        if group := device.get("Group"):
            self._attr_device_info["suggested_area"] = group.get("Name")

    @property
    def _device_data(self) -> dict:
        """Get the latest device data from coordinator."""
        # Fallback to initial data if not found in coordinator (shouldn't happen if initialized correctly)
        return self.coordinator.data.get(self._device_id, self._initial_device_data)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self._device_data.get("Visible", True)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        d = self._device_data
        attrs = {
            "ID": self._device_id,
            "Kind": d.get("Kind"),
        }
        for key in ["IpAddress", "Port", "Protocol", "Status", "Output"]:
            if val := d.get(key):
                attrs[key] = val
        return attrs

    # No async_update needed, CoordinatorEntity handles it.
    # We just implement properties that read from _device_data
    
    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        d = self._device_data
        val = d.get("Status") or d.get("status") or d.get("Value") or d.get("value")
        if isinstance(val, bool):
            return val
        return int(val or 0) > 0

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        if self._attr_color_mode == ColorMode.ONOFF:
            return None
            
        d = self._device_data
        val = d.get("Status") or d.get("status") or d.get("Value") or d.get("value")
        
        # If boolean, map to 0/255
        if isinstance(val, bool):
             return 255 if val else 0
             
        int_val = int(val or 0)
        # Dimmer value is typically 0-100 in IPBuilding
        return int(int_val * 255 / 100)

    # async_turn_on / off method logic remains mostly same but uses _device_data
    # and calls await self.coordinator.async_request_refresh() after optimistic update
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        d = self._device_data
        if d.get("Type") == 2: # Dimmer
            brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
            val = int(brightness * 100 / 255)
            if val == 0 and brightness > 0:
                val = 1
            await self._api.set_value(self._device_id, val, "DIM")
        else:
            await self._api.set_value(self._device_id, 1, "ON")

        # Request refresh to update state
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self._api.set_value(self._device_id, 0, "OFF")
        await self.coordinator.async_request_refresh()


