"""Panel feature engineering with same-household, exact-next-interval labels."""
from __future__ import annotations

import numpy as np
import pandas as pd


def make_supervised(panel: pd.DataFrame, horizon_minutes: int = 30,
                    lag_intervals: tuple[int, ...] = (1, 2, 4, 48),
                    rolling_windows: tuple[int, ...] = (4, 48)) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Return X, E(t+1), and target timestamps; all features use values through t only."""
    required = {"LCLid", "timestamp", "energy_kwh"}
    if not required.issubset(panel.columns):
        raise ValueError(f"Missing panel fields: {sorted(required - set(panel.columns))}")
    df = panel.sort_values(["LCLid", "timestamp"], kind="mergesort").reset_index(drop=True).copy()
    energy = pd.to_numeric(df.energy_kwh, errors="coerce")
    X = pd.DataFrame(index=df.index)
    X["energy_t"] = energy
    stamps = pd.to_datetime(df.timestamp)
    interval = pd.Timedelta(minutes=horizon_minutes)
    indexed_energy = {}
    for lclid, indexes in df.groupby("LCLid", sort=False).indices.items():
        times = pd.DatetimeIndex(stamps.iloc[indexes])
        if times.has_duplicates:
            raise ValueError(f"Duplicate timestamps for LCLid {lclid}; deduplicate before feature generation")
        indexed_energy[lclid] = (indexes, times, pd.Series(energy.iloc[indexes].to_numpy(), index=times))
    for lag in lag_intervals:
        X[f"energy_lag_{lag}"] = np.nan
    X["energy_change_from_previous"] = np.nan
    for window in rolling_windows:
        X[f"energy_roll_mean_{window}"] = np.nan
        X[f"energy_roll_std_{window}"] = np.nan
    target = pd.Series(np.nan, index=df.index, dtype="float64")
    target_timestamp = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
    # Every lag/window position is looked up at its exact timestamp. Gaps and
    # DST transitions therefore stay missing instead of masquerading as rows.
    for _, (indexes, times, series) in indexed_energy.items():
        for lag in lag_intervals:
            historical = series.reindex(times - interval * lag).to_numpy()
            X.loc[indexes, f"energy_lag_{lag}"] = historical
        previous = series.reindex(times - interval).to_numpy()
        X.loc[indexes, "energy_change_from_previous"] = energy.iloc[indexes].to_numpy() - previous
        for window in rolling_windows:
            matrix = np.column_stack([
                series.reindex(times - interval * offset).to_numpy()
                for offset in range(1, window + 1)
            ])
            complete = np.isfinite(matrix).all(axis=1)
            means = np.full(len(indexes), np.nan)
            stds = np.full(len(indexes), np.nan)
            means[complete] = matrix[complete].mean(axis=1)
            stds[complete] = matrix[complete].std(axis=1, ddof=1) if window > 1 else 0.0
            X.loc[indexes, f"energy_roll_mean_{window}"] = means
            X.loc[indexes, f"energy_roll_std_{window}"] = stds
        next_values = series.reindex(times + interval).to_numpy()
        has_target = np.isfinite(next_values)
        target.iloc[indexes[has_target]] = next_values[has_target]
        target_timestamp.iloc[indexes[has_target]] = times[has_target] + interval
    minute_of_day = stamps.dt.hour * 60 + stamps.dt.minute
    X["hour_sin"] = np.sin(2 * np.pi * minute_of_day / 1440)
    X["hour_cos"] = np.cos(2 * np.pi * minute_of_day / 1440)
    X["weekday_sin"] = np.sin(2 * np.pi * stamps.dt.dayofweek / 7)
    X["weekday_cos"] = np.cos(2 * np.pi * stamps.dt.dayofweek / 7)
    return X, target.rename("target_energy_kwh"), target_timestamp.rename("target_timestamp")


def valid_examples(X: pd.DataFrame, y: pd.Series, target_timestamp: pd.Series) -> pd.Series:
    return X.notna().all(axis=1) & y.notna() & target_timestamp.notna()
