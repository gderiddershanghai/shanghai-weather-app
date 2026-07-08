# pipeline/build_derived.py
# Orchestrator: reads source CSVs from data/, emits chart-ready JSON into
# static/data/derived/. This is the single command CI runs before `vite build`.
#
#   python3 -m pipeline.build_derived [--skip-images]

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

import pandas as pd

from .aqi import binned_medians, load_aqi, temp_aqi_join, yearly_summary
from .config import DAILY_COMPACT_COLUMNS, DERIVED_DIR, WEATHER_CSV
from .emit import date_to_int, df_to_compact, series_round, write_json
from .events_curated import load_curated_events
from .precip_wind import PrecipConfig, compute_precip_tables
from .temperature import TempConfig, compute_temperature_tables

# Smoothed climatology series exposed to the frontend (renamed without the _sm15 suffix).
CLIM_SERIES = [
    "tmax_p50", "tmax_p95", "tmax_p99",
    "tmin_p50", "tmin_p05", "tmin_p01",
    "atmax_p50", "atmax_p95", "atmax_p99",
    "atmin_p50", "atmin_p05", "atmin_p01",
]

OUTLIER_SERIES_ENUM = ["real_hot", "real_cold", "feel_hot", "feel_cold"]


def load_weather() -> pd.DataFrame:
    df = pd.read_csv(WEATHER_CSV)
    # normalize legacy export artifacts
    df = df.loc[:, [c for c in df.columns if not c.lower().startswith("unnamed")]]
    df = df.drop(columns=[c for c in ("uv_index_max",) if c in df.columns])
    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    return df


def emit_climatology(df_clim: pd.DataFrame, cfg: TempConfig) -> dict:
    w = cfg.smooth_window_days
    d = df_clim.sort_values("doy")
    out: dict = {
        "doy": [int(v) for v in d["doy"]],
        "date_ref": [ts.strftime("%m-%d") for ts in d["date_ref"]],
    }
    for name in CLIM_SERIES:
        out[name] = series_round(d[f"{name}_sm{w}"])
    return out


def emit_daily(df: pd.DataFrame) -> dict:
    d = df.copy()
    d["_date_int"] = date_to_int(d["time"])
    d["_sun_h"] = d["sunshine_duration"] / 3600.0
    csv_col = dict(DAILY_COMPACT_COLUMNS)
    csv_col["date"] = "_date_int"
    csv_col["sun_h"] = "_sun_h"
    renamed = d.rename(columns={v: k for k, v in csv_col.items()})
    return df_to_compact(renamed, list(DAILY_COMPACT_COLUMNS.keys()))


def emit_outliers(df_outliers: pd.DataFrame) -> dict:
    d = df_outliers.copy()
    d["_date_int"] = date_to_int(d["date"])
    d["_series_idx"] = d["series"].map(OUTLIER_SERIES_ENUM.index)
    d = d.rename(
        columns={
            "_date_int": "date_i",
            "_series_idx": "series_i",
            "severity_score": "severity",
            "baseline_p50": "baseline",
        }
    )
    payload = df_to_compact(d, ["date_i", "doy", "series_i", "value", "severity", "baseline"])
    # rename for the frontend contract
    payload["columns"] = ["date", "doy", "series", "value", "severity", "baseline_p50"]
    payload["series_enum"] = OUTLIER_SERIES_ENUM
    return payload


