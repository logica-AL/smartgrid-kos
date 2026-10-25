"""Rebuild the same London panel and run train-only Isolation Forest sensitivity."""
from pathlib import Path
import argparse, hashlib
import numpy as np
import pandas as pd
import yaml
from sklearn.ensemble import IsolationForest
from data_pipeline import read_meter_file, write_json
from features import make_supervised, valid_examples

def main():
    p=argparse.ArgumentParser(); p.add_argument("--config",default="config.yaml"); a=p.parse_args()
    root=Path.cwd(); cfg=yaml.safe_load(Path(a.config).read_text()); panel,_=read_meter_file(root/cfg["data"]["meter_file"])
    X,y,target=make_supervised(panel,int(cfg["model"]["horizon_minutes"]),tuple(cfg["model"]["lag_intervals"]),tuple(cfg["model"]["rolling_windows"]))
    valid=valid_examples(X,y,target); times=np.sort(panel.loc[valid,"timestamp"].unique())
    split_index=int(len(times)*cfg["model"]["train_fraction"]); cutoff=pd.Timestamp(times[max(1,split_index-1)])
    second_index=int(len(times)*(cfg["model"]["train_fraction"]+cfg["model"]["validation_fraction"])); cutoff2=pd.Timestamp(times[min(len(times)-2,second_index-1)])
    train=valid & panel.timestamp.le(cutoff) & target.le(cutoff); test=valid & panel.timestamp.gt(cutoff2) & target.gt(cutoff2)
    X=X.astype("float32"); train_idx=np.flatnonzero(train); rng=np.random.default_rng(int(cfg["model"]["random_state"]))
    sample_n=min(int(cfg["model"]["anomaly_sample_rows"]),len(train_idx)); sample=rng.choice(train_idx,sample_n,replace=False)
    report={"method":"IsolationForest","fit_scope":"train rows only; deterministic sample","train_rows":int(train.sum()),
      "fit_sample_rows":sample_n,"random_state":int(cfg["model"]["random_state"]),"test_rows":int(test.sum()),"sensitivity":{}}
    test_X=X.loc[test]
    for c in cfg["model"]["anomaly_contamination"]:
        m=IsolationForest(n_estimators=100,contamination=float(c),random_state=int(cfg["model"]["random_state"]),max_samples=sample_n,n_jobs=-1).fit(X.loc[sample])
        scores=m.score_samples(test_X); flags=m.predict(test_X)==-1; examples=[]
        pos=np.flatnonzero(test.to_numpy())
        for j in np.flatnonzero(flags)[:12]:
            ident=str(panel.iloc[pos[j]].LCLid)
            examples.append({"timestamp":panel.iloc[pos[j]].timestamp.isoformat(),"household_pseudonym":hashlib.sha256(ident.encode()).hexdigest()[:10],"score":float(scores[j]),"energy_kwh_per_30min":float(test_X.iloc[j].energy_t)})
        report["sensitivity"][str(c)]={"flagged_count":int(flags.sum()),"flagged_percent":float(flags.mean()*100),"decision_score_threshold":float(m.offset_),
          "score_min":float(scores.min()),"score_median":float(np.median(scores)),"score_max":float(scores.max()),"examples":examples,
          "interpretation":"Unusual consumption pattern for human review; no verified incident labels."}
    write_json(root/"outputs/anomaly_summary.json",report); print({"test_rows":report["test_rows"],"sensitivity":list(report["sensitivity"])})

if __name__=="__main__": main()
