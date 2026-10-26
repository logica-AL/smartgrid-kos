"""Audit and prepare the supplied London half-hourly household dataset."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

RAW_COLUMNS = ["LCLid", "stdorToU", "DateTime", "KWH/hh (per half hour)"]
NORMAL_COLUMNS = ["LCLid", "stdorToU", "DateTime", "KWH/hh (per half hour)"]


def read_meter_file(path: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read all local observations, retaining a report of raw/normalized names."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV meter tidak ditemukan: {path}")
    original_columns = list(pd.read_csv(path, nrows=0).columns)
    normalized = [str(c).strip() for c in original_columns]
    if normalized != NORMAL_COLUMNS:
        raise ValueError(f"Skema CSV tidak cocok. Header mentah={original_columns}; setelah strip={normalized}; diharapkan={NORMAL_COLUMNS}")
    df = pd.read_csv(path, skipinitialspace=True, low_memory=False)
    df.columns = df.columns.str.strip()
    if list(df.columns) != NORMAL_COLUMNS:
        raise ValueError(f"Skema setelah normalisasi tidak cocok: {list(df.columns)}")
    raw_rows = int(len(df))
    energy_col = "KWH/hh (per half hour)"
    energy = pd.to_numeric(df[energy_col], errors="coerce")
    ts = pd.to_datetime(df["DateTime"], errors="coerce")
    out = pd.DataFrame({
        "LCLid": df["LCLid"].astype("string").str.strip(),
        "stdorToU": df["stdorToU"].astype("string").str.strip(),
        "timestamp": ts,
        "energy_kwh": energy.astype("float64"),
    })
    invalid_ts = int(out.timestamp.isna().sum())
    invalid_energy = int(out.energy_kwh.isna().sum())
    zero_energy_before_dedup = int(out.energy_kwh.eq(0).sum())
    negative_energy = int(out.energy_kwh.lt(0).sum())
    duplicate_key = out.duplicated(["LCLid", "timestamp"], keep="first")
    duplicates = int(duplicate_key.sum())
    clean = out.dropna(subset=["LCLid", "timestamp"]).loc[~duplicate_key].copy()
    clean = clean.sort_values(["LCLid", "timestamp"], kind="mergesort").reset_index(drop=True)
    zero_energy_after_dedup = int(clean.energy_kwh.eq(0).sum())
    # Keep missing/bad energy as NaN; it is never imputed to zero.
    intervals = clean.groupby("LCLid", sort=False)["timestamp"].diff().dropna()
    audit = {
        "source_file": path.name if path.is_absolute() else str(path), "file_size_bytes": path.stat().st_size,
        "raw_column_names": original_columns, "normalized_column_names": normalized,
        "rows_before_cleaning": raw_rows, "invalid_timestamp_rows": invalid_ts,
        "energy_missing_or_invalid_rows": invalid_energy,
        "valid_zero_energy_rows_before_deduplication": zero_energy_before_dedup,
        "valid_zero_energy_rows": zero_energy_after_dedup,
        "negative_energy_rows": negative_energy, "duplicate_household_timestamp_rows_removed": duplicates,
        "rows_after_timestamp_and_duplicate_cleaning": int(len(clean)),
        "rows_with_valid_numeric_energy_after_cleaning": int(clean.energy_kwh.notna().sum()),
        "unique_households": int(clean.LCLid.nunique()),
        "customer_categories": {str(k): int(v) for k, v in clean.stdorToU.value_counts(dropna=False).items()},
        "timestamp_min": clean.timestamp.min().isoformat() if len(clean) else None,
        "timestamp_max": clean.timestamp.max().isoformat() if len(clean) else None,
        "rows_with_valid_timestamp": int(clean.timestamp.notna().sum()),
        "interval_counts_minutes": {str(k): int(v) for k, v in (intervals.dt.total_seconds().div(60).value_counts().sort_index().items())},
        "interval_30_minutes_count": int(intervals.eq(pd.Timedelta(minutes=30)).sum()),
        "interval_other_than_30_minutes_count": int((intervals != pd.Timedelta(minutes=30)).sum()),
        "zero_values_are_retained": True, "missing_energy_fill_policy": "No fill; blank and non-numeric readings remain NaN and affected features/targets are excluded.",
        "duplicate_policy": "For duplicate (LCLid, timestamp) rows, retain the first record in source order; record removed count.",
        "timestamp_policy": "Parse naive source timestamps; validate target alignment using actual timestamp differences; do not synthesize DST intervals.",
    }
    return clean, audit


def audit_tariffs(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Workbook tarif tidak ditemukan: {path}")
    xls = pd.ExcelFile(path)
    sheets = {}
    for sheet in xls.sheet_names:
        frame = pd.read_excel(path, sheet_name=sheet)
        item: dict[str, Any] = {"rows": int(len(frame)), "columns": [str(c) for c in frame.columns]}
        if len(frame):
            if "TariffDateTime" in frame:
                stamps = pd.to_datetime(frame["TariffDateTime"], errors="coerce")
                item["timestamp_min"] = stamps.min().isoformat() if stamps.notna().any() else None
                item["timestamp_max"] = stamps.max().isoformat() if stamps.notna().any() else None
                item["invalid_timestamps"] = int(stamps.isna().sum())
            if "Tariff" in frame:
                item["categories"] = {str(k): int(v) for k, v in frame["Tariff"].value_counts(dropna=False).items()}
            item["missing_by_column"] = {str(k): int(v) for k, v in frame.isna().sum().items()}
        sheets[sheet] = item
    return {"source_file": path.name if path.is_absolute() else str(path), "file_size_bytes": path.stat().st_size, "sheet_names": xls.sheet_names,
            "sheets": sheets, "monetary_rate_present": False,
            "join_decision": "Not joined to the local sample: it contains only Std customers, while workbook labels describe dynamic ToU periods in 2013."}


def write_json(path: str | Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
