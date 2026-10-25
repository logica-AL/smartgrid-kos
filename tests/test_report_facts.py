import json
from pathlib import Path
import pandas as pd


def test_report_facts_match_result_artifacts():
    root=Path(__file__).resolve().parents[1]
    facts=json.loads((root/"outputs/report_facts.json").read_text(encoding="utf-8"))
    quality=json.loads((root/"outputs/data_quality_report.json").read_text(encoding="utf-8"))
    metrics=json.loads((root/"outputs/metrics.json").read_text(encoding="utf-8"))
    comparison=pd.read_csv(root/"outputs/model_comparison.csv")
    assert facts["dataset"]["local_rows"]==quality["rows_before_cleaning"]
    assert facts["dataset"]["valid_energy_rows"]==quality["rows_with_valid_numeric_energy_after_cleaning"]
    assert facts["experiment"]["splits"]==metrics["splits"]
    fact_models={row["model"]:row for row in facts["experiment"]["metrics_test"]}
    artifact_models={row["model"]:row for row in comparison.to_dict(orient="records")}
    assert fact_models.keys()==artifact_models.keys()
    for name in fact_models:
        assert fact_models[name]["observations"]==artifact_models[name]["observations"]
        assert abs(fact_models[name]["MAE_kWh_per_30min"]-artifact_models[name]["MAE_kWh_per_30min"])<1e-12
