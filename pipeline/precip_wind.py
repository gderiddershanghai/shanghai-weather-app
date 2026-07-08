# pipeline/precip_wind.py
# Rain/storm derivations, mirroring temperature.py's shape:
#   - extreme rain days (wet-day p99)
#   - multi-day rain events (consecutive wet days, ranked by total)
#   - high-wind days (gust p99 — typhoon candidates)
#   - dry spells (longest runs without rain)

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class PrecipConfig:
    date_col: str = "time"
    prcp_col: str = "precipitation_sum"
    gust_col: str = "wind_gusts_10m_max"

    wet_day_mm: float = 0.1     # threshold for "it rained"
    extreme_q: float = 0.99     # of wet days only (else zeros dominate)
    gust_q: float = 0.99
    min_rain_event_days: int = 2
    min_dry_spell_days: int = 20


def _runs(mask: pd.Series, dates: pd.Series) -> pd.Series:
    """Run ids over consecutive calendar days where mask holds."""
    date_gap = dates.diff().dt.days.fillna(1).ne(1)
    return ((~mask.fillna(False)) | date_gap).cumsum()


def extreme_rain_days(d: pd.DataFrame, cfg: PrecipConfig) -> pd.DataFrame:
    wet = d[d[cfg.prcp_col] >= cfg.wet_day_mm]
    thr = wet[cfg.prcp_col].quantile(cfg.extreme_q)
    out = wet[wet[cfg.prcp_col] >= thr][["date", "year", "doy", cfg.prcp_col]].copy()
    out = out.rename(columns={cfg.prcp_col: "value"})
    out["threshold"] = round(float(thr), 1)
    return out.sort_values("value", ascending=False).reset_index(drop=True)


def high_wind_days(d: pd.DataFrame, cfg: PrecipConfig) -> pd.DataFrame:
    thr = d[cfg.gust_col].quantile(cfg.gust_q)
    out = d[d[cfg.gust_col] >= thr][["date", "year", "doy", cfg.gust_col, cfg.prcp_col]].copy()
    out = out.rename(columns={cfg.gust_col: "value", cfg.prcp_col: "prcp"})
    out["threshold"] = round(float(thr), 1)
    return out.sort_values("value", ascending=False).reset_index(drop=True)


def rain_events(d: pd.DataFrame, cfg: PrecipConfig) -> pd.DataFrame:
    is_wet = d[cfg.prcp_col] >= cfg.wet_day_mm
    run_id = _runs(is_wet, d["date"])
    events = []
    for _, g in d[is_wet].groupby(run_id):
        if len(g) < cfg.min_rain_event_days:
            continue
        total = float(g[cfg.prcp_col].sum())
        peak = g.loc[g[cfg.prcp_col].idxmax()]
        events.append(
            {
                "event_type": "rain_event",
                "start_date": g["date"].min(),
                "end_date": g["date"].max(),
                "duration_days": int(len(g)),
                "peak_date": peak["date"],
                "peak_value": float(peak[cfg.prcp_col]),
                "total_mm": round(total, 1),
                "year": int(g["year"].iloc[0]),
            }
        )
    out = pd.DataFrame(events)
    if out.empty:
        return out
    return out.sort_values(["total_mm"], ascending=False).reset_index(drop=True)


def dry_spells(d: pd.DataFrame, cfg: PrecipConfig) -> pd.DataFrame:
    is_dry = d[cfg.prcp_col] < cfg.wet_day_mm
    run_id = _runs(is_dry, d["date"])
    spells = []
    for _, g in d[is_dry].groupby(run_id):
        if len(g) < cfg.min_dry_spell_days:
            continue
        spells.append(
            {
                "event_type": "dry_spell",
                "start_date": g["date"].min(),
                "end_date": g["date"].max(),
                "duration_days": int(len(g)),
                "year": int(g["year"].iloc[0]),
            }
        )
    out = pd.DataFrame(spells)
    if out.empty:
        return out
    return out.sort_values("duration_days", ascending=False).reset_index(drop=True)


def compute_precip_tables(df_daily: pd.DataFrame, cfg: PrecipConfig | None = None):
    """df_daily must already have date/year/doy fields (temperature.add_time_fields)."""
    cfg = cfg or PrecipConfig()
    d = df_daily.copy()
    d[cfg.prcp_col] = pd.to_numeric(d[cfg.prcp_col], errors="coerce")
    d[cfg.gust_col] = pd.to_numeric(d[cfg.gust_col], errors="coerce")
    return {
        "extreme_rain_days": extreme_rain_days(d, cfg),
        "rain_events": rain_events(d, cfg),
        "high_wind_days": high_wind_days(d, cfg),
        "dry_spells": dry_spells(d, cfg),
    }
