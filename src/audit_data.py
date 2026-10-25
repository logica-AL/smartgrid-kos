"""Run fresh audits on the copied local CSV and every tariff workbook sheet."""
from pathlib import Path
import argparse
import pandas as pd
import yaml

from data_pipeline import audit_tariffs, read_meter_file, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    root = Path.cwd()
    meter, report = read_meter_file(root / config["data"]["meter_file"])
    by_household = meter.groupby("LCLid").agg(first_timestamp=("timestamp", "min"), last_timestamp=("timestamp", "max"),
                                                   rows=("timestamp", "size"), energy_valid_rows=("energy_kwh", "count"),
                                                   energy_missing_or_invalid=("energy_kwh", lambda s: int(s.isna().sum())))
    by_household.to_csv(root / "outputs" / "household_frequency.csv")
    tariff = audit_tariffs(root / config["data"]["tariffs_file"])
    report["tariffs_audit"] = tariff
    report["energy_statistics_valid_values"] = {"count": int(meter.energy_kwh.notna().sum()),
       "sum_kwh": float(meter.energy_kwh.sum()), "mean_kwh_per_30min": float(meter.energy_kwh.mean()),
       "median_kwh_per_30min": float(meter.energy_kwh.median()), "min_kwh_per_30min": float(meter.energy_kwh.min()),
       "max_kwh_per_30min": float(meter.energy_kwh.max())}
    report["household_frequency_file"] = "outputs/household_frequency.csv"
    report["data_source_scope"] = "Only the supplied 1,000,000-row LCL-June2015v2_0.csv extract is analyzed; the 167-million-row full release is not copied or treated as local observations."
    write_json(root / "outputs" / "data_quality_report.json", report)
    print({"rows": report["rows_before_cleaning"], "after": report["rows_after_timestamp_and_duplicate_cleaning"],
           "households": report["unique_households"], "period": [report["timestamp_min"], report["timestamp_max"]]})


if __name__ == "__main__":
    main()
