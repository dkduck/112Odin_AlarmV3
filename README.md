# 112Odin Alarmer (v1.5)

Fuldt HACS-ready release med live opsætning (dansk + engelsk).

Manual install:
1. Unzip `112Odin_Alarmer_v1_5.zip`.
2. Copy `custom_components/112odin_alarner` to your Home Assistant `custom_components` folder.
3. Restart Home Assistant.
4. Settings → Devices & Services → Add Integration → search "112Odin Alarmer".

HACS install:
- Create GitHub repo `112Odin-Alarmer`, push these files to repo root and tag a release `v1.5.0`.
- Add repository in HACS (Integration category) and install.

Notes:
- Config flow fetches BeredskabsID and Stations live from ODIN RSS during setup.
- If feed cannot be fetched, UI shows a clear error and a retry option.
