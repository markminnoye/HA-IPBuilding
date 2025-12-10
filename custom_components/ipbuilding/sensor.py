"""Sensor platform for IPBuilding."""
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfPower
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
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
    data = hass.data[DOMAIN][entry.entry_id]
    api: IPBuildingAPI = data["api"]
    coordinator: DataUpdateCoordinator = data["coordinator"]

    entities = []
    
    if coordinator.data:
        # Time Sensors
        for dev_id, device in coordinator.data.items():
            if int(device.get("Type") or 0) == TYPE_TIME:
                 entities.append(IPBuildingSensor(coordinator, api, device, "Time", "hub_system"))
        
        # Regime Sensors
        for dev_id, device in coordinator.data.items():
            if int(device.get("Type") or 0) == TYPE_REGIME:
                 entities.append(IPBuildingSensor(coordinator, api, device, "Regime", "hub_system"))
        
        # Power Sensors (Relays and Dimmers)
        for dev_id, device in coordinator.data.items():
            dtype = int(device.get("Type") or 0)
            if dtype in [TYPE_RELAY, TYPE_DIMMER]:
                if "Watt" in device:
                    entities.append(IPBuildingPowerSensor(coordinator, api, device))

    async_add_entities(entities)


class IPBuildingSensor(CoordinatorEntity, SensorEntity):
    """Representation of an IPBuilding Sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DataUpdateCoordinator, api: IPBuildingAPI, device: dict, sensor_type: str, hub: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._api = api
        self._sensor_type = sensor_type
        self._device_id = device.get("ID") or device.get("id")
        self._initial_device_data = device
        
        self._attr_unique_id = f"ipbuilding_sensor_{self._device_id}"
        self._attr_name = device.get("Description") or device.get("name") or f"{sensor_type} {self._device_id}"
        
        self._attr_entity_registry_visible_default = False
        
        # Device Info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"sensor_{self._device_id}")},
            "name": self._attr_name,
            "manufacturer": "IPBuilding",
            "model": sensor_type,
            "via_device": (DOMAIN, hub),
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
        return self.coordinator.last_update_success and self._device_data.get("Visible", True)

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        d = self._device_data
        return d.get("Value") or d.get("value")

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


class IPBuildingPowerSensor(CoordinatorEntity, SensorEntity):
    """Representation of an IPBuilding Power Sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: DataUpdateCoordinator, api: IPBuildingAPI, device: dict) -> None:
        """Initialize the power sensor."""
        super().__init__(coordinator)
        self._api = api
        self._device_id = device.get("ID") or device.get("id")
        self._initial_device_data = device
        
        self._attr_unique_id = f"ipbuilding_power_{self._device_id}"
        self._attr_name = f"{device.get('Description') or device.get('name')} Power"
        
        # Hide state display by default
        self._attr_entity_registry_visible_default = False

        # Device Info
        hub = "hub_dimmers" if int(device.get("Type") or 0) == TYPE_DIMMER else "hub_relays"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"output_{self._device_id}")},
            "name": device.get("Description") or device.get("name") or f"Device {self._device_id}",
            "manufacturer": "IPBuilding",
            "model": "Dimmer" if int(device.get("Type") or 0) == TYPE_DIMMER else "Relay",
            "via_device": (DOMAIN, hub),
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
        return self.coordinator.last_update_success and self._device_data.get("Visible", True)

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        return self._calculate_power()

    def _calculate_power(self) -> float:
        """Calculate the power usage based on state."""
        d = self._device_data
        rated_watt = float(d.get("Watt") or 0)
        
        val = d.get("Status")
        if val is None:
            val = d.get("status")
        if val is None:
            val = d.get("Value")
        if val is None:
            val = d.get("value")

        if isinstance(val, bool):
            val = 1 if val else 0
        else:
            val = int(val or 0)

        type_id = int(d.get("Type") or d.get("type") or 0)
        
        if type_id == TYPE_DIMMER:
             # Dimmer value is 0-100
             return round(rated_watt * (val / 100.0), 1)
        
        # Binary ON/OFF
        return rated_watt if val > 0 else 0
