# AGENTS.md

## What this is

A bilingual (EN/ZH) scrollytelling data-viz site that tests claims about Shanghai's climate — hotter summers, fading cold extremes, changing rain, improving air — against 45+ years of daily data. Live at <https://gderiddershanghai.github.io/shanghai-weather-app/>.

Prioritize clarity, simple explainable methods, and shareable visuals. No backends, no databases, no opaque statistics.

## Architecture (two layers, one rule each)

**Layer 1 — Python computes (build time).** `pipeline/` turns `data/*.csv` into chart-ready JSON in `static/data/derived/`. ALL statistics live here: DOY climatology with circular smoothing, anomaly-ranked outliers, heat/cold-wave detection, precip/wind events, AQI rollups. Run with `npm run data` (= `uv run python -m pipeline.build_derived`). CI regenerates these on every deploy — derived JSON is **not committed** (except `event-images/`).

**Layer 2 — SvelteKit renders (client).** Svelte 5 + D3-as-math-only (scales/shape/array — never d3-selection), SVG charts, adapter-static. JS may filter/group/count the compact tables; it must never re-derive statistics.

**The one chart system.** `src/lib/stores/chartState.ts` is the single source of truth. Story mode scroll-steps (`src/lib/story/steps.ts`) apply _partial presets_ to it; Explore mode controls bind to the same store; charts only read it. Never fork chart logic per mode.

## Data contracts

- Source of truth: `data/weather_shanghai.csv` (1980→present, Open-Meteo schema), `data/aqi_shanghai.csv` (2013→, aqicn per-pollutant), `data/events.csv` (curated bilingual news events, dd/mm/yyyy dates).
- `daily.json` is an array-of-arrays table; its column order is defined in `pipeline/config.py` (`DAILY_COMPACT_COLUMNS`) and mirrored by hand in `src/lib/data/daily.ts` (`COL`). A runtime assertion catches drift — if you change one, change both.
- Leap days: Feb 29 maps to DOY 59 and post-Feb leap-year dates shift −1, so every calendar date always hits the same DOY bin (fixed bug — don't regress).
- `uv_index_max` is 100% NaN and excluded; humidity is unavailable pre-1984 and excluded.

## Daily freshness

`.github/workflows/daily-data.yml` (07:30 Shanghai) fetches Open-Meteo (to today−6, ERA5 lag) and the WAQI feed (needs `WAQI_TOKEN` secret), commits if changed, and calls `deploy.yml` via `workflow_call` (GITHUB_TOKEN pushes don't trigger `push` workflows).

## Sharp edges

- **Base path:** deployed under `/shanghai-weather-app`. `paths.relative` is on, so `base` from `$app/paths` can be `'..'`-relative during SSR — never slice/concat it against pathnames (the language toggle broke this way once). Runtime fetches use `${base}/data/derived/…`.
- **i18n:** copy lives side-by-side (`{"key": {en, zh}}`) in `src/lib/i18n/copy.json`; `hooks.server.ts` stamps `<html lang>` at prerender; routes are `/en/…` + `/zh/…` via the `[lang=lang]` matcher; root `/` JS-redirects with _relative_ URLs.
- **Dates:** format manually (`src/lib/utils/format.ts`) — no `Intl` (WeChat webview quirks). `events.csv` is dd/mm/yyyy; compact tables use yyyymmdd ints.
- **Motion:** all animation goes through the Svelte 5 `Tween` class wired in `stores/tweens.ts`, which zeroes durations under `prefers-reduced-motion`.
- Do not modify or rely on `Nbs/*.ipynb` (exploratory only) or `shanghai_weather/` (raw source archive).

## Conventions

- Chart colors/tokens live in `src/app.css` (`--color-hot/cold/band/median`); same category = same color in every chart. Hot/cold are also encoded by position (above/below band), never color alone.
- Curated events: extend `data/events.csv` (categories HOT/COLD/RAIN/TYPHOON/AQI). `(TBD)` cells and non-URL text are nulled by `pipeline/events_curated.py`. Event thumbnails are fetched locally with `uv run python -m pipeline.og_images` and committed — never fetched in CI.
- Commits: no AI co-author trailers.
