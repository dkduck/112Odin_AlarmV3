"""Config flow for 112Odin Alarmer."""
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, DEFAULT_COUNT, DEFAULT_RSS_URL, CONF_BEREDSKABSID, CONF_STATION, CONF_COUNT

class OdinConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        errors = {}
        schema = vol.Schema({
            vol.Required(CONF_BEREDSKABSID): str,
            vol.Optional(CONF_STATION, default=""): str,
            vol.Optional(CONF_COUNT, default=DEFAULT_COUNT): vol.All(int, vol.Range(min=1, max=20))
        })
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=schema)
        # Basic validation: beredskabsID should not be empty
        if not user_input.get(CONF_BEREDSKABSID):
            errors["base"] = "beredskabsid_required"
            return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
        # create entry
        return self.async_create_entry(title=f"112odin {user_input.get(CONF_BEREDSKABSID)}", data={
            CONF_BEREDSKABSID: user_input.get(CONF_BEREDSKABSID),
            CONF_STATION: user_input.get(CONF_STATION, ""),
            CONF_COUNT: user_input.get(CONF_COUNT, DEFAULT_COUNT),
            "rss_url": DEFAULT_RSS_URL
        })
