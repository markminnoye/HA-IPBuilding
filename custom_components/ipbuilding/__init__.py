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



    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
