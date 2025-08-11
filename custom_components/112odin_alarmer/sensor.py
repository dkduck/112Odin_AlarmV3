"""Sensor platform for 112Odin Alarmer using aiohttp for fetching."""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import CONF_BEREDSKABSID, CONF_STATION, CONF_COUNT, DEFAULT_NAME
import feedparser
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

MAX_RETRIES = 3
TIMEOUT = 10  # seconds

async def async_setup_entry(hass: HomeAssistantType, entry, async_add_entities):
    data = entry.data
    rss_url = data.get("rss_url")
    beredskabsID = data.get(CONF_BEREDSKABSID)
    station = entry.options.get(CONF_STATION, data.get(CONF_STATION, ""))
    count = int(entry.options.get(CONF_COUNT, data.get(CONF_COUNT, 5)))

    sensor = OdinFeedSensor(hass=entry.hass if hasattr(entry, 'hass') else None, entry_id=entry.entry_id, rss_url=rss_url, beredskabsID=beredskabsID, station=station, count=count)
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
        self.entity_id = "sensor.112odin"

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

    async def _fetch_raw(self, session, url: str) -> Optional[bytes]:
        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                timeout = aiohttp.ClientTimeout(total=TIMEOUT)
                async with session.get(url, timeout=timeout) as resp:
                    if resp.status != 200:
                        raise Exception(f"HTTP {resp.status}")
                    data = await resp.read()
                    return data
            except Exception as e:
                last_exc = e
                _LOGGER.warning("Attempt %d/%d failed fetching ODIN RSS: %s", attempt, MAX_RETRIES, e)
                await asyncio.sleep(2 ** attempt)
        _LOGGER.error("All fetch attempts failed: %s", last_exc)
        return None

    async def async_update(self) -> None:
        # Build feed URL
        params = []
        if self._beredskabsID:
            params.append(f"beredskabsID={self._beredskabsID}")
        if self._station:
            params.append(f"enhed={self._station}")
        if self._count:
            params.append(f"antal={self._count}")
        url = f"{self._rss_url}?" + "&".join(params)

        try:
            session = async_get_clientsession(self.hass) if self.hass else async_get_clientsession(None)
        except Exception:
            # fallback: get a default session
            session = async_get_clientsession(None)

        # import aiohttp lazily to avoid import at module load time if not available
        try:
            import aiohttp
        except Exception as e:
            _LOGGER.error("aiohttp not available: %s", e)
            raise ConfigEntryNotReady from e

        raw = await self._fetch_raw(session, url)
        if raw is None:
            # failed to fetch
            self._state = None
            self._entries = []
            return

        # parse using feedparser (can parse bytes)
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
