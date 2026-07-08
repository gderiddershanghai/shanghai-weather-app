# pipeline/fetch/aqi_feed.py
# Two modes:
#   daily append : WAQI city feed (current day only) -> appends one row
#                    python3 -m pipeline.fetch.aqi_feed        (needs $WAQI_TOKEN)
#   backfill     : merge a manually downloaded aqicn.org data-platform CSV
#                    python3 -m pipeline.fetch.aqi_feed --import-csv path/to/export.csv
#
# CSV schema (aqicn.org export format, kept as-is):
#   date, pm25, pm10, o3, no2, so2, co     (date yyyy/m/d, values are US-EPA IAQI)

from __future__ import annotations

import argparse
import os
import sys
from datetime import date

import pandas as pd
import requests

from ..config import AQI_CSV

POLLUTANTS = ["pm25", "pm10", "o3", "no2", "so2", "co"]
FEED_URL = "https://api.waqi.info/feed/shanghai/"


def load_csv() -> pd.DataFrame:
    df = pd.read_csv(AQI_CSV)
    df.columns = [c.strip() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"].astype(str).str.strip(), format="mixed")
    for col in POLLUTANTS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)


def save_csv(df: pd.DataFrame) -> None:
    out = df.copy()
    out["date"] = out["date"].dt.strftime("%Y/%-m/%-d")
    out.to_csv(AQI_CSV, index=False)


def fetch_today() -> dict | None:
    token = os.environ.get("WAQI_TOKEN")
    if not token:
        print("WAQI_TOKEN not set — skipping AQI fetch", file=sys.stderr)
        return None
    resp = requests.get(FEED_URL, params={"token": token}, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("status") != "ok":
        raise RuntimeError(f"WAQI feed error: {payload}")
    iaqi = payload["data"].get("iaqi", {})
    row: dict = {"date": pd.Timestamp(date.today())}
    for p in POLLUTANTS:
        v = iaqi.get(p, {}).get("v")
        row[p] = float(v) if v is not None else None
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description="Append/merge Shanghai AQI data")
    parser.add_argument("--import-csv", help="merge an aqicn.org data-platform CSV export")
    args = parser.parse_args()

    df = load_csv()

    if args.import_csv:
        imported = pd.read_csv(args.import_csv)
        imported.columns = [c.strip() for c in imported.columns]
        imported["date"] = pd.to_datetime(imported["date"].astype(str).str.strip(), format="mixed")
        for col in POLLUTANTS:
            if col in imported.columns:
                imported[col] = pd.to_numeric(imported[col], errors="coerce")
        merged = (
            pd.concat([df, imported[["date", *POLLUTANTS]]], ignore_index=True)
            .sort_values("date")
            .drop_duplicates("date", keep="last")  # imported values win
            .reset_index(drop=True)
        )
        added = len(merged) - len(df)
        save_csv(merged)
        print(f"merged {args.import_csv}: {added} new rows; now {merged['date'].min().date()} -> {merged['date'].max().date()}")
        return 0

    row = fetch_today()
    if row is None:
        return 0
    if (df["date"] == row["date"]).any():
        print(f"{row['date'].date()} already present — nothing to do")
        return 0
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True).sort_values("date").reset_index(drop=True)
    save_csv(df)
    print(f"appended {row['date'].date()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
