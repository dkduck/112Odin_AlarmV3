# 112Odin Alarmer (v1.2)

Custom Home Assistant integration to fetch 112 (ODIN) alarms via ODIN RSS.

New in v1.2
- Uses aiohttp for robust network fetching with timeout, retries and backoff.
- Updated manifest to include `aiohttp` requirement.
- GitHub-ready repo structure with LICENSE, .gitignore and GitHub Actions workflow for releases.

Features
- HACS friendly (place in custom_components)
- GUI setup (Config Flow) — enter beredskabsID (GUID), station (optional), and number of events (1–20)
- Options flow to update station/antal after setup
- Stores full summary/description for each event in `sensor` entity attributes (entries)
- Uses `aiohttp` + `feedparser` for robust fetch + parse

Installation
1. Unzip `112Odin_Alarmer_v3.zip`
2. Copy `custom_components/112odin_alarmer` into your Home Assistant `custom_components` folder
3. Restart Home Assistant
4. Add integration via Settings -> Devices & Services -> Add Integration -> search for "112Odin Alarmer"

Preparing for HACS / GitHub
- Repo name suggestion: `112Odin-Alarmer`
- Place the `custom_components/112odin_alarmer` folder at the root of the repo.
- Create a release (tag) on GitHub; HACS looks for releases.

Notes
- If Home Assistant already has aiohttp available (it does), the integration will use the HA client session.
- If entity_id doesn't become `sensor.112odin` automatically, rename it in the Entity Registry.
