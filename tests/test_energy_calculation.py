from src.economics import cost_scenarios
import pandas as pd


def test_interval_energy_is_not_multiplied_by_half_hour():
    # London values are already kWh per 30-minute interval.
    result=cost_scenarios(pd.Series([2.0]),1000)
    assert result.iloc[0].estimated_cost_idr_per_household_month==2000
