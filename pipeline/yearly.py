# pipeline/yearly.py
# Per-year aggregates for the trend views: warming stripes (annual tmean
# anomaly), seasonal means (JJA highs / DJF lows), threshold-day counts,
# rain totals, peak gusts, PM2.5 medians — plus 10-yr centered rolling means
# so the frontend never re-derives a statistic.

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class YearlyConfig:
    baseline_years: tuple[int, int] = (1980, 2009)  # anomaly reference period
    min_annual_days: int = 360   # else annual stats -> null (partial year)
    min_season_days: int = 85    # JJA has 92 days, DJF 90/91
    min_pm25_days: int = 300     # else pm25 median -> null
    smooth_years: int = 10       # centered rolling window for trend lines
    hot_day_c: float = 35.0      # CMA high-temperature warning threshold
    ice_day_c: float = 0.0


def _roll(s: pd.Series, window: int) -> pd.Series:
    return s.rolling(window, center=True, min_periods=max(3, window // 2)).mean()


def compute_yearly(df_daily: pd.DataFrame, aqi: pd.DataFrame, cfg: YearlyConfig = YearlyConfig()) -> pd.DataFrame:
    d = df_daily.copy()

    annual = (
        d.groupby("year")
        .agg(
            days=("temperature_2m_max", "count"),
            tmean=("temperature_2m_mean", "mean"),
            days_ge_35=("temperature_2m_max", lambda s: int((s >= cfg.hot_day_c).sum())),
            days_le_0=("temperature_2m_min", lambda s: int((s <= cfg.ice_day_c).sum())),
            prcp=("precipitation_sum", "sum"),
            gust_max=("wind_gusts_10m_max", "max"),
        )
        .reset_index()
    )
    partial = annual["days"] < cfg.min_annual_days
    annual.loc[partial, ["tmean", "prcp", "gust_max"]] = np.nan
    annual.loc[partial, ["days_ge_35", "days_le_0"]] = np.nan

    # JJA mean of daily highs
    jja = d[d["month"].isin([6, 7, 8])]
    summer = jja.groupby("year").agg(
        summer_days=("temperature_2m_max", "count"),
        summer_tmax=("temperature_2m_max", "mean"),
    ).reset_index()
    summer.loc[summer["summer_days"] < cfg.min_season_days, "summer_tmax"] = np.nan

    # DJF mean of daily lows, December counted toward the FOLLOWING January's
    # winter (winter "2016" = Dec 2015 + Jan/Feb 2016 — the pipes-burst winter)
    djf = d[d["month"].isin([12, 1, 2])].copy()
    djf["wyear"] = djf["year"] + (djf["month"] == 12).astype(int)
    winter = djf.groupby("wyear").agg(
        winter_days=("temperature_2m_min", "count"),
        winter_tmin=("temperature_2m_min", "mean"),
    ).reset_index().rename(columns={"wyear": "year"})
    winter.loc[winter["winter_days"] < cfg.min_season_days, "winter_tmin"] = np.nan

    am = (
        aqi.groupby("year")
        .agg(pm25_days=("pm25", "count"), pm25_median=("pm25", "median"))
        .reset_index()
    )
    am.loc[am["pm25_days"] < cfg.min_pm25_days, "pm25_median"] = np.nan

    out = (
        annual.merge(summer[["year", "summer_tmax"]], on="year", how="left")
        .merge(winter[["year", "winter_tmin"]], on="year", how="left")
        .merge(am[["year", "pm25_days", "pm25_median"]], on="year", how="left")
        .sort_values("year")
        .reset_index(drop=True)
    )

    lo, hi = cfg.baseline_years
    baseline = out.loc[(out["year"] >= lo) & (out["year"] <= hi), "tmean"].mean()
    out["anom"] = out["tmean"] - baseline

    for col in ("tmean", "summer_tmax", "winter_tmin", "prcp"):
        out[f"{col}_sm"] = _roll(out[col], cfg.smooth_years)

    return out
