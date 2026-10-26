"""Cost scenarios for a representative sample household-month."""
from __future__ import annotations

import pandas as pd


def monthly_household_energy(panel: pd.DataFrame, min_coverage_fraction: float = 0.95) -> pd.Series:
    """Return household-month totals only when valid readings cover enough of a month."""
    if not 0 <= min_coverage_fraction <= 1:
        raise ValueError("min_coverage_fraction harus berada pada rentang 0 sampai 1")
    data = panel.dropna(subset=["timestamp", "energy_kwh"]).copy()
    data["year_month"] = data.timestamp.dt.to_period("M").astype(str)
    grouped = data.groupby(["LCLid", "year_month"], observed=True)
    totals = grouped.energy_kwh.sum(min_count=1)
    counts = grouped.energy_kwh.count()
    # London's source timestamps are naive local time. Use nominal half-hourly
    # slots per calendar month; a 95% threshold tolerates DST and small gaps.
    days = data.groupby(["LCLid", "year_month"], observed=True).timestamp.first().map(
        lambda ts: ts.days_in_month * 48
    )
    coverage = counts / days
    return totals.loc[coverage.ge(min_coverage_fraction)]


def cost_scenarios(monthly_totals: pd.Series, tariff_idr_per_kwh: float) -> pd.DataFrame:
    mean_kwh = float(monthly_totals.mean())
    return pd.DataFrame([{"reduction_percent": pct, "mean_household_month_kwh": mean_kwh * (1 - pct / 100),
                          "tariff_idr_per_kwh": float(tariff_idr_per_kwh),
                          "estimated_cost_idr_per_household_month": mean_kwh * (1 - pct / 100) * tariff_idr_per_kwh,
                          "status": "simulation; London energy x assumed Indonesian household tariff"}
                         for pct in (0, 5, 10)])
