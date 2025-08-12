"""112Odin Alarmer integration - HACS-ready v1.4."""

from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup(hass: HomeAssistant, config: dict):
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass, entry):
    await hass.config_entries.async_forward_entry_setup(entry, "sensor")
    return True

async def async_unload_entry(hass, entry):
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    return True