def emit_precip_events(tables: dict) -> list[dict]:
    # Shanghai is wet: "2+ consecutive rain days" matches thousands of runs.
    # Ship only the rankable tail the app can actually show.
    tables = dict(tables)
    tables["rain_events"] = tables["rain_events"].head(100)
    tables["high_wind_days"] = tables["high_wind_days"].head(60)

    events: list[dict] = []
    for _, r in tables["rain_events"].iterrows():
        start = r["start_date"].strftime("%Y-%m-%d")
        events.append(
            {
                "id": f"rain_event_{start}",
                "type": "rain_event",
                "start": start,
                "end": r["end_date"].strftime("%Y-%m-%d"),
                "days": int(r["duration_days"]),
                "peak_date": r["peak_date"].strftime("%Y-%m-%d"),
                "peak_value": float(r["peak_value"]),
                "total_mm": float(r["total_mm"]),
                "year": int(r["year"]),
            }
        )
    for _, r in tables["extreme_rain_days"].iterrows():
        iso = r["date"].strftime("%Y-%m-%d")
        events.append(
            {
                "id": f"extreme_rain_day_{iso}",
                "type": "extreme_rain_day",
                "start": iso,
                "end": iso,
                "days": 1,
                "peak_date": iso,
                "peak_value": float(r["value"]),
                "year": int(r["year"]),
            }
        )
    for _, r in tables["high_wind_days"].iterrows():
        iso = r["date"].strftime("%Y-%m-%d")
        events.append(
            {
                "id": f"high_wind_day_{iso}",
                "type": "high_wind_day",
                "start": iso,
                "end": iso,
                "days": 1,
                "peak_date": iso,
                "peak_value": float(r["value"]),
                "year": int(r["year"]),
            }
        )
    for _, r in tables["dry_spells"].iterrows():
        start = r["start_date"].strftime("%Y-%m-%d")
        events.append(
            {
                "id": f"dry_spell_{start}",
                "type": "dry_spell",
                "start": start,
                "end": r["end_date"].strftime("%Y-%m-%d"),
                "days": int(r["duration_days"]),
                "year": int(r["year"]),
            }
        )
    return events


def emit_monthly(df_daily: pd.DataFrame, aqi: pd.DataFrame) -> dict:
    """One row per (year, month) — feeds every heatmap."""
    d = df_daily.copy()
    g = d.groupby(["year", "month"])
    monthly = g.agg(
        tmax_mean=("temperature_2m_max", "mean"),
        tmin_mean=("temperature_2m_min", "mean"),
        days_ge_35=("temperature_2m_max", lambda s: int((s >= 35).sum())),
        days_le_0=("temperature_2m_min", lambda s: int((s <= 0).sum())),
        prcp_sum=("precipitation_sum", "sum"),
        wet_days=("precipitation_sum", lambda s: int((s >= 0.1).sum())),
        prcp_max_day=("precipitation_sum", "max"),
        gust_max=("wind_gusts_10m_max", "max"),
    ).reset_index()

    am = (
        aqi.groupby(["year", "month"])
        .agg(
            pm25_median=("pm25", "median"),
            days_pm25_gt_100=("pm25", lambda s: int((s > 100).sum())),
        )
        .reset_index()
    )
    monthly = monthly.merge(am, on=["year", "month"], how="left")
    cols = [
        "year", "month", "tmax_mean", "tmin_mean", "days_ge_35", "days_le_0",
        "prcp_sum", "wet_days", "prcp_max_day", "gust_max",
        "pm25_median", "days_pm25_gt_100",
    ]
    return df_to_compact(monthly, cols)


