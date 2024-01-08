"""Custom integration to integrate philips_humidifier with Home Assistant.

For more details about this integration, please refer to
https://github.com/ludeeus/philips-humidifier
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform, CONF_ENTITY_ID, CONF_SOURCE, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, LOGGER, DATA_KEY_FAN, DATA_KEY_SENSOR

PLATFORM = Platform.HUMIDIFIER


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    LOGGER.debug(f'async_setup_entry called for {entry.data[CONF_NAME]}')

    registry = er.async_get(hass)
    source_entity_id = er.async_validate_entity_id(
        registry, entry.data[CONF_SOURCE]
    )
    humidity_entity_id = er.async_validate_entity_id(
        registry, entry.data[CONF_ENTITY_ID]
    )

    states = [
        state.state
        for entity_id in [source_entity_id, humidity_entity_id]
        if (state := hass.states.get(entity_id)) is not None
    ]
    if states and any(state == STATE_UNAVAILABLE for state in states):
        raise ConfigEntryNotReady("Source entities unavailable")

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_KEY_FAN: entry.data[CONF_SOURCE],
        DATA_KEY_SENSOR: entry.data[CONF_ENTITY_ID]
    }

    await hass.config_entries.async_forward_entry_setups(entry, (PLATFORM,))
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, (PLATFORM,)):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
