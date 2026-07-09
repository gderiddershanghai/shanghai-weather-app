# Shanghai Weather Stories · 上海天气故事

**Live: <https://gderiddershanghai.github.io/shanghai-weather-app/>**

A bilingual (English/中文) scrollytelling data essay that tests what people say about Shanghai's climate — *summers are hotter, the deep cold is disappearing, the rain is wilder, the air is cleaner* — against 45+ years of daily weather data and 12 years of air-quality measurements.

- **Story mode** walks through seven chapters: the shape of a normal year, record heat, the vanishing cold (including the 2016 frozen-pipes winter), the plum rains and typhoons, the air-quality turnaround, and how temperature and smog travel together.
- **Explore mode** hands you the same charts with filters: climatology, time series, monthly heatmaps, and the temperature×PM2.5 scatter.
- Extreme days link to what the newspapers said at the time — in both languages.

## Data

| Source | Coverage | What |
|---|---|---|
| [Open-Meteo](https://open-meteo.com/) (ERA5) | 1980 → today−6 | daily temperature, feels-like, precipitation, wind, sunshine |
| [aqicn.org](https://aqicn.org/) | 2013 → present | daily PM2.5/PM10/O₃/NO₂/SO₂/CO |
| `data/events.csv` | 1980 → present | hand-curated extreme events with EN/ZH news citations |

Data refreshes itself daily via a GitHub Actions cron; statistics are computed at build time by the Python pipeline in `pipeline/` and shipped as static JSON — the site has no backend.

## Develop

```bash
npm install && uv sync   # deps (frontend / pipeline)
npm run data             # build derived JSON from data/*.csv
npm run dev              # dev server
```

See `CLAUDE.md` / `AGENTS.MD` for architecture and contribution guardrails.
