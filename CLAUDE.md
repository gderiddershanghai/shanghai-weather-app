# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A client-side data-visualization app that analyzes **Shanghai weather and air quality** (1980–present) to test common claims — hotter summers, changing rainfall, better/worse air quality — and present the answers as **clear, explainable charts**. Prioritize clarity, simple methods, and shareable visuals over complex modeling or infrastructure.

## Current state (important)

The repo is mostly **scaffolding**. `src/app/index.js` and `src/app/routes.js` are one-line stubs; nearly every directory under `src/` (`modes/`, `viz/`, `components/`, `styles/`, `app/state/`) contains only `.gitkeep`. There is **no `package.json`, bundler, test runner, or lint config yet** — so no build/test/lint commands exist to run. When adding the frontend, you are choosing the stack; keep it light (see constraints below).

The only real, working code is the Python analysis layer in `src/analysis_py/`.

## Python analysis layer

`src/analysis_py/temperature_datasets.py` is a self-contained pandas/numpy pipeline that turns raw daily weather into chart-ready tables. Entry point:

```python
from src.analysis_py.temperature_datasets import compute_temperature_tables, TempConfig
df_daily, df_clim, df_enriched, df_outliers, df_events = compute_temperature_tables(df_raw)
```

Key design points to understand before editing:

- **Day-of-year (DOY) climatology is the backbone.** Everything is computed per-DOY (quantiles p01/p05/p50/p95/p99), then smoothed with a **circular** rolling window (`circular_rolling`) so Dec 31 ↔ Jan 1 wrap correctly. Leap days are mapped to Feb 28 (DOY 59) by default to keep DOY stats stable across years.
- **"Real" vs "feels-like" run in parallel.** Real uses `temperature_2m_max/min`; feels-like uses `apparent_temperature_max/min`. The code deliberately mirrors both through the same functions with `tmax/tmin` vs `atmax/atmin` prefixes — keep that symmetry when extending.
- **Severity is anomaly vs DOY median**, not absolute temperature: hot = `value − p50(doy)`, cold = `p50(doy) − value`. Both are "higher = more extreme" so tables sort uniformly.
- Two extremes tables: `df_outliers` (single extreme days, filtered by p99/p95 threshold) and `df_events` (multi-day heat/cold waves, ≥`min_event_days`, ranked by peak severity then duration).
- All tuning lives in the frozen `TempConfig` dataclass (column names, quantiles, smoothing window, leap-day policy). Prefer changing config over hard-coding.

## Data

- **CSV is the source of truth**, kept as static files in `public/data/` (`weather_shanghai.csv`, `aqi_shanghai.csv`). Easy to inspect and replace.
- **Derived JSON is allowed** for chart-ready payloads (e.g. monthly rollups) under `public/data/derived/`.
- Weather CSVs have an unnamed index column plus `time`, `temperature_2m_*`, `apparent_temperature_*`, `precipitation_*`, wind, sunshine, and `uv_index_max`. `weather_shanghai2.csv` is the same schema with apparent-temperature columns backfilled.
- Raw/unprocessed source files and spreadsheets live in `shanghai_weather/`; exploratory notebooks live in `Nbs/`.

## Two application modes (must share primitives)

- **Story mode** — fixed scrollytelling narrative; each section = one claim, one chart, one takeaway.
- **Explore mode** — free interactive inspection with filters (time range, metric, thresholds).

Both modes must reuse the **same data, chart primitives, and scales**. Do **not** duplicate chart logic between them — that's the primary architectural rule. Charts belong in `src/viz/charts/`, with data loaders/transforms and encodings/scales factored into `src/viz/data/` and `src/viz/encodings/`.

## Constraints

- Developed and run **inside WSL / Linux**. Use Linux paths and tooling; don't assume Windows paths.
- Do **not** modify or depend on `.ipynb` files in `Nbs/` — they are exploratory only.
- Do **not** add backends, databases, or build-heavy frameworks.
- Do **not** add complex statistical models or opaque transformations — methods should stay explainable.
- You may freely reorganize/rename files for clarity (including moving cleaned CSVs into `public/data/`) as long as the structure stays minimal.

Note: `AGENTS.MD` holds the fuller version of this intent and the target folder layout; keep the two consistent if you change project direction.
