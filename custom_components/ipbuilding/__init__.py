"""The IPBuilding integration."""
import asyncio
import logging
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

# NOTE: IPBuildingAPI is imported lazily inside async_setup_entry to avoid blocking imports during component loading.

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.LIGHT, Platform.SWITCH, Platform.BUTTON, Platform.SENSOR, Platform.SCENE]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up IPBuilding from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    session = async_get_clientsession(hass)
    
    # Lazy import to avoid blocking the event loop during component loading
    from .api import IPBuildingAPI
    # Import DataUpdateCoordinator
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
    from datetime import timedelta
    from .const import TYPE_RELAY, TYPE_DIMMER, TYPE_DMX, TYPE_LED

    api = IPBuildingAPI(host, port, session)

    # Define the polling function
    async def async_update_data():
        """Fetch data from API - Only specific types."""
        try:
            # Poll only types 1, 2, 3 (DMX), 60 (LED)
            # DMX is 3, LED is 60 in const.py
            partial_devices = await api.get_devices([TYPE_RELAY, TYPE_DIMMER, TYPE_DMX, TYPE_LED])
            
            # Convert to dict
            partial_data = {d.get("ID") or d.get("id"): d for d in partial_devices}
            
            # Merge with existing data
            # We access the coordinator's current data via 'coordinator.data' but we are inside the method passed TO it.
            # We can't access 'coordinator' instance here easily before creation if we define function inline?
            # Actually, we can use a closure or 'nonlocal' if defined inside setup_entry.
            # But 'coordinator' variable is created AFTER this function definition usually.
            # Solution: We can wrap this in a class or use the fact that we return the NEW data.
            # BUT we need the OLD data to merge.
            # 'coordinator.data' is available on the coordinator object.
            # We'll define the function, create coordinator, then attach function? No.
            # Better: Define a class or use a mutable dict reference.
            
            # Actually, standard way:
            current_data = coordinator.data if coordinator.data else {}
            # Create a NEW dict to trigger updates? Or update in place?
            # Creating a shallow copy to be safe and ensure 'data' reference changes if HA checks identity.
            new_data = current_data.copy()
            new_data.update(partial_data)
            return new_data

        except Exception as e:
            raise UpdateFailed(f"Error communicating with API: {e}")

    # Initialize Coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="ipbuilding_fast",
        update_method=async_update_data,
        update_interval=timedelta(seconds=20),
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    # Fetch initial data (ALL devices) for the first run
    try:
        all_devices = await api.get_devices()
        initial_data = {d.get("ID") or d.get("id"): d for d in all_devices}
        # Seed the coordinator with initial data
        coordinator.async_set_updated_data(initial_data)
    except Exception as e:
        _LOGGER.error("Failed to fetch initial devices: %s", e)
        return False
    
    # Create Hub Devices for Grouping
    from homeassistant.helpers import device_registry as dr
    from .const import (
        TYPE_RELAY, TYPE_DIMMER, TYPE_DMX, TYPE_ENERGY_COUNTER, TYPE_ENERGY_METER,
        TYPE_BUTTON, TYPE_TEMPERATURE, TYPE_DETECTOR, TYPE_ANALOG_SENSOR,
        TYPE_KMI, TYPE_WEATHER_STATION, TYPE_TIME, TYPE_LED,
        TYPE_ACCESS_READER, TYPE_ACCESS_KEY, TYPE_SPHERE, TYPE_TEMP_SPHERE,
        TYPE_PROG, TYPE_ACCESS_CONTROL, TYPE_SCRIPT, TYPE_REGIME
    )
    
    dev_reg = dr.async_get(hass)
    
    # We already have 'all_devices' from the initial fetch above.
    
    # Track present types
    present_types = set()
    for d in all_devices:
        if dtype := d.get("Type") or d.get("type"):
            present_types.add(int(dtype))

    # Define Hubs and their associated types
    # (hub_id, hub_name, list_of_types)
    hub_definitions = [
        ("hub_dimmers", "IPBuilding Dimmers", [TYPE_DIMMER]),
        ("hub_relays", "IPBuilding Relays", [TYPE_RELAY]),
        ("hub_dmx", "IPBuilding DMX", [TYPE_DMX]),
        ("hub_led", "IPBuilding LED", [TYPE_LED]),
        ("hub_buttons", "IPBuilding Buttons", [TYPE_BUTTON]),
        ("hub_scenes", "IPBuilding Scenes", [TYPE_SPHERE, TYPE_TEMP_SPHERE]),
        ("hub_detectors", "IPBuilding Detectors", [TYPE_DETECTOR]),
        ("hub_temperature", "IPBuilding Temperature", [TYPE_TEMPERATURE]),
        ("hub_weather", "IPBuilding Weather", [TYPE_KMI, TYPE_WEATHER_STATION]),
        ("hub_energy", "IPBuilding Energy", [TYPE_ENERGY_COUNTER, TYPE_ENERGY_METER]),
        ("hub_access", "IPBuilding Access", [TYPE_ACCESS_READER, TYPE_ACCESS_KEY, TYPE_ACCESS_CONTROL]),
        ("hub_analog", "IPBuilding Analog", [TYPE_ANALOG_SENSOR]),
        ("hub_system", "IPBuilding System", [TYPE_TIME, TYPE_REGIME]),
        ("hub_logic", "IPBuilding Logic", [TYPE_PROG, TYPE_SCRIPT]),
    ]
    
    for hub_id, hub_name, types in hub_definitions:
        # Check if any of the types for this hub are present
        if any(t in present_types for t in types):
            dev_reg.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, hub_id)},
                name=hub_name,
                manufacturer="IPBuilding",
                model="System Hub",
            )

    # Forward entry setups
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
