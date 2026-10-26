import pandas as pd
from src.economics import cost_scenarios, monthly_household_energy


def test_cost_scenarios_use_kwh_once():
    costs=cost_scenarios(pd.Series([100.0]),1000)
    assert costs.estimated_cost_idr_per_household_month.tolist()==[100000.0,95000.0,90000.0]


def test_monthly_energy_keeps_valid_zero_and_omits_missing():
    frame=pd.DataFrame({"LCLid":["a","a","a"],"timestamp":pd.to_datetime(["2024-01-01 00:00:00","2024-01-01 00:30:00","2024-01-01 01:00:00"]),"energy_kwh":[0.0,0.5,float("nan")]})
    result=monthly_household_energy(frame,min_coverage_fraction=0.0)
    assert result.iloc[0]==0.5


def test_monthly_energy_excludes_incomplete_household_months():
    good=pd.date_range("2024-01-01",periods=1414,freq="30min")
    low=pd.date_range("2024-01-01",periods=1413,freq="30min")
    frame=pd.concat([
        pd.DataFrame({"LCLid":"good","timestamp":good,"energy_kwh":1.0}),
        pd.DataFrame({"LCLid":"low","timestamp":low,"energy_kwh":1.0}),
    ],ignore_index=True)
    result=monthly_household_energy(frame)
    assert len(result)==1
    assert result.index[0][0]=="good"
    assert result.iloc[0]==1414.0
