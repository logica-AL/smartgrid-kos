"""Cost scenarios for a representative sample household-month."""
from __future__ import annotations

import pandas as pd


def monthly_household_energy(panel: pd.DataFrame) -> pd.Series:
    data = panel.dropna(subset=["timestamp", "energy_kwh"]).copy()
    data["year_month"] = data.timestamp.dt.to_period("M").astype(str)
    totals = data.groupby(["LCLid", "year_month"], observed=True).energy_kwh.sum(min_count=1)
    return totals


def cost_scenarios(monthly_totals: pd.Series, tariff_idr_per_kwh: float) -> pd.DataFrame:
    mean_kwh = float(monthly_totals.mean())
    return pd.DataFrame([{"reduction_percent": pct, "mean_household_month_kwh": mean_kwh * (1 - pct / 100),
                          "tariff_idr_per_kwh": float(tariff_idr_per_kwh),
                          "estimated_cost_idr_per_household_month": mean_kwh * (1 - pct / 100) * tariff_idr_per_kwh,
                          "status": "simulation; London energy x assumed Indonesian household tariff"}
                         for pct in (0, 5, 10)])
