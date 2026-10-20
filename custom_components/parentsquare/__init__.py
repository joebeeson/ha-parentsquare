from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import ParentSquareCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = ParentSquareCoordinator(hass, entry)
    try:
        await coordinator.async_initialize()
    except Exception:
        await coordinator.async_shutdown()
        raise
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator: ParentSquareCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    await coordinator.async_shutdown()
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
    return unloaded
