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
    api: IPBuildingAPI = hass.data[DOMAIN][entry.entry_id]

    # Create a coordinator to fetch data
    # Note: For a real implementation, a shared coordinator in __init__ would be better
    # to avoid multiple polling loops. For now, we'll fetch per platform or just fetch once.
    # Let's just fetch devices once for setup, and then entities can poll or we can add a coordinator later.
    # Given the simplicity, we'll fetch devices now.
    
    # from .const import TYPE_RELAY (moved to top)
    
    entities = []
    
    # Fetch Dimmers
    try:
        devices = await api.get_devices(TYPE_DIMMER)
        for device in devices:
            entities.append(IPBuildingLight(api, device))
    except Exception as e:
        _LOGGER.error("Failed to fetch dimmers: %s", e)

    # Fetch Relays that are Lights (Kind 1)
    try:
        devices = await api.get_devices(TYPE_RELAY)
        for device in devices:
            if device.get("Kind") == 1:
                entities.append(IPBuildingLight(api, device))
    except Exception as e:
        _LOGGER.error("Failed to fetch relays for lights: %s", e)

    async_add_entities(entities, True)


class IPBuildingLight(LightEntity):
    """Representation of an IPBuilding Light (Dimmer)."""

    _attr_has_entity_name = True
    # _attr_color_mode and _attr_supported_color_modes are set in __init__

    def __init__(self, api: IPBuildingAPI, device: dict) -> None:
        """Initialize the light."""
        self._api = api
        self._device = device
        self._attr_unique_id = f"ipbuilding_dimmer_{device.get('ID') or device.get('id')}"
        self._attr_name = device.get("Description") or device.get("name") or f"Dimmer {device.get('ID') or device.get('id')}"
        self._state = False
        self._brightness = 0
        
        # Device Info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"output_{device.get('ID') or device.get('id')}")},
            "name": self._attr_name,
            "manufacturer": "IPBuilding",
            "model": "Dimmer" if self._device.get("Type") == TYPE_DIMMER else "Relay",
        }
        if group := device.get("Group"):
            self._attr_device_info["suggested_area"] = group.get("Name")

        # Determine color mode
        if self._device.get("Type") == TYPE_DIMMER:
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        else:
            self._attr_color_mode = ColorMode.ONOFF
            self._attr_supported_color_modes = {ColorMode.ONOFF}
            
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Use Visible property from API, default to True
        return self._device.get("Visible", True)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {
            "ID": self._device.get("ID") or self._device.get("id"),
            "Kind": self._device.get("Kind"),
        }
        for key in ["IpAddress", "Port", "Protocol", "Status", "Output"]:
            if val := self._device.get(key):
                attrs[key] = val
        return attrs

    async def async_update(self) -> None:
        """Fetch new state data for this light."""
        # In a real scenario, we'd want to fetch the status of this specific device
        # or refresh the whole list.
        # Assuming the 'device' dict from get_devices contains the current state 'value'.
        # We might need to re-fetch the device list or a specific status endpoint.
        # For now, let's re-fetch the list and find our device.
        try:
            # Determine type to re-fetch
            # If Kind is 1 and not a dimmer type (assuming dimmer type is 2), it's a relay.
            # But we don't store original type easily.
            # Let's try to infer or check both.
            # Or better, store the type in __init__.
            # For now, let's try fetching both lists and finding the device.
            # This is inefficient but safe.
            
            found = False
            # Try Dimmers first
            devices = await self._api.get_devices(TYPE_DIMMER)
            for d in devices:
                if (d.get('ID') or d.get('id')) == (self._device.get('ID') or self._device.get('id')):
                    self._device = d
                    found = True
                    break
            
            if not found:
                # Try Relays
                from .const import TYPE_RELAY
                devices = await self._api.get_devices(TYPE_RELAY)
                for d in devices:
                    if (d.get('ID') or d.get('id')) == (self._device.get('ID') or self._device.get('id')):
                        self._device = d
                        found = True
                        break

            # Update state based on device data
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
                int_val = 1 if val else 0
            else:
                int_val = int(val or 0)
                self._state = int_val > 0
            
            # Map to brightness if it's a dimmer (Type 2)
            # If it's a relay (Type 1), brightness is just 0 or 255
            if self._device.get("Type") == 2:
                self._brightness = int(int_val * 255 / 100)
            else:
                self._brightness = 255 if self._state else 0
            
        except Exception as e:
            _LOGGER.error("Error updating light %s: %s", self.entity_id, e)

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._state

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        if self._attr_color_mode == ColorMode.ONOFF:
            return None
        return self._brightness

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        # Check if it's a dimmer or relay
        if self._device.get("Type") == 2:
            # Dimmer
            brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
            # Map 0-255 to 0-100
            val = int(brightness * 100 / 255)
            if val == 0 and brightness > 0:
                val = 1 # Ensure it turns on
            await self._api.set_value(self._device.get('ID') or self._device.get('id'), val, "DIM")
            self._brightness = brightness
        else:
            # Relay (Light)
            await self._api.set_value(self._device.get('ID') or self._device.get('id'), 1, "ON")
            self._brightness = 255

        # Optimistic update
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self._api.set_value(self._device.get('ID') or self._device.get('id'), 0, "OFF")
        # Optimistic update
        self._state = False
        self._brightness = 0
        self.async_write_ha_state()
