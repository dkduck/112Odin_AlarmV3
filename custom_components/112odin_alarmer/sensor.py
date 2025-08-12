"""Sensor platform using aiohttp for fetch and feedparser for parse."""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import CONF_BEREDSKABSID, CONF_STATION, CONF_COUNT, DEFAULT_NAME
import asyncio
import logging
import feedparser

_LOGGER = logging.getLogger(__name__)

MAX_RETRIES = 3
TIMEOUT = 10

async def async_setup_entry(hass: HomeAssistantType, entry, async_add_entities):
    data = entry.data
    rss_url = data.get("rss_url")
    beredskabsID = data.get(CONF_BEREDSKABSID)
    station = entry.options.get(CONF_STATION, data.get(CONF_STATION, ""))
    count = int(entry.options.get(CONF_COUNT, data.get(CONF_COUNT, 5)))

    sensor = OdinFeedSensor(hass, entry.entry_id, rss_url, beredskabsID, station, count)
    async_add_entities([sensor], update_before_add=True)

class OdinFeedSensor(SensorEntity):
    def __init__(self, hass, entry_id: str, rss_url: str, beredskabsID: str, station: str, count: int):
        self.hass = hass
        self._entry_id = entry_id
        self._rss_url = rss_url.rstrip('/')
        self._beredskabsID = beredskabsID
        self._station = station
        self._count = max(1, min(20, int(count)))
        self._attr_name = DEFAULT_NAME
        self._state: Optional[int] = None
        self._entries: List[Dict[str, Any]] = []

    @property
    def unique_id(self) -> str:
        return f"112odin_{self._entry_id}"

    @property
    def native_value(self) -> Optional[int]:
        return self._state

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        return {
            "entries": self._entries,
            "last_update": datetime.utcnow().isoformat() + "Z",
            "rss_url": self._rss_url
        }

    async def _fetch(self, session, url: str) -> Optional[bytes]:
        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                import aiohttp
                timeout = aiohttp.ClientTimeout(total=TIMEOUT)
                async with session.get(url, timeout=timeout) as resp:
                    if resp.status != 200:
                        raise Exception(f"HTTP {resp.status}")
                    return await resp.read()
            except Exception as e:
                last_exc = e
                _LOGGER.warning("Fetch attempt %d/%d failed: %s", attempt, MAX_RETRIES, e)
                await asyncio.sleep(2 ** attempt)
        _LOGGER.error("All fetch attempts failed: %s", last_exc)
        return None

    async def async_update(self) -> None:
        params = []
        if self._beredskabsID:
            params.append(f"beredskabsID={self._beredskabsID}")
        if self._station:
            params.append(f"enhed={self._station}")
        if self._count:
            params.append(f"antal={self._count}")
        url = f"{self._rss_url}?" + "&".join(params)

        try:
            session = async_get_clientsession(self.hass)
        except Exception:
            raise ConfigEntryNotReady

        raw = await self._fetch(session, url)
        if raw is None:
            self._state = None
            self._entries = []
            return

        loop = asyncio.get_running_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, raw)
        if getattr(feed, 'bozo', False):
            _LOGGER.warning("Feed parsed with warnings: %s", getattr(feed, 'bozo_exception', 'unknown'))
        items = []
        for it in (feed.entries or [])[: self._count]:
            items.append({
                "title": it.get("title"),
                "description": it.get("description") or it.get('summary'),
                "summary": it.get('summary'),
                "published": it.get("published", it.get("updated", "")),
                "link": it.get("link")
            })
        self._entries = items
        self._state = len(items)
