"""Options flow for 112Odin Alarmer."""
import voluptuous as vol
from homeassistant import config_entries
from .const import CONF_STATION, CONF_COUNT, DEFAULT_COUNT

class OdinOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        schema = vol.Schema({
            vol.Optional(CONF_STATION, default=self.config_entry.options.get(CONF_STATION, self.config_entry.data.get(CONF_STATION, ""))): str,
            vol.Optional(CONF_COUNT, default=self.config_entry.options.get(CONF_COUNT, self.config_entry.data.get(CONF_COUNT, DEFAULT_COUNT))): vol.All(int, vol.Range(min=1, max=20))
        })
        if user_input is None:
            return self.async_show_form(step_id="init", data_schema=schema)
        return self.async_create_entry(title="Options updated", data=user_input)
