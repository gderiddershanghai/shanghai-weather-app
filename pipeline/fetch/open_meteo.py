# pipeline/fetch/open_meteo.py
# Idempotent daily-weather appender. Fetches from the last date in the CSV up
# to today-ARCHIVE_LAG_DAYS (ERA5 archive lag) and appends new rows.
# The same code path performs the initial backfill (e.g. Jan->Jul 2026 gap).
#
#   python3 -m pipeline.fetch.open_meteo

from __future__ import annotations

import sys
from datetime import date, timedelta

import pandas as pd
import requests

from ..config import (
    ARCHIVE_LAG_DAYS,
    LATITUDE,
    LONGITUDE,
    OPEN_METEO_DAILY_VARS,
    OPEN_METEO_URL,
    TIMEZONE,
    WEATHER_CSV,
)


def load_csv() -> pd.DataFrame:
    df = pd.read_csv(WEATHER_CSV)
    # normalize legacy export artifacts once; the rewrite below makes it permanent
    df = df.loc[:, [c for c in df.columns if not c.lower().startswith("unnamed")]]
    df = df.drop(columns=[c for c in ("uv_index_max",) if c in df.columns])
    df["time"] = pd.to_datetime(df["time"])
    return df.sort_values("time").drop_duplicates("time").reset_index(drop=True)


def fetch_range(start: date, end: date) -> pd.DataFrame:
    resp = requests.get(
        OPEN_METEO_URL,
        params={
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "daily": ",".join(OPEN_METEO_DAILY_VARS),
            "timezone": TIMEZONE,
        },
        timeout=60,
    )
    resp.raise_for_status()
    daily = resp.json()["daily"]
    df = pd.DataFrame(daily)
    df["time"] = pd.to_datetime(df["time"])
    return df


def main() -> int:
    df = load_csv()
    last = df["time"].max().date()
    start = last + timedelta(days=1)
    end = date.today() - timedelta(days=ARCHIVE_LAG_DAYS)

    if start > end:
        print(f"no new data: CSV ends {last}, archive horizon is {end}")
        # still rewrite once so schema normalization (index col, uv) persists
        df.to_csv(WEATHER_CSV, index=False, date_format="%Y-%m-%d")
        return 0

    print(f"fetching {start} -> {end} …")
    new = fetch_range(start, end)

    # Drop trailing rows where the archive has no temperatures yet (all-null)
    new = new.dropna(subset=["temperature_2m_max", "temperature_2m_min"], how="all")
    if new.empty:
        print("archive returned no usable rows yet")
        return 0

    merged = (
        pd.concat([df, new], ignore_index=True)
        .sort_values("time")
        .drop_duplicates("time", keep="last")
        .reset_index(drop=True)
    )
    added = len(merged) - len(df)
    merged.to_csv(WEATHER_CSV, index=False, date_format="%Y-%m-%d")
    print(f"appended {added} rows; CSV now ends {merged['time'].max().date()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
