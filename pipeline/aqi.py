# pipeline/aqi.py
# AQI derivations from the aqicn.org export (US-EPA IAQI per pollutant):
#   - cleaned daily table
#   - yearly summary/trend (pm25)
#   - day-level join with temperature for the interplay scatter

from __future__ import annotations

import pandas as pd

from .config import AQI_CSV

POLLUTANTS = ["pm25", "pm10", "o3", "no2", "so2", "co"]


def load_aqi() -> pd.DataFrame:
    df = pd.read_csv(AQI_CSV)
    df.columns = [c.strip() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"].astype(str).str.strip(), format="mixed")
    for col in POLLUTANTS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df


def yearly_summary(aqi: pd.DataFrame) -> list[dict]:
    """Per-year pm25 trend stats; coverage flags partial years honestly."""
    rows = []
    for year, g in aqi.groupby("year"):
        pm = g["pm25"].dropna()
        days_in_year = 366 if pd.Timestamp(year=int(year), month=12, day=31).is_leap_year else 365
        rows.append(
            {
                "year": int(year),
                "pm25_median": round(float(pm.median()), 1) if len(pm) else None,
                "pm25_p90": round(float(pm.quantile(0.9)), 1) if len(pm) else None,
                "days_gt_100": int((pm > 100).sum()),
                "days_gt_150": int((pm > 150).sum()),
                "days_le_50": int((pm <= 50).sum()),
                "coverage_pct": round(100 * len(pm) / days_in_year),
            }
        )
    return rows


def _season(month: pd.Series) -> pd.Series:
    """0=DJF 1=MAM 2=JJA 3=SON (matches the frontend Season enum)."""
    return month.map(lambda m: 0 if m in (12, 1, 2) else 1 if m <= 5 else 2 if m <= 8 else 3)


def temp_aqi_join(aqi: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    """Inner join on date; only days where both pm25 and temperature exist."""
    w = weather[["time", "temperature_2m_max", "temperature_2m_min"]].rename(
        columns={"time": "date", "temperature_2m_max": "tmax", "temperature_2m_min": "tmin"}
    )
    j = aqi.merge(w, on="date", how="inner")
    j = j.dropna(subset=["pm25", "tmax"])
    j["season"] = _season(j["date"].dt.month)
    return j[["date", "tmax", "tmin", "pm25", "o3", "season"]].reset_index(drop=True)


def binned_medians(joined: pd.DataFrame, bin_width: int = 2) -> list[dict]:
    """Median pm25/o3 per tmax bin per season — the story-mode summary lines."""
    d = joined.copy()
    d["tbin"] = (d["tmax"] // bin_width) * bin_width
    rows = []
    for (season, tbin), g in d.groupby(["season", "tbin"]):
        if len(g) < 10:  # skip noisy tiny bins
            continue
        rows.append(
            {
                "season": int(season),
                "tmax_bin": float(tbin),
                "n": int(len(g)),
                "pm25_median": round(float(g["pm25"].median()), 1),
                "o3_median": round(float(g["o3"].median()), 1) if g["o3"].notna().any() else None,
            }
        )
    rows.sort(key=lambda r: (r["season"], r["tmax_bin"]))
    return rows
