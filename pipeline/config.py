# pipeline/config.py
# Single place for paths, station coordinates, API details and thresholds.

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DERIVED_DIR = ROOT / "static" / "data" / "derived"
EVENT_IMAGES_DIR = DERIVED_DIR / "event-images"

WEATHER_CSV = DATA_DIR / "weather_shanghai.csv"
AQI_CSV = DATA_DIR / "aqi_shanghai.csv"
EVENTS_CSV = DATA_DIR / "events.csv"

# Downtown Shanghai (Xuhui) — matches the coordinates the historical data was fetched with.
LATITUDE = 31.1667
LONGITUDE = 121.4333
TIMEZONE = "Asia/Shanghai"

OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
# ERA5 archive lags realtime by ~5 days; never request closer than this.
ARCHIVE_LAG_DAYS = 6

# Canonical daily variables (order matters — it defines the CSV schema).
# uv_index_max is deliberately excluded: 100% NaN across 1980-2025.
# humidity_2m_mean is excluded: unavailable before 1984.
OPEN_METEO_DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "precipitation_hours",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "sunshine_duration",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "wind_speed_10m_mean",
]

# Compact daily.json schema: JSON column name -> CSV column name.
# The JS mirror lives in src/lib/data/daily.ts (COL enum); build_derived embeds
# the column list in the JSON and the frontend asserts against it at load time.
DAILY_COMPACT_COLUMNS: dict[str, str] = {
    "date": "time",  # emitted as yyyymmdd int
    "tmax": "temperature_2m_max",
    "tmin": "temperature_2m_min",
    "tmean": "temperature_2m_mean",
    "prcp": "precipitation_sum",
    "prcp_h": "precipitation_hours",
    "atmax": "apparent_temperature_max",
    "atmin": "apparent_temperature_min",
    "sun_h": "sunshine_duration",  # emitted in hours, not seconds
    "wmax": "wind_speed_10m_max",
    "gmax": "wind_gusts_10m_max",
    "wmean": "wind_speed_10m_mean",
}

VALID_EVENT_CATEGORIES = {"HOT", "COLD", "RAIN", "TYPHOON", "AQI"}
