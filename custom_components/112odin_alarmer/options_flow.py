"""Options flow that mirrors the config flow, with live fetch for dynamic dropdowns."""
from __future__ import annotations
import asyncio
import aiohttp
import feedparser
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DEFAULT_RSS_URL, CONF_BEREDSKABSID, CONF_STATION, CONF_COUNT, DEFAULT_COUNT
from typing import Any, Dict, List

class OdinOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry
        self._beredskabs_list: List[str] = []
        self._selected_id: str | None = None

    async def _fetch_feed(self) -> Any:
        url = DEFAULT_RSS_URL
        session = async_get_clientsession(self.config_entry.hass)
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.get(url, timeout=timeout) as resp:
            resp.raise_for_status()
            raw = await resp.read()
        loop = asyncio.get_running_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, raw)
        return feed

    async def async_step_init(self, user_input: Dict[str, Any] | None = None):
        # build beredskabs list
        if not self._beredskabs_list:
            try:
                feed = await self._fetch_feed()
            except Exception:
                return self.async_show_form(step_id="init", data_schema=vol.Schema({}), errors={"base": "fetch_error"})
            ids = []
            for entry in (feed.entries or []):
                link = entry.get('link', '')
                if 'beredskabsID=' in link:
                    try:
                        part = link.split('beredskabsID=')[1].split('&')[0]
                        if part and part not in ids:
                            ids.append(part)
                    except Exception:
                        pass
            if not ids:
                ids = [""]
            self._beredskabs_list = ids

        if user_input is None:
            default = self.config_entry.options.get(CONF_BEREDSKABSID, self.config_entry.data.get(CONF_BEREDSKABSID, self._beredskabs_list[0] if self._beredskabs_list else ""))
            schema = vol.Schema({
                vol.Required(CONF_BEREDSKABSID, default=default): vol.In(self._beredskabs_list)
            })
            return self.async_show_form(step_id="init", data_schema=schema)

        self._selected_id = user_input.get(CONF_BEREDSKABSID)
        return await self.async_step_station()

    async def async_step_station(self, user_input: Dict[str, Any] | None = None):
        try:
            feed = await self._fetch_feed()
        except Exception:
            return self.async_show_form(step_id="station", data_schema=vol.Schema({}), errors={"base": "fetch_error"})

        stations = []
        for entry in (feed.entries or []):
            link = entry.get('link', '')
            summary = entry.get('summary', '')
            if self._selected_id and self._selected_id not in link and self._selected_id not in summary:
                continue
            station = None
            if 'enhed=' in link:
                try:
                    station = link.split('enhed=')[1].split('&')[0]
                except Exception:
                    station = None
            if not station:
                title = entry.get('title', '')
                if '-' in title:
                    station = title.split('-')[0].strip()
            if station and station not in stations:
                stations.append(station)

        if not stations:
            stations = [""]

        if user_input is None:
            default_station = self.config_entry.options.get(CONF_STATION, self.config_entry.data.get(CONF_STATION, stations[0]))
            default_count = self.config_entry.options.get(CONF_COUNT, self.config_entry.data.get(CONF_COUNT, DEFAULT_COUNT))
            schema = vol.Schema({
                vol.Optional(CONF_STATION, default=default_station): vol.In(stations),
                vol.Optional(CONF_COUNT, default=default_count): vol.All(int, vol.Range(min=1, max=20))
            })
            return self.async_show_form(step_id="station", data_schema=schema)

        # save options
        return self.async_create_entry(title="Options updated", data={
            CONF_STATION: user_input.get(CONF_STATION, ""),
            CONF_COUNT: int(user_input.get(CONF_COUNT, DEFAULT_COUNT)),
            CONF_BEREDSKABSID: self._selected_id
        })
