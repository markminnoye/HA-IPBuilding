"""Light platform for IPBuilding."""
import logging
from typing import Any

from homeassistant.components.light import LightEntity, ColorMode, ATTR_BRIGHTNESS
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN, TYPE_DIMMER
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
    
    try:
        devices = await api.get_devices(TYPE_DIMMER)
    except Exception as e:
        _LOGGER.error("Failed to fetch dimmers: %s", e)
        return

    entities = []
    for device in devices:
        entities.append(IPBuildingLight(api, device))

    async_add_entities(entities, True)


class IPBuildingLight(LightEntity):
    """Representation of an IPBuilding Light (Dimmer)."""

    _attr_has_entity_name = True
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, api: IPBuildingAPI, device: dict) -> None:
        """Initialize the light."""
        self._api = api
        self._device = device
        self._attr_unique_id = f"ipbuilding_dimmer_{device.get('ID') or device.get('id')}"
        self._attr_name = device.get("Description") or device.get("name") or f"Dimmer {device.get('ID') or device.get('id')}"
        self._state = False
        self._brightness = 0

    async def async_update(self) -> None:
        """Fetch new state data for this light."""
        # In a real scenario, we'd want to fetch the status of this specific device
        # or refresh the whole list.
        # Assuming the 'device' dict from get_devices contains the current state 'value'.
        # We might need to re-fetch the device list or a specific status endpoint.
        # For now, let's re-fetch the list and find our device.
        try:
            devices = await self._api.get_devices(TYPE_DIMMER)
            for d in devices:
                dev_id = d.get('ID') or d.get('id')
                cur_id = self._device.get('ID') or self._device.get('id')
                if dev_id == cur_id:
                    self._device = d
                    break
            
            # Update state based on device data
            # Assumption: 'value' is 0-100 or 0-255.
            # If value > 0, it's on.
            val = int(self._device.get("Value") or self._device.get("value") or 0)
            self._state = val > 0
            # Map 0-100 to 0-255
            self._brightness = int(val * 255 / 100)
            
        except Exception as e:
            _LOGGER.error("Error updating light %s: %s", self.entity_id, e)

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        return self._state

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        return self._brightness

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        # Map 0-255 to 0-100
        val = int(brightness * 100 / 255)
        if val == 0 and brightness > 0:
            val = 1 # Ensure it turns on
            
        await self._api.set_value(self._device.get('ID') or self._device.get('id'), val, "DIM")
        # Optimistic update
        self._state = True
        self._brightness = brightness
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self._api.set_value(self._device.get('ID') or self._device.get('id'), 0, "OFF")
        # Optimistic update
        self._state = False
        self._brightness = 0
        self.async_write_ha_state()
