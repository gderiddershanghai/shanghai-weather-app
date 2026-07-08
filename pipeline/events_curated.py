# pipeline/events_curated.py
# data/events.csv -> events-curated.json: the bilingual annotation layer
# (curated extreme-weather events with news citations) used by hover cards.

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .config import EVENT_IMAGES_DIR, EVENTS_CSV, VALID_EVENT_CATEGORIES

_TBD = re.compile(r"^\s*\(?tbd\)?\s*$", re.IGNORECASE)


def _clean_cell(value) -> str | None:
    """Empty / '(TBD)' / non-string -> None; otherwise stripped string."""
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s or _TBD.match(s):
        return None
    return s


def _clean_url(value) -> str | None:
    """Only accept things that are actually URLs (one known row has headline text here)."""
    s = _clean_cell(value)
    if s is None or not s.startswith("http"):
        return None
    return s


def _parse_date(value) -> pd.Timestamp:
    # events.csv uses dd/mm/yyyy
    return pd.to_datetime(value, dayfirst=True)


def _links(row: pd.Series, prefix: str) -> dict | None:
    outlet = _clean_cell(row.get(f"{prefix}_outlet"))
    headline = _clean_cell(row.get(f"{prefix}_headline"))
    url = _clean_url(row.get(f"{prefix}_url"))
    if not (outlet or headline or url):
        return None
    return {"outlet": outlet, "headline": headline, "url": url}


def load_curated_events(csv_path: Path = EVENTS_CSV) -> list[dict]:
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    # drop trailing unnamed export artifact columns
    df = df.loc[:, [c for c in df.columns if not c.lower().startswith("unnamed")]]

    events: list[dict] = []
    for _, row in df.iterrows():
        category = _clean_cell(row.get("category"))
        if category is None:
            continue
        category = category.upper()
        if category not in VALID_EVENT_CATEGORIES:
            raise ValueError(f"events.csv: unknown category {category!r} (row {row.to_dict()})")

        date = _parse_date(row["date"])
        start = _parse_date(row["period_start"]) if _clean_cell(row.get("period_start")) else date
        end = _parse_date(row["period_end"]) if _clean_cell(row.get("period_end")) else date
        slug = f"{category.lower()}-{date.strftime('%Y-%m-%d')}"

        image_rel = None
        for ext in ("jpg", "png", "webp"):
            if (EVENT_IMAGES_DIR / f"{slug}.{ext}").exists():
                image_rel = f"event-images/{slug}.{ext}"
                break

        note_en = _clean_cell(row.get("note"))
        note_zh = _clean_cell(row.get("zh_note"))  # column added in the content pass

        events.append(
            {
                "id": slug,
                "category": category,
                "date": date.strftime("%Y-%m-%d"),
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d"),
                "days": int(row["duration_days"]) if pd.notna(row.get("duration_days")) else max((end - date).days + 1, 1),
                "doy": min(int(date.dayofyear), 365),
                "year": int(date.year),
                "real_c": float(row["real_temp_c"]) if pd.notna(row.get("real_temp_c")) else None,
                "feels_c": float(row["feels_like_c"]) if pd.notna(row.get("feels_like_c")) else None,
                "note": {"en": note_en, "zh": note_zh or note_en},
                "links": {"en": _links(row, "en"), "zh": _links(row, "zh")},
                "image": image_rel,
            }
        )

    events.sort(key=lambda e: e["date"])
    ids = [e["id"] for e in events]
    if len(ids) != len(set(ids)):
        dupes = {i for i in ids if ids.count(i) > 1}
        raise ValueError(f"events.csv: duplicate event ids {dupes}")
    return events
