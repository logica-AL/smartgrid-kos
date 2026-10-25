"""Train and evaluate one-step-ahead London half-hourly energy forecasts."""
from __future__ import annotations

import argparse, json, time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from data_pipeline import read_meter_file, audit_tariffs, write_json
from economics import monthly_household_energy, cost_scenarios
from features import make_supervised, valid_examples
from figures import draw_series, draw_histogram, draw_cost_scenarios


def score_row(name, actual, pred):
    return {"model": name, "MAE_kWh_per_30min": float(mean_absolute_error(actual,pred)),
            "RMSE_kWh_per_30min": float(mean_squared_error(actual,pred)**.5), "R2": float(r2_score(actual,pred)),
            "observations": int(len(actual))}


def make_split(df, y, target_time, valid, train_fraction, validation_fraction):
    times=np.sort(df.loc[valid,"timestamp"].dropna().unique())
    if len(times)<100: raise ValueError(f"Terlalu sedikit waktu unik untuk split kronologis: {len(times)}")
    i1=max(1,int(len(times)*train_fraction)-1); i2=min(len(times)-2,int(len(times)*(train_fraction+validation_fraction))-1)
    cut1=pd.Timestamp(times[i1]); cut2=pd.Timestamp(times[i2])
    t=df.timestamp
    # Require each label to fall within the same temporal partition as its feature row.
    train=valid & t.le(cut1) & target_time.le(cut1)
    val=valid & t.gt(cut1) & t.le(cut2) & target_time.le(cut2)
    test=valid & t.gt(cut2) & target_time.gt(cut2)
    return {"train":train,"validation":val,"test":test},cut1,cut2


