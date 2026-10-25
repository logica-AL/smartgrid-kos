from pathlib import Path
import pandas as pd
from src.data_pipeline import read_meter_file


def test_real_sample_audit_reports_source_file():
    path=Path(__file__).parents[1]/"data/raw/LCL-June2015v2_0.csv"
    panel,report=read_meter_file(path)
    assert report["rows_before_cleaning"]==1_000_000
    assert report["unique_households"]==30
    assert report["energy_missing_or_invalid_rows"]>0
    assert "KWH/hh (per half hour) " in report["raw_column_names"]
    assert report["rows_with_valid_numeric_energy_after_cleaning"]==int(panel.energy_kwh.notna().sum())
