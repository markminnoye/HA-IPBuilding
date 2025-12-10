"""Sensor platform for IPBuilding."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfPower
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from typing import Any

from .const import DOMAIN, TYPE_TIME, TYPE_REGIME, TYPE_RELAY, TYPE_DIMMER
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

    # Fetch Power sensors (from Relays and Dimmers)
    for type_id in [TYPE_RELAY, TYPE_DIMMER]:
        try:
            devices = await api.get_devices(type_id)
            for device in devices:
                # Only create power sensor if Watt field exists (and maybe > 0, but 0 is valid)
                if "Watt" in device:
                    entities.append(IPBuildingPowerSensor(api, device))
        except Exception as e:
            _LOGGER.error("Failed to fetch devices for power sensors (type %s): %s", type_id, e)

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
        
        # Hide state display by default
        self._attr_entity_registry_visible_default = False
        
        # Device Info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"sensor_{device.get('ID') or device.get('id')}")},
            "name": self._attr_name,
            "manufacturer": "IPBuilding",
            "model": sensor_type,
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
        """Fetch new state data for this sensor."""
        try:
            # Re-fetch specific type list to find this device
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


class IPBuildingPowerSensor(SensorEntity):
    """Representation of an IPBuilding Power Sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, api: IPBuildingAPI, device: dict) -> None:
        """Initialize the power sensor."""
        self._api = api
        self._device = device
        self._attr_unique_id = f"ipbuilding_power_{device.get('ID') or device.get('id')}"
        self._attr_name = f"{device.get('Description') or device.get('name')} Power"
        self._attr_native_value = self._calculate_power()
        
        # Hide state display by default
        self._attr_entity_registry_visible_default = False

        # Device Info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"output_{device.get('ID') or device.get('id')}")},
            "name": device.get("Description") or device.get("name") or f"Device {device.get('ID') or device.get('id')}",
            "manufacturer": "IPBuilding",
            "model": "Dimmer" if int(device.get("Type") or 0) == TYPE_DIMMER else "Relay",
        }
        if group := device.get("Group"):
            self._attr_device_info["suggested_area"] = group.get("Name")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Use Visible property from API, default to True
        return self._device.get("Visible", True)

    def _calculate_power(self) -> float:
        """Calculate the power usage based on state."""
        rated_watt = float(self._device.get("Watt") or 0)
        
        val = self._device.get("Status")
        if val is None:
            val = self._device.get("status")
        if val is None:
            val = self._device.get("Value")
        if val is None:
            val = self._device.get("value")

        if isinstance(val, bool):
            val = 1 if val else 0
        else:
            val = int(val or 0)

        type_id = int(self._device.get("Type") or self._device.get("type") or 0)
        
        if type_id == TYPE_DIMMER:
             # Dimmer value is 0-100
             return round(rated_watt * (val / 100.0), 1)
        
        # Binary ON/OFF
        return rated_watt if val > 0 else 0

    async def async_update(self) -> None:
        """Fetch new state data for this sensor."""
        try:
            # We need to know the type to re-fetch.
            type_id = int(self._device.get("Type") or self._device.get("type") or TYPE_RELAY)
            
            devices = await self._api.get_devices(type_id)
            for d in devices:
                dev_id = d.get('ID') or d.get('id')
                cur_id = self._device.get('ID') or self._device.get('id')
                if dev_id == cur_id:
                    self._device = d
                    break
            
            self._attr_native_value = self._calculate_power()
            
        except Exception as e:
            _LOGGER.error("Error updating power sensor %s: %s", self.entity_id, e)
