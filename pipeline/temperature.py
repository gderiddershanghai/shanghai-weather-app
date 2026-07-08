# pipeline/temperature.py
# Moved verbatim from src/analysis_py/temperature_datasets.py.
# DOY climatology (quantiles + circular smoothing), anomalies, outlier days,
# and multi-day heat/cold wave detection for real and feels-like temperature.

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd


TempMode = Literal["real", "feels_like"]
Tail = Literal["hot", "cold"]


@dataclass(frozen=True)
class TempConfig:
    date_col: str = "time"

    # real temperature
    tmax_col: str = "temperature_2m_max"
    tmin_col: str = "temperature_2m_min"

    # feels-like / apparent temperature
    atmax_col: str = "apparent_temperature_max"
    atmin_col: str = "apparent_temperature_min"

    # climatology quantiles (DOY)
    hot_qs: Tuple[float, ...] = (0.50, 0.95, 0.99)
    cold_qs: Tuple[float, ...] = (0.50, 0.05, 0.01)

    # event definitions (DOY-adjusted)
    heat_q: float = 0.99
    cold_q: float = 0.01
    min_event_days: int = 3

    # smoothing
    smooth_window_days: int = 15

    # leap day handling
    # "map_to_feb28" keeps DOY stats stable and avoids introducing DOY=60 in some years only
    leapday_policy: Literal["map_to_feb28", "drop"] = "map_to_feb28"


