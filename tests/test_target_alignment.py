import pandas as pd
from src.features import make_supervised, valid_examples


def sample_panel():
    times=pd.date_range("2024-01-01",periods=60,freq="30min")
    return pd.DataFrame({"LCLid":["A"]*60+ ["B"]*60,"timestamp":list(times)*2,"energy_kwh":list(range(60))+list(range(100,160))})


def test_target_is_exact_next_30_minutes_and_same_household():
    df=sample_panel(); X,y,target=make_supervised(df,30,(1,),(4,))
    row=10
    assert y.iloc[row]==11
    assert target.iloc[row]==df.timestamp.iloc[row]+pd.Timedelta(minutes=30)
    assert y.iloc[59] != 100
    assert pd.isna(y.iloc[59])


def test_gap_does_not_receive_shifted_row_as_next_interval():
    df=sample_panel().iloc[:60].copy(); df.loc[11,"timestamp"] += pd.Timedelta(minutes=15)
    df=df.sort_values("timestamp").reset_index(drop=True)
    _,y,target=make_supervised(df,30,(1,),(4,))
    row=int(df.index[df.timestamp.eq(pd.Timestamp("2024-01-01 05:00:00"))][0])
    assert pd.isna(y.iloc[row])
    assert pd.isna(target.iloc[row])


def test_lag_feature_requires_exact_historical_interval():
    df=sample_panel().iloc[:60].copy(); df.loc[11,"timestamp"] += pd.Timedelta(minutes=15)
    df=df.sort_values("timestamp").reset_index(drop=True)
    X,_,_=make_supervised(df,30,(1,),(4,))
    row=int(df.index[df.timestamp.eq(pd.Timestamp("2024-01-01 06:00:00"))][0])
    assert pd.isna(X.loc[row,"energy_lag_1"])


def test_future_change_does_not_change_current_features():
    df=sample_panel().iloc[:60].copy()
    X1,_,_=make_supervised(df,30,(1,2),(4,))
    changed=df.copy(); changed.loc[20,"energy_kwh"]=99999
    X2,_,_=make_supervised(changed,30,(1,2),(4,))
    # At t=10, feature windows end at t, so modifying t=20 cannot affect them.
    pd.testing.assert_series_equal(X1.loc[10],X2.loc[10])
