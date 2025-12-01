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
