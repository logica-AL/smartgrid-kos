"""Create reproducible EDA tables, descriptive insights, and labeled charts."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from data_pipeline import write_json
from figures import draw_energy_histogram, draw_profile

DAY_NAMES = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]


def build_data_insights(meter: pd.DataFrame, audit: dict, output_dir: str | Path) -> dict:
    """Summarize cleaned public observations without imputing or inventing readings."""
    out = Path(output_dir)
    figures = out / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    valid = meter.loc[meter.energy_kwh.notna()].copy()
    valid["hour"] = valid.timestamp.dt.hour
    valid["weekday"] = valid.timestamp.dt.dayofweek
    valid["month"] = valid.timestamp.dt.to_period("M").astype(str)

    hourly = valid.groupby("hour", as_index=False).agg(
        readings=("energy_kwh", "size"), mean_kwh=("energy_kwh", "mean"), median_kwh=("energy_kwh", "median"))
    weekday = valid.groupby("weekday", as_index=False).agg(
        readings=("energy_kwh", "size"), mean_kwh=("energy_kwh", "mean"), median_kwh=("energy_kwh", "median"))
    weekday["weekday_name"] = weekday.weekday.map(dict(enumerate(DAY_NAMES)))
    monthly = valid.groupby("month", as_index=False).agg(
        readings=("energy_kwh", "size"), mean_kwh=("energy_kwh", "mean"), sum_kwh=("energy_kwh", "sum"))
    hourly.to_csv(out / "hourly_profile.csv", index=False)
    weekday.to_csv(out / "weekday_profile.csv", index=False)
    monthly.to_csv(out / "monthly_profile.csv", index=False)

    e = valid.energy_kwh
    stats = {
        "dataset_status": "real_public_sensor_dataset_subset; not synthetic",
        "source_file": Path(audit["source_file"]).name,
        "unit": "kWh per 30-minute interval",
        "rows_analyzed": int(len(meter)),
        "valid_energy_rows": int(len(valid)),
        "missing_or_invalid_energy_rows": int(meter.energy_kwh.isna().sum()),
        "valid_zero_readings": int(e.eq(0).sum()),
        "duplicate_household_timestamps_removed": int(audit["duplicate_household_timestamp_rows_removed"]),
        "households": int(meter.LCLid.nunique()),
        "period": {"start": meter.timestamp.min().isoformat(), "end": meter.timestamp.max().isoformat()},
        "energy_kwh_per_30min": {
            "mean": float(e.mean()), "median": float(e.median()), "std": float(e.std()),
            "p90": float(e.quantile(.90)), "p95": float(e.quantile(.95)), "p99": float(e.quantile(.99)),
            "max": float(e.max()), "sum": float(e.sum())
        },
        "temporal_profiles": {
            "hourly_csv": "outputs/hourly_profile.csv", "weekday_csv": "outputs/weekday_profile.csv",
            "monthly_csv": "outputs/monthly_profile.csv",
            "highest_mean_hour": int(hourly.loc[hourly.mean_kwh.idxmax(), "hour"]),
            "lowest_mean_hour": int(hourly.loc[hourly.mean_kwh.idxmin(), "hour"]),
            "highest_mean_weekday": str(weekday.loc[weekday.mean_kwh.idxmax(), "weekday_name"]),
            "highest_mean_month": str(monthly.loc[monthly.mean_kwh.idxmax(), "month"])
        },
        "interpretation_limits": [
            "The CSV is a supplied one-million-row slice of London data, not the full release and not a Surabaya measurement.",
            "Profiles describe this slice; household coverage and sampling are uneven across time.",
            "Zero readings are valid observations; missing energy is not imputed.",
            "The hourly pattern is descriptive and does not establish a causal effect."
        ]
    }
    write_json(out / "data_insights.json", stats)
    draw_energy_histogram(figures / "energy_distribution.png", e.to_numpy())
    draw_profile(figures / "hourly_profile.png", list(zip(hourly.hour, hourly.mean_kwh)),
                 "Pola konsumsi menurut jam", "Jam lokal pada timestamp sumber")
    draw_profile(figures / "weekday_profile.png", list(zip(weekday.weekday_name, weekday.mean_kwh)),
                 "Pola konsumsi menurut hari", "Hari dalam minggu")
    draw_profile(figures / "monthly_profile.png", list(zip(monthly.month, monthly.mean_kwh)),
                 "Rata-rata energi per bulan", "Bulan pada periode sampel")
    return stats
