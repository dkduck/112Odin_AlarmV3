"""Config flow with dynamic, live-fetched dropdowns from ODIN RSS."""

from __future__ import annotations
import asyncio
import aiohttp
import feedparser
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, DEFAULT_RSS_URL, CONF_BEREDSKABSID, CONF_STATION, CONF_COUNT, DEFAULT_COUNT
from typing import Any, Dict, List

class OdinConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        # cache to avoid refetching during the flow
        self._feed_cache: Dict[str, Any] = {}
        self._beredskabs_list: List[str] = []

    async def _fetch_feed(self) -> Any:
        # fetch raw RSS and parse with feedparser
        url = DEFAULT_RSS_URL
        session = async_get_clientsession(self.hass)
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.get(url, timeout=timeout) as resp:
            resp.raise_for_status()
            raw = await resp.read()
        loop = asyncio.get_running_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, raw)
        return feed

    async def async_step_user(self, user_input: Dict[str, Any] | None = None):
        """First step: fetch list of BeredskabsID and show dropdown."""
        errors = {}
        # If we've already cached, reuse
        if not self._beredskabs_list:
            try:
                feed = await self._fetch_feed()
            except Exception:
                errors["base"] = "fetch_error"
                # show a basic form with a retry button
                schema = vol.Schema({})
                return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

            # extract unique beredskabsID values from feed entries
            ids = []
            for entry in (feed.entries or []):
                # heuristics: feed may include beredskabsID as a query param in link or in summary
                link = entry.get('link', '')
                # try to extract 'beredskabsID=' from link
                if 'beredskabsID=' in link:
                    try:
                        part = link.split('beredskabsID=')[1].split('&')[0]
                        if part and part not in ids:
                            ids.append(part)
                    except Exception:
                        pass
                # also check summary for GUID-like patterns (naive)
                summary = entry.get('summary', '')
                if 'beredskabsID=' in summary:
                    try:
                        part = summary.split('beredskabsID=')[1].split('&')[0]
                        if part and part not in ids:
                            ids.append(part)
                    except Exception:
                        pass
            # fallback: if no IDs found, offer an empty text option
            if not ids:
                ids = [""]
            self._beredskabs_list = ids

        if user_input is None:
            # show dropdown
            options = {i: i for i in self._beredskabs_list}
            schema = vol.Schema({
                vol.Required(CONF_BEREDSKABSID, default=self._beredskabs_list[0]): vol.In(list(options.keys()))
            })
            return self.async_show_form(step_id="user", data_schema=schema)

        # user selected an ID -> proceed to station step
        self._selected_id = user_input.get(CONF_BEREDSKABSID)
        return await self.async_step_station()

    async def async_step_station(self, user_input: Dict[str, Any] | None = None):
        """Second step: fetch stations (filtered by selected ID) and show dropdown + count."""
        errors = {}
        # use cached feed if available, otherwise fetch
        try:
            feed = await self._fetch_feed()
        except Exception:
            errors["base"] = "fetch_error"
            schema = vol.Schema({})
            return self.async_show_form(step_id="station", data_schema=schema, errors=errors)

        stations = []
        for entry in (feed.entries or []):
            # try to find station in entry (simple heuristic)
            link = entry.get('link', '')
            summary = entry.get('summary', '')
            # only include entries that match selected beredskabsID
            if self._selected_id and self._selected_id not in link and self._selected_id not in summary:
                continue
            # attempt to extract enhed=station from link
            station = None
            if 'enhed=' in link:
                try:
                    station = link.split('enhed=')[1].split('&')[0]
                except Exception:
                    station = None
            # if not in link, try to infer from title/summary (naive: take first word before '-')</n                    if not station:
                title = entry.get('title', '')
                if '-' in title:
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

        # finalize config entry
        data = {
            CONF_BEREDSKABSID: self._selected_id,
            CONF_STATION: user_input.get(CONF_STATION, ""),
            CONF_COUNT: int(user_input.get(CONF_COUNT, DEFAULT_COUNT)),
            "rss_url": DEFAULT_RSS_URL
        }
        return self.async_create_entry(title=f"112odin {self._selected_id}", data=data)
