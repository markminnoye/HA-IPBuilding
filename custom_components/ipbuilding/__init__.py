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
    from .coordinator import IPBuildingCoordinator
    from .const import (
        FAST_POLL_INTERVAL, SLOW_POLL_INTERVAL,
        FAST_POLL_TYPES, SLOW_POLL_TYPES
    )
    
    api = IPBuildingAPI(host, port, session)

    # Initialize Coordinators
    coordinator_fast = IPBuildingCoordinator(
        hass, api, FAST_POLL_TYPES, FAST_POLL_INTERVAL, "fast"
    )
    coordinator_slow = IPBuildingCoordinator(
        hass, api, SLOW_POLL_TYPES, SLOW_POLL_INTERVAL, "slow"
    )

    # Fetch initial data so we have something before entities start
    await coordinator_fast.async_config_entry_first_refresh()
    await coordinator_slow.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator_fast": coordinator_fast,
        "coordinator_slow": coordinator_slow,
    }

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
    
    # Fetch all devices once to determine which types are present
    try:
        # Re-use fast coordinator data if possible, or fetch anew. 
        # Since we just refreshed, we might combine or just fetch "all" once safely.
        # But api.get_devices() without args fetches ALL.
        all_devices = await api.get_devices()
    except Exception as e:
        _LOGGER.warning("Failed to fetch devices for hub creation: %s", e)
        all_devices = []

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
        # Compatibility: If we previously created "hub_sensors" and now use specific ones,
        # we might want to migrate or just assume new setup. 
        # For Time/Regime we moved to "hub_system".

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