# ----------------------------
# Core utilities
# ----------------------------
def _ensure_datetime(d: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_datetime(d[col], errors="raise")


def add_time_fields(df: pd.DataFrame, cfg: TempConfig) -> pd.DataFrame:
    d = df.copy()
    d[cfg.date_col] = _ensure_datetime(d, cfg.date_col)
    d = d.sort_values(cfg.date_col).reset_index(drop=True)

    d["date"] = d[cfg.date_col].dt.floor("D")
    d["year"] = d["date"].dt.year
    d["month"] = d["date"].dt.month
    d["day"] = d["date"].dt.day
    d["doy"] = d["date"].dt.dayofyear

    if cfg.leapday_policy == "map_to_feb28":
        is_leap_day = (d["month"] == 2) & (d["day"] == 29)
        # Feb 28 DOY is 59 for non-leap years
        d.loc[is_leap_day, "doy"] = 59
    elif cfg.leapday_policy == "drop":
        d = d[~((d["month"] == 2) & (d["day"] == 29))].copy()

    return d


def _to_numeric_inplace(d: pd.DataFrame, cols: List[str]) -> None:
    for c in cols:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")


def doy_quantiles(df: pd.DataFrame, value_col: str, qs: Tuple[float, ...]) -> pd.DataFrame:
    g = df.groupby("doy")[value_col]
    out = g.quantile(list(qs)).unstack(level=-1)
    out.columns = [f"q{int(q*100):02d}" for q in qs]
    return out.reset_index()


def circular_rolling(series: pd.Series, window: int) -> pd.Series:
    x = series.to_numpy()
    pad = window // 2
    xpad = np.r_[x[-pad:], x, x[:pad]]
    sm = pd.Series(xpad).rolling(window, center=True, min_periods=1).mean().to_numpy()
    sm = sm[pad:-pad]
    return pd.Series(sm, index=series.index)


def add_climatology_calendar(df_clim: pd.DataFrame, ref_year: int = 2001) -> pd.DataFrame:
    """
    Adds a reference date for plotting DOY-based climatology.
    This is NOT the year the values occurred; it's a stable x-axis anchor.
    """
    d = df_clim.copy()
    ref_dates = pd.to_datetime(d["doy"].astype(int), format="%j", errors="raise").map(
        lambda x: x.replace(year=ref_year)
    )
    d["date_ref"] = ref_dates
    d["month_ref"] = d["date_ref"].dt.month
    d["day_ref"] = d["date_ref"].dt.day
    return d


# ----------------------------
# Climatology builder (real + feels-like)
# ----------------------------
def build_temperature_climatology(df_daily: pd.DataFrame, cfg: TempConfig) -> pd.DataFrame:
    """
    Output: one row per DOY with quantiles and smoothed quantiles for:
      - real tmax/tmin
      - feels-like atmax/atmin
    """
    d = df_daily.copy()

    # Build per-mode quantiles (using the same naming pattern so downstream stays simple)
    def _build_for(mode: TempMode) -> pd.DataFrame:
        if mode == "real":
            max_col, min_col = cfg.tmax_col, cfg.tmin_col
            prefix_max, prefix_min = "tmax", "tmin"
        else:
            max_col, min_col = cfg.atmax_col, cfg.atmin_col
            prefix_max, prefix_min = "atmax", "atmin"

        q_max = doy_quantiles(d, max_col, cfg.hot_qs)
        q_min = doy_quantiles(d, min_col, cfg.cold_qs)

        # rename quantiles to stable names
        q_max = q_max.rename(
            columns={
                "q50": f"{prefix_max}_p50",
                "q95": f"{prefix_max}_p95",
                "q99": f"{prefix_max}_p99",
            }
        )
        q_min = q_min.rename(
            columns={
                "q50": f"{prefix_min}_p50",
                "q05": f"{prefix_min}_p05",
                "q01": f"{prefix_min}_p01",
            }
        )

        out = q_max.merge(q_min, on="doy", how="outer").sort_values("doy").reset_index(drop=True)

        # smooth selected columns for nicer envelopes
        idx = out.set_index("doy")
        smooth_cols = [
            f"{prefix_max}_p50", f"{prefix_max}_p95", f"{prefix_max}_p99",
            f"{prefix_min}_p50", f"{prefix_min}_p05", f"{prefix_min}_p01",
        ]
        for c in smooth_cols:
            if c in idx.columns:
                idx[f"{c}_sm{cfg.smooth_window_days}"] = circular_rolling(idx[c], cfg.smooth_window_days)

        out = idx.reset_index()

        # add spreads on climatology (tail widths)
        # hot tail: p99 - p50
        out[f"{prefix_max}_spread_p99_p50"] = out[f"{prefix_max}_p99"] - out[f"{prefix_max}_p50"]
        if f"{prefix_max}_p99_sm{cfg.smooth_window_days}" in out.columns and f"{prefix_max}_p50_sm{cfg.smooth_window_days}" in out.columns:
            out[f"{prefix_max}_spread_p99_p50_sm{cfg.smooth_window_days}"] = (
                out[f"{prefix_max}_p99_sm{cfg.smooth_window_days}"] - out[f"{prefix_max}_p50_sm{cfg.smooth_window_days}"]
            )

        # cold tail depth: p50 - p01 (positive magnitude)
        out[f"{prefix_min}_spread_p50_p01"] = out[f"{prefix_min}_p50"] - out[f"{prefix_min}_p01"]
        if f"{prefix_min}_p01_sm{cfg.smooth_window_days}" in out.columns and f"{prefix_min}_p50_sm{cfg.smooth_window_days}" in out.columns:
            out[f"{prefix_min}_spread_p50_p01_sm{cfg.smooth_window_days}"] = (
                out[f"{prefix_min}_p50_sm{cfg.smooth_window_days}"] - out[f"{prefix_min}_p01_sm{cfg.smooth_window_days}"]
            )

        return out

    clim_real = _build_for("real")
    clim_feels = _build_for("feels_like")

    # merge on DOY, keep both sets of columns
    df_clim = clim_real.merge(clim_feels, on="doy", how="outer").sort_values("doy").reset_index(drop=True)
    df_clim = add_climatology_calendar(df_clim, ref_year=2001)
    return df_clim


# ----------------------------
# Daily enrichment (anomalies + thresholds)
# ----------------------------
def attach_temperature_climatology(df_daily: pd.DataFrame, df_clim: pd.DataFrame, cfg: TempConfig) -> pd.DataFrame:
    """
    Adds:
      - DOY baselines (p50) and thresholds (p95/p99, p05/p01)
      - anomalies vs DOY p50 (this is your sorting metric)
    for both real and feels-like.
    """
    d = df_daily.merge(df_clim, on="doy", how="left")

    W = cfg.smooth_window_days

    def _pick(sm: str, raw: str) -> pd.Series:
        return d[sm] if sm in d.columns else d[raw]

    # REAL
    d["real_hot_base"] = _pick(f"tmax_p50_sm{W}", "tmax_p50")
    d["real_cold_base"] = _pick(f"tmin_p50_sm{W}", "tmin_p50")
    d["real_hot_anom"] = d[cfg.tmax_col] - d["real_hot_base"]          # value - median(doy)
    d["real_cold_anom"] = d["real_cold_base"] - d[cfg.tmin_col]        # median(doy) - value

    d["real_hot_thr_p99"] = _pick(f"tmax_p99_sm{W}", "tmax_p99")
    d["real_hot_thr_p95"] = _pick(f"tmax_p95_sm{W}", "tmax_p95")
    d["real_cold_thr_p01"] = _pick(f"tmin_p01_sm{W}", "tmin_p01")
    d["real_cold_thr_p05"] = _pick(f"tmin_p05_sm{W}", "tmin_p05")

    # FEELS-LIKE
    d["feel_hot_base"] = _pick(f"atmax_p50_sm{W}", "atmax_p50")
    d["feel_cold_base"] = _pick(f"atmin_p50_sm{W}", "atmin_p50")
    d["feel_hot_anom"] = d[cfg.atmax_col] - d["feel_hot_base"]
    d["feel_cold_anom"] = d["feel_cold_base"] - d[cfg.atmin_col]

    d["feel_hot_thr_p99"] = _pick(f"atmax_p99_sm{W}", "atmax_p99")
    d["feel_hot_thr_p95"] = _pick(f"atmax_p95_sm{W}", "atmax_p95")
    d["feel_cold_thr_p01"] = _pick(f"atmin_p01_sm{W}", "atmin_p01")
    d["feel_cold_thr_p05"] = _pick(f"atmin_p05_sm{W}", "atmin_p05")

    return d


# ----------------------------
# Outlier days (single-day)
# ----------------------------
def build_temperature_outlier_days(df_enriched: pd.DataFrame, cfg: TempConfig, use_threshold: str = "p99") -> pd.DataFrame:
    """
    One row per outlier "fact" (hot/cold), for real + feels-like.

    Ranking metric (severity_score):
      - hot:  value - median(doy)  (anom)
      - cold: median(doy) - value  (anom)

    `use_threshold` controls the filter:
      - "p99" (default): only show truly extreme days
      - "p95": broader
      - "none": no threshold filter (then "Top N" becomes purely anomaly-based)
    """
    d = df_enriched.copy()
    rows = []

    def _add(mode: TempMode, tail: Tail):
        if mode == "real":
            if tail == "hot":
                value_col = cfg.tmax_col
                anom_col = "real_hot_anom"
                thr_col = f"real_hot_thr_{use_threshold}" if use_threshold in ("p95", "p99") else None
                label = "real_hot"
            else:
                value_col = cfg.tmin_col
                anom_col = "real_cold_anom"
                thr_col = f"real_cold_thr_{'p01' if use_threshold=='p99' else 'p05'}" if use_threshold in ("p95", "p99") else None
                label = "real_cold"
        else:
            if tail == "hot":
                value_col = cfg.atmax_col
                anom_col = "feel_hot_anom"
                thr_col = f"feel_hot_thr_{use_threshold}" if use_threshold in ("p95", "p99") else None
                label = "feel_hot"
            else:
                value_col = cfg.atmin_col
                anom_col = "feel_cold_anom"
                thr_col = f"feel_cold_thr_{'p01' if use_threshold=='p99' else 'p05'}" if use_threshold in ("p95", "p99") else None
                label = "feel_cold"

        sub = d.copy()
        if thr_col is not None:
            if tail == "hot":
                sub = sub[sub[value_col] > sub[thr_col]]
            else:
                sub = sub[sub[value_col] < sub[thr_col]]

        if sub.empty:
            return

        out = sub[["date", "year", "month", "day", "doy"]].copy()
        out["mode"] = mode
        out["tail"] = tail
        out["series"] = label
        out["value"] = sub[value_col].astype(float)
        out["severity_score"] = sub[anom_col].astype(float)  # higher = more extreme (for both hot and cold)
        out["baseline_p50"] = (sub["real_hot_base"] if label == "real_hot" else
                               sub["real_cold_base"] if label == "real_cold" else
                               sub["feel_hot_base"] if label == "feel_hot" else
                               sub["feel_cold_base"]).astype(float)
        rows.append(out)

    for m in ("real", "feels_like"):
        _add(m, "hot")
        _add(m, "cold")

    if not rows:
        return pd.DataFrame(columns=[
            "date","year","month","day","doy","mode","tail","series","value","severity_score","baseline_p50"
        ])

    out = pd.concat(rows, ignore_index=True)
    out = out.sort_values(["mode", "tail", "severity_score"], ascending=[True, True, False]).reset_index(drop=True)
    return out


# ----------------------------
# Heat/cold waves (multi-day events)
# ----------------------------
def _runs_to_events(
    df: pd.DataFrame,
    condition_col: str,
    value_col: str,
    severity_col: str,
    event_type: str,
    min_days: int,
) -> pd.DataFrame:
    d = df[["date", "year", "doy", value_col, severity_col, condition_col]].copy()
    d = d.sort_values("date").reset_index(drop=True)

    date_gap = d["date"].diff().dt.days.fillna(1).ne(1)
    run_break = (~d[condition_col].fillna(False)) | date_gap
    run_id = run_break.cumsum()

    events = []
    true_days = d[d[condition_col].fillna(False)]
    for _, g in true_days.groupby(run_id):
        if len(g) < min_days:
            continue

        # Peak severity within event (max severity_score always)
        peak_idx = g[severity_col].idxmax()
        peak = d.loc[peak_idx]

        events.append({
            "event_type": event_type,
            "start_date": g["date"].min(),
            "end_date": g["date"].max(),
            "duration_days": int(len(g)),
            "peak_date": peak["date"],
            "peak_value": float(peak[value_col]),
            "peak_severity": float(peak[severity_col]),  # primary sort
            "year": int(g["year"].iloc[0]),
        })

    out = pd.DataFrame(events)
    if out.empty:
        return out

    return out.sort_values(["peak_severity", "duration_days"], ascending=[False, False]).reset_index(drop=True)


def build_temperature_events(df_enriched: pd.DataFrame, df_clim: pd.DataFrame, cfg: TempConfig) -> pd.DataFrame:
    """
    Builds heat/cold waves for both real + feels-like, using DOY-adjusted thresholds:
      heat day: value > p{heat_q}(doy)
      cold day: value < p{cold_q}(doy)

    Event severity is your chosen story metric:
      peak of (value - median(doy)) for heat
      peak of (median(doy) - value) for cold
    """
    d = df_enriched.copy()

    # We need p{heat_q}/p{cold_q} thresholds by DOY; compute them from daily data quickly by DOY.
    # Keep this local to avoid overcomplicating df_clim schema.
    def _doy_thr(value_col: str, q: float, name: str) -> pd.DataFrame:
        thr = d.groupby("doy")[value_col].quantile(q).reset_index().rename(columns={value_col: name})
        return thr

    # REAL thresholds
    thr_real_heat = _doy_thr(cfg.tmax_col, cfg.heat_q, "real_heat_thr")
    thr_real_cold = _doy_thr(cfg.tmin_col, cfg.cold_q, "real_cold_thr")

    # FEELS thresholds
    thr_feel_heat = _doy_thr(cfg.atmax_col, cfg.heat_q, "feel_heat_thr")
    thr_feel_cold = _doy_thr(cfg.atmin_col, cfg.cold_q, "feel_cold_thr")

    d = d.merge(thr_real_heat, on="doy", how="left").merge(thr_real_cold, on="doy", how="left")
    d = d.merge(thr_feel_heat, on="doy", how="left").merge(thr_feel_cold, on="doy", how="left")

    d["real_is_heat_day"] = d[cfg.tmax_col] > d["real_heat_thr"]
    d["real_is_cold_day"] = d[cfg.tmin_col] < d["real_cold_thr"]
    d["feel_is_heat_day"] = d[cfg.atmax_col] > d["feel_heat_thr"]
    d["feel_is_cold_day"] = d[cfg.atmin_col] < d["feel_cold_thr"]

    # Build events
    real_heat = _runs_to_events(
        d, "real_is_heat_day", cfg.tmax_col, "real_hot_anom",
        event_type="real_heat_wave", min_days=cfg.min_event_days
    )
    real_cold = _runs_to_events(
        d, "real_is_cold_day", cfg.tmin_col, "real_cold_anom",
        event_type="real_cold_wave", min_days=cfg.min_event_days
    )
    feel_heat = _runs_to_events(
        d, "feel_is_heat_day", cfg.atmax_col, "feel_hot_anom",
        event_type="feel_heat_wave", min_days=cfg.min_event_days
    )
    feel_cold = _runs_to_events(
        d, "feel_is_cold_day", cfg.atmin_col, "feel_cold_anom",
        event_type="feel_cold_wave", min_days=cfg.min_event_days
    )

    out = pd.concat([real_heat, real_cold, feel_heat, feel_cold], ignore_index=True)
    if out.empty:
        return out

    # stable sort for explore: strongest first
    out = out.sort_values(["event_type", "peak_severity", "duration_days"], ascending=[True, False, False]).reset_index(drop=True)
    return out


# ----------------------------
# One-call pipeline (temperature-focused)
# ----------------------------
def compute_temperature_tables(df_raw: pd.DataFrame, cfg: Optional[TempConfig] = None):
    """
    Returns:
      df_daily:     daily base with time fields
      df_clim:      DOY climatology for real + feels-like (with smoothed columns + spreads + date_ref)
      df_enriched:  daily + baselines + anomalies + thresholds
      df_outliers:  single-day outliers (rankable by severity_score)
      df_events:    heat/cold waves (rankable by peak_severity, duration)
    """
    cfg = cfg or TempConfig()

    df_daily = add_time_fields(df_raw, cfg)
    _to_numeric_inplace(df_daily, [cfg.tmax_col, cfg.tmin_col, cfg.atmax_col, cfg.atmin_col])

    df_clim = build_temperature_climatology(df_daily, cfg)
    df_enriched = attach_temperature_climatology(df_daily, df_clim, cfg)

    df_outliers = build_temperature_outlier_days(df_enriched, cfg, use_threshold="p99")
    df_events = build_temperature_events(df_enriched, df_clim, cfg)

    return df_daily, df_clim, df_enriched, df_outliers, df_events
