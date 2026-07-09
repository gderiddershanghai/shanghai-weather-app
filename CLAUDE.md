# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm run dev          # dev server (vite)
npm run build        # static build -> build/   (CI adds BASE_PATH=/shanghai-weather-app)
npm run check        # svelte-kit sync + svelte-check (keep at 0 errors/warnings)
npm run lint         # prettier --check
npm run data         # regenerate static/data/derived/*.json from data/*.csv
uv sync              # install Python deps (pyproject.toml; uv, not pip)
uv run python -m pipeline.fetch.open_meteo   # append new weather days (also does backfills)
uv run python -m pipeline.fetch.aqi_feed     # append today's AQI (needs WAQI_TOKEN) / --import-csv for backfill
uv run python -m pipeline.og_images          # fetch event thumbnails (LOCAL only, commit results)
```

There is no test runner; verification = `npm run check` + `npm run build` + running `npm run data` cleanly (it contains build-failing sanity assertions).

## Architecture

Two layers with a hard boundary:

1. **`pipeline/` (Python, build time)** — owns ALL statistics. `build_derived.py` orchestrates: `temperature.py` (DOY climatology p01–p99 with circular smoothing, anomaly-ranked outliers, heat/cold waves), `precip_wind.py`, `aqi.py`, `events_curated.py` → compact JSON in `static/data/derived/`. Derived JSON is regenerated in CI and **not committed** (except `event-images/`).
2. **`src/` (SvelteKit, Svelte 5 runes)** — renders SVG charts with D3 as a math library only (no d3-selection). Client JS may filter/group the shipped tables but never re-derives statistics.

**One store, two drivers.** `src/lib/stores/chartState.ts` holds all chart config. Story mode (`src/lib/story/steps.ts` — steps are *partial presets* applied on scroll via `Scrolly.svelte`) and Explore mode (`src/lib/explore/ControlPanel.svelte`) both write it; chart components in `src/lib/charts/` only read it (plus `stores/tweens.ts` for animated domains). Never duplicate chart logic per mode — that's the cardinal rule.

**i18n:** prerendered `/en/` + `/zh/` via `[lang=lang]` routes; copy is side-by-side `{en, zh}` in `src/lib/i18n/copy.json`; `hooks.server.ts` stamps `<html lang>` at prerender.

## Contracts & sharp edges (violating these breaks prod)

- `daily.json` column order: `pipeline/config.py DAILY_COMPACT_COLUMNS` ⇄ `src/lib/data/daily.ts COL` are hand-mirrored; a runtime assert catches drift. Change both or neither.
- `base` from `$app/paths` may be `'..'`-relative during SSR (`paths.relative`): never slice/concat it with pathnames. Use it only as `${base}/...` prefix.
- Leap-day DOY: Feb 29 → 59 and post-Feb leap dates shift −1 (`temperature.py add_time_fields`) — keeps every calendar date in one DOY bin. Don't regress.
- Dates are formatted manually (`utils/format.ts`, no `Intl`); `events.csv` is dd/mm/yyyy; compact tables use yyyymmdd ints.
- Weather fetches stop at today−6 (ERA5 archive lag). "Data through" comes from `meta.json`.
- `Nbs/` notebooks and `shanghai_weather/` raw files are read-only archives.
- Chart conventions: tokens in `src/app.css`; same category = same color everywhere; hot/cold dots are position-encoded (above/below the band), never color-only; direct labels over legends.
- Commits: no AI co-author trailers.

## CI

`deploy.yml`: push→main builds derived data (uv) + site (BASE_PATH set) → GitHub Pages. `daily-data.yml`: 07:30 Shanghai cron appends weather/AQI, commits, then calls deploy via `workflow_call` (GITHUB_TOKEN pushes don't retrigger `push` workflows).

`AGENTS.MD` holds the same picture with more design rationale — keep the two in sync.
