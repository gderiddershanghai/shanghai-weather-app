# pipeline/emit.py
# JSON serialization helpers: compact output, consistent rounding, NaN -> null.

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd


def _clean(value: Any) -> Any:
    """Convert numpy/pandas scalars to plain JSON-safe Python values."""
    if value is None:
        return None
    if isinstance(value, (np.floating, float)):
        if math.isnan(value) or math.isinf(value):
            return None
        # 2 decimals: enough for temps/mm AND for config quantiles like 0.99
        return round(float(value), 2)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    return value


def clean_deep(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: clean_deep(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean_deep(v) for v in obj]
    return _clean(obj)


def write_json(path: Path, obj: Any) -> int:
    """Write compact JSON; returns byte size."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(clean_deep(obj), ensure_ascii=False, separators=(",", ":"))
    path.write_text(text, encoding="utf-8")
    return len(text.encode("utf-8"))


def series_round(s: pd.Series, decimals: int = 1) -> list:
    """Series -> list of rounded floats with NaN -> None."""
    return [None if pd.isna(v) else round(float(v), decimals) for v in s]


def df_to_compact(df: pd.DataFrame, columns: Sequence[str]) -> dict:
    """DataFrame -> {'columns': [...], 'rows': [[...], ...]} array-of-arrays payload."""
    sub = df[list(columns)]
    rows = [[_clean(v) for v in row] for row in sub.itertuples(index=False, name=None)]
    return {"columns": list(columns), "rows": rows}


def date_to_int(s: pd.Series) -> pd.Series:
    """Datetime series -> yyyymmdd ints (compact, sortable, trivially parsed in JS)."""
    return s.dt.year * 10000 + s.dt.month * 100 + s.dt.day