def run(config_path="config.yaml"):
    start=time.time(); root=Path.cwd(); cfg=yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    out=root/"outputs"; (out/"figures").mkdir(parents=True,exist_ok=True)
    panel, audit=read_meter_file(root/cfg["data"]["meter_file"])
    audit["tariffs_audit"] = audit_tariffs(root/cfg["data"]["tariffs_file"])
    X,y,target_time=make_supervised(panel,int(cfg["model"]["horizon_minutes"]),tuple(cfg["model"]["lag_intervals"]),tuple(cfg["model"]["rolling_windows"]))
    valid=valid_examples(X,y,target_time)
    splits,cut1,cut2=make_split(panel,y,target_time,valid,float(cfg["model"]["train_fraction"]),float(cfg["model"]["validation_fraction"]))
    if any(int(mask.sum())<100 for mask in splits.values()): raise ValueError("Salah satu split memiliki kurang dari 100 contoh valid")
    X=X.astype("float32"); y=y.astype("float32")
    train,val,test=splits["train"],splits["validation"],splits["test"]
    model=LinearRegression()
    model.fit(X.loc[train],y.loc[train])
    val_pred=model.predict(X.loc[val]); test_pred=model.predict(X.loc[test])
    y_val=y.loc[val]; y_test=y.loc[test]
    naive_val=X.loc[val,"energy_t"].to_numpy(dtype=float); naive_test=X.loc[test,"energy_t"].to_numpy(dtype=float)
    metrics={"target":"energy_kwh at the next exact +30 minute timestamp for the same LCLid",
       "mode":"one-step-ahead; observed energy E(t) is available at prediction time",
       "unit":"kWh per 30-minute interval", "feature_names":list(X.columns),
       "valid_examples":int(valid.sum()), "splits":{}, "temporal_boundaries":{"train_end":cut1.isoformat(),"validation_end":cut2.isoformat()},
       "metrics_validation":[score_row("persistence_same_household",y_val,naive_val),score_row("linear_regression",y_val,val_pred)],
       "metrics_test":[score_row("persistence_same_household",y_test,naive_test),score_row("linear_regression",y_test,test_pred)],
       "train_only_fit":True,"random_state":int(cfg["model"]["random_state"]),"linear_regression":"sklearn.linear_model.LinearRegression",
       "run_started_unix":start}
    for name,mask in splits.items():
        idx=np.flatnonzero(mask.to_numpy())
        metrics["splits"][name]={"observations":int(len(idx)),"timestamp_min":panel.timestamp.iloc[idx].min().isoformat(),
          "timestamp_max":panel.timestamp.iloc[idx].max().isoformat(),"target_timestamp_max":target_time.iloc[idx].max().isoformat()}
    pd.DataFrame(metrics["metrics_test"]).to_csv(out/"model_comparison.csv",index=False)
    write_json(out/"metrics.json",metrics)
    joblib.dump(model,out/"linear_regression.joblib")
    write_json(out/"model_config.json",{"config":cfg,"model_class":"sklearn.linear_model.LinearRegression","run_duration_seconds":time.time()-start,
       "python_seed":cfg["model"]["random_state"],"features":list(X.columns)})

    # Train-only historical high-use reference; this is not a safety/protection limit.
    threshold=float(panel.loc[train,"energy_kwh"].quantile(float(cfg["model"]["high_energy_percentile"])))
    audit["target_valid_examples"] = int(valid.sum())
    audit["target_excluded_rows"] = int(len(panel)-valid.sum())
    audit["target_alignment"] = "Next observed row for same LCLid is accepted only when timestamp equals current timestamp + 30 minutes."
    audit["split_counts"]={k:int(v.sum()) for k,v in splits.items()}
    audit["high_energy_reference"]={"percentile":float(cfg["model"]["high_energy_percentile"]),"threshold_kwh_per_30min":threshold,
      "fit_scope":"training partition only","meaning":"historical notification reference, not an electrical safety limit"}
    audit["valid_energy_sum_kwh"] = float(panel.energy_kwh.sum(min_count=1))
    audit["average_household_month_rows"] = int(len(monthly_household_energy(panel)))
    audit["data_source_scope"] = "Only the supplied 1,000,000-row LCL-June2015v2_0.csv extract is analyzed; the 167-million-row full release is not copied or treated as local observations."
    write_json(out/"data_quality_report.json",audit)

    # Isolation Forest: sampling only from train to bound fit time; complete test is scored.
    train_indices=np.flatnonzero(train.to_numpy()); rng=np.random.default_rng(int(cfg["model"]["random_state"]))
    sample_n=min(int(cfg["model"]["anomaly_sample_rows"]),len(train_indices)); sample_idx=rng.choice(train_indices,size=sample_n,replace=False)
    test_X=X.loc[test]; anomaly_report={"method":"IsolationForest","fit_scope":"train rows only; deterministic sample","train_rows":int(train.sum()),
        "fit_sample_rows":int(sample_n),"random_state":int(cfg["model"]["random_state"]),"test_rows":int(test.sum()),"sensitivity":{}}
    flags_one=None
    for contamination in cfg["model"]["anomaly_contamination"]:
        forest=IsolationForest(n_estimators=100,contamination=float(contamination),random_state=int(cfg["model"]["random_state"]),max_samples=sample_n,n_jobs=-1)
        forest.fit(X.loc[sample_idx]); scores=forest.score_samples(test_X); flags=forest.predict(test_X)==-1
        which=np.flatnonzero(flags)[:12]
        records=[]
        test_pos=np.flatnonzero(test.to_numpy())
        for j in which:
            lclid=str(panel.iloc[test_pos[j]].LCLid)
            import hashlib
            records.append({"timestamp":panel.iloc[test_pos[j]].timestamp.isoformat(),"household_pseudonym":hashlib.sha256(lclid.encode()).hexdigest()[:10],
              "score":float(scores[j]),"energy_kwh_per_30min":float(test_X.iloc[j].energy_t)})
        anomaly_report["sensitivity"][str(contamination)]={"flagged_count":int(flags.sum()),"flagged_percent":float(flags.mean()*100),
          "decision_score_threshold":float(forest.offset_),"score_min":float(scores.min()),"score_median":float(np.median(scores)),"score_max":float(scores.max()),
          "examples":records,"interpretation":"Unusual consumption pattern for human review; no verified incident labels."}
        if float(contamination)==0.01: flags_one=flags
    write_json(out/"anomaly_summary.json",anomaly_report)
    test_pos=np.flatnonzero(test.to_numpy()); test_vals=panel.iloc[test_pos]
    limit=min(1200,len(test_vals)); actual=y.loc[test].to_numpy(dtype=float); pred=test_pred.astype(float)
    draw_series(out/"figures/actual_vs_predicted.png","Prediksi energi interval berikutnya pada test","Energi (kWh / 30 menit)",
       [("Aktual",actual[:limit].tolist(),"#2878c8"),("Linear Regression",pred[:limit].tolist(),"#e05a47")])
    draw_histogram(out/"figures/residuals.png","Residual model pada data test",(actual-pred).tolist(),"Residual energi kWh per 30 menit")
    # Show one household selected deterministically from the test partition.
    example_id=str(test_vals.LCLid.iloc[0]); selected=test_vals.LCLid.eq(example_id).to_numpy(); actual_one=actual[selected][:limit]
    pred_one=pred[selected][:limit]
    draw_series(out/"figures/time_series_example.png","Contoh deret waktu test untuk satu rumah tangga","Energi (kWh / 30 menit)",
       [("Aktual",actual_one.tolist(),"#2878c8"),("Prediksi",pred_one.tolist(),"#e05a47")])
    powers=test_X.energy_t.to_numpy(dtype=float); marked=[float(v) if flag else float('nan') for v,flag in zip(powers[:limit],(flags_one if flags_one is not None else np.zeros(len(powers),dtype=bool))[:limit])]
    draw_series(out/"figures/anomaly_example.png","Isolation Forest pada interval test","Energi terukur (kWh / 30 menit)",
       [("Pengukuran",powers[:limit].tolist(),"#2878c8"),("Flag anomali 1%",marked,"#e05a47")])

    monthly=monthly_household_energy(panel); economic=cfg["economics"]
    costs=cost_scenarios(monthly,float(economic["tariff_idr_per_kwh"]))
    costs.to_csv(out/"cost_scenarios.csv",index=False)
    draw_cost_scenarios(out/"figures/cost_scenarios.png",costs.to_dict(orient="records"))
    metrics["mean_household_month_energy_kwh"]=float(monthly.mean()); metrics["mean_household_month_observations"]=int(len(monthly))
    write_json(out/"metrics.json",metrics)
    print(json.dumps({"test_metrics":metrics["metrics_test"],"split_counts":metrics["splits"],"anomaly_flags_1pct":anomaly_report["sensitivity"].get("0.01",{}).get("flagged_count"),
       "mean_household_month_kwh":float(monthly.mean()),"run_duration_seconds":time.time()-start},indent=2))


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--config",default="config.yaml"); args=parser.parse_args(); run(args.config)

if __name__=="__main__": main()
