"""Config flow with dynamic live-fetched dropdowns from ODIN RSS."""
from __future__ import annotations
import asyncio
import feedparser
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, DEFAULT_RSS_URL, CONF_BEREDSKABSID, CONF_STATION, CONF_COUNT, DEFAULT_COUNT
from typing import Any, Dict, List

class OdinConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for 112Odin Alarmer."""

    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        self._beredskabs_list: List[str] = []
        self._selected_id: str | None = None

    async def _fetch_feed(self) -> Any:
        session = async_get_clientsession(self.hass)
        timeout = 10
        async with session.get(DEFAULT_RSS_URL, timeout=timeout) as resp:
            resp.raise_for_status()
            raw = await resp.read()
        loop = asyncio.get_running_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, raw)
        return feed

    async def async_step_user(self, user_input: Dict[str, Any] | None = None):
        errors = {}
        if not self._beredskabs_list:
            try:
                feed = await self._fetch_feed()
            except Exception:
                errors["base"] = "fetch_error"
                return self.async_show_form(step_id="user", data_schema=vol.Schema({}), errors=errors)

            ids: List[str] = []
            for entry in (feed.entries or []):
                link = entry.get('link', '') or ''
                summary = entry.get('summary', '') or ''
                if 'beredskabsID=' in link:
                    try:
                        val = link.split('beredskabsID=')[1].split('&')[0]
                        if val and val not in ids:
                            ids.append(val)
                    except Exception:
                        pass
                if 'beredskabsID=' in summary:
                    try:
                        val = summary.split('beredskabsID=')[1].split('&')[0]
                        if val and val not in ids:
                            ids.append(val)
                    except Exception:
                        pass
            if not ids:
                ids = [""]
            self._beredskabs_list = ids

        if user_input is None:
            schema = vol.Schema({
                vol.Required(CONF_BEREDSKABSID, default=self._beredskabs_list[0]): vol.In(self._beredskabs_list)
            })
            return self.async_show_form(step_id="user", data_schema=schema)

        self._selected_id = user_input.get(CONF_BEREDSKABSID)
        return await self.async_step_station()

    async def async_step_station(self, user_input: Dict[str, Any] | None = None):
        errors = {}
        try:
            feed = await self._fetch_feed()
        except Exception:
            errors["base"] = "fetch_error"
            return self.async_show_form(step_id="station", data_schema=vol.Schema({}), errors=errors)

        stations: List[str] = []
        for entry in (feed.entries or []):
            link = entry.get('link', '') or ''
            summary = entry.get('summary', '') or ''
            title = entry.get('title', '') or ''
            if self._selected_id and self._selected_id not in link and self._selected_id not in summary:
                continue
            station = None
            if 'enhed=' in link:
                try:
                    station = link.split('enhed=')[1].split('&')[0]
                except Exception:
                    station = None
            if not station and '-' in title:
                station = title.split('-')[0].strip()
            if station and station not in stations:
                stations.append(station)

        if not stations:
            stations = [""]

        if user_input is None:
            schema = vol.Schema({
                vol.Optional(CONF_STATION, default=stations[0]): vol.In(stations),
                vol.Optional(CONF_COUNT, default=DEFAULT_COUNT): vol.All(int, vol.Range(min=1, max=20))
            })
            return self.async_show_form(step_id="station", data_schema=schema)

        data = {
            CONF_BEREDSKABSID: self._selected_id,
            CONF_STATION: user_input.get(CONF_STATION, ""),
            CONF_COUNT: int(user_input.get(CONF_COUNT, DEFAULT_COUNT)),
            "rss_url": DEFAULT_RSS_URL
        }
        title = f"112odin {self._selected_id}"
        return self.async_create_entry(title=title, data=data)