def emit_temp_events(df_events: pd.DataFrame) -> list[dict]:
    events = []
    for _, r in df_events.iterrows():
        start = r["start_date"].strftime("%Y-%m-%d")
        events.append(
            {
                "id": f"{r['event_type']}_{start}",
                "type": r["event_type"],
                "start": start,
                "end": r["end_date"].strftime("%Y-%m-%d"),
                "days": int(r["duration_days"]),
                "peak_date": r["peak_date"].strftime("%Y-%m-%d"),
                "peak_value": float(r["peak_value"]),
                "peak_severity": float(r["peak_severity"]),
                "year": int(r["year"]),
            }
        )
    return events


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build derived JSON for the app")
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="skip OG image fetching (CI default; images are fetched locally and committed)",
    )
    args = parser.parse_args(argv)

    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    sizes: dict[str, int] = {}

    print("loading weather…", flush=True)
    weather = load_weather()
    cfg = TempConfig()

    print("computing temperature tables…", flush=True)
    df_daily, df_clim, df_enriched, df_outliers, df_events = compute_temperature_tables(weather, cfg)

    # sanity checks — fail the build loudly rather than ship broken stats
    w = cfg.smooth_window_days
    clim_check = df_clim[f"tmax_p95_sm{w}"] >= df_clim[f"tmax_p50_sm{w}"]
    assert clim_check.all(), "climatology violated: p95 < p50 somewhere"
    assert len(df_clim) == 365, f"expected 365 DOY rows, got {len(df_clim)}"

    sizes["climatology.json"] = write_json(DERIVED_DIR / "climatology.json", emit_climatology(df_clim, cfg))
    sizes["daily.json"] = write_json(DERIVED_DIR / "daily.json", emit_daily(weather))
    sizes["outliers.json"] = write_json(DERIVED_DIR / "outliers.json", emit_outliers(df_outliers))
    sizes["temp-events.json"] = write_json(DERIVED_DIR / "temp-events.json", emit_temp_events(df_events))

    print("computing precip/wind tables…", flush=True)
    precip_tables = compute_precip_tables(df_daily, PrecipConfig())
    sizes["precip-events.json"] = write_json(
        DERIVED_DIR / "precip-events.json", emit_precip_events(precip_tables)
    )

    print("computing AQI tables…", flush=True)
    aqi = load_aqi()
    aqi_daily = aqi.copy()
    aqi_daily["date_i"] = date_to_int(aqi_daily["date"])
    aqi_payload = df_to_compact(
        aqi_daily.rename(columns={"date_i": "date_int"}),
        ["date_int", "pm25", "pm10", "o3", "no2", "so2", "co"],
    )
    aqi_payload["columns"][0] = "date"
    sizes["aqi-daily.json"] = write_json(DERIVED_DIR / "aqi-daily.json", aqi_payload)
    sizes["aqi-derived.json"] = write_json(
        DERIVED_DIR / "aqi-derived.json", {"yearly": yearly_summary(aqi)}
    )

    joined = temp_aqi_join(aqi, weather)
    joined["date_int"] = date_to_int(joined["date"])
    temp_aqi_payload = df_to_compact(joined, ["date_int", "tmax", "tmin", "pm25", "o3", "season"])
    temp_aqi_payload["columns"][0] = "date"
    temp_aqi_payload["binned"] = binned_medians(joined)
    sizes["temp-aqi.json"] = write_json(DERIVED_DIR / "temp-aqi.json", temp_aqi_payload)

    sizes["monthly.json"] = write_json(DERIVED_DIR / "monthly.json", emit_monthly(df_daily, aqi))

    print("loading curated events…", flush=True)
    curated = load_curated_events()
    sizes["events-curated.json"] = write_json(DERIVED_DIR / "events-curated.json", curated)

    if not args.skip_images:
        from .og_images import fetch_event_images

        fetch_event_images(curated)
        # re-emit with freshly discovered image paths
        curated = load_curated_events()
        sizes["events-curated.json"] = write_json(DERIVED_DIR / "events-curated.json", curated)

    meta = {
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "weather": {
            "start": weather["time"].min().strftime("%Y-%m-%d"),
            "end": weather["time"].max().strftime("%Y-%m-%d"),
            "rows": int(len(weather)),
        },
        "aqi": {
            "start": aqi["date"].min().strftime("%Y-%m-%d"),
            "end": aqi["date"].max().strftime("%Y-%m-%d"),
            "rows": int(len(aqi)),
            "pm25_start": aqi.loc[aqi["pm25"].notna(), "date"].min().strftime("%Y-%m-%d"),
        },
        "counts": {
            "outlier_days": int(len(df_outliers)),
            "temp_events": int(len(df_events)),
            "curated_events": len(curated),
        },
        "config": {
            "smooth_window_days": cfg.smooth_window_days,
            "heat_q": cfg.heat_q,
            "cold_q": cfg.cold_q,
            "min_event_days": cfg.min_event_days,
        },
    }
    sizes["meta.json"] = write_json(DERIVED_DIR / "meta.json", meta)

    print("\nemitted:")
    for name, size in sizes.items():
        print(f"  {name:24s} {size/1024:8.1f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
