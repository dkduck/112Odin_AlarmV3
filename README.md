# 112Odin Alarmer (v1.3)

This release adds a fully dynamic GUI setup that fetches available BeredskabsID and Stations
from ODIN RSS live during the config flow. It includes loading indicators and clear error messages
if the feed cannot be fetched.

Key features
- Live fetch of BeredskabsID and Stations during config flow (no hardcoding)
- Two-step config flow: choose BeredskabsID, then choose Station + count
- Options flow mirrors the same dynamic behavior
- Uses aiohttp for robust network fetching (timeouts, retries) and feedparser for parsing

Installation
1. Unzip `112Odin_Alarmer_v1_3.zip`
2. Copy `custom_components/112odin_alarmer` to your Home Assistant `custom_components` folder
3. Restart Home Assistant
4. Add integration via Settings -> Devices & Services -> Add Integration -> search for "112Odin Alarmer"

Notes
- If the feed cannot be fetched during setup you'll see an error in the UI; try again later.
- The integration stores full summary/description in sensor attributes under `entries`.
