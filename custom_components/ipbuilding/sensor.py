"""Sensor platform for IPBuilding."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, TYPE_TIME, TYPE_REGIME
from .api import IPBuildingAPI

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the IPBuilding sensor platform."""
    api: IPBuildingAPI = hass.data[DOMAIN][entry.entry_id]

    entities = []
    
    # Fetch Time sensors
    try:
        time_devices = await api.get_devices(TYPE_TIME)
        for device in time_devices:
            entities.append(IPBuildingSensor(api, device, "Time"))
    except Exception as e:
        _LOGGER.error("Failed to fetch time sensors: %s", e)

    # Fetch Regime sensors
    try:
        regime_devices = await api.get_devices(TYPE_REGIME)
        for device in regime_devices:
             entities.append(IPBuildingSensor(api, device, "Regime"))
    except Exception as e:
        _LOGGER.error("Failed to fetch regime sensors: %s", e)

    async_add_entities(entities, True)


class IPBuildingSensor(SensorEntity):
    """Representation of an IPBuilding Sensor."""

    _attr_has_entity_name = True

    def __init__(self, api: IPBuildingAPI, device: dict, sensor_type: str) -> None:
        """Initialize the sensor."""
        self._api = api
        self._device = device
        self._sensor_type = sensor_type
        self._attr_unique_id = f"ipbuilding_sensor_{device.get('ID') or device.get('id')}"
        self._attr_name = device.get("Description") or device.get("name") or f"{sensor_type} {device.get('ID') or device.get('id')}"
        self._attr_native_value = device.get("Value") or device.get("value")

    async def async_update(self) -> None:
        """Fetch new state data for this sensor."""
        try:
            # Re-fetch specific type list to find this device
            # This is inefficient but simple for now.
            type_id = TYPE_TIME if self._sensor_type == "Time" else TYPE_REGIME
            devices = await self._api.get_devices(type_id)
            for d in devices:
                dev_id = d.get('ID') or d.get('id')
                cur_id = self._device.get('ID') or self._device.get('id')
                if dev_id == cur_id:
                    self._device = d
                    break
            
            self._attr_native_value = self._device.get("Value") or self._device.get("value")
            
        except Exception as e:
            _LOGGER.error("Error updating sensor %s: %s", self.entity_id, e)
