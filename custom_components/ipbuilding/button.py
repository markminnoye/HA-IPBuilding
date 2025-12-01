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

    async def async_press(self) -> None:
        """Handle the button press."""
        # Assumption: Pressing a button sends a '1' or triggers an action.
        # We'll try sending '1'.
        await self._api.set_value(self._device.get('ID') or self._device.get('id'), 1, "ON")
