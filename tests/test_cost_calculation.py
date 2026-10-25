import pandas as pd
from src.economics import cost_scenarios, monthly_household_energy


def test_cost_scenarios_use_kwh_once():
    costs=cost_scenarios(pd.Series([100.0]),1000)
    assert costs.estimated_cost_idr_per_household_month.tolist()==[100000.0,95000.0,90000.0]


def test_monthly_energy_keeps_valid_zero_and_omits_missing():
    frame=pd.DataFrame({"LCLid":["a","a","a"],"timestamp":pd.to_datetime(["2024-01-01 00:00:00","2024-01-01 00:30:00","2024-01-01 01:00:00"]),"energy_kwh":[0.0,0.5,float("nan")]})
    result=monthly_household_energy(frame)
    assert result.iloc[0]==0.5
