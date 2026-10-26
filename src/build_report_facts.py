"""Build the report's single numeric source of truth from experiment artifacts."""
from pathlib import Path
import csv, json, shutil, yaml
from data_pipeline import load_json, write_json

def fmt(n, decimals=4): return f"{n:,.{decimals}f}".replace(",","X").replace(".",",").replace("X",".")

def main():
    root=Path.cwd(); out=root/"outputs"
    config=yaml.safe_load((root/"config.yaml").read_text(encoding="utf-8"))
    (root/"reports").mkdir(parents=True,exist_ok=True)
    quality=load_json(out/"data_quality_report.json"); insights=load_json(out/"data_insights.json"); metrics=load_json(out/"metrics.json")
    anomalies=load_json(out/"anomaly_summary.json"); costs=list(__import__('pandas').read_csv(out/"cost_scenarios.csv").to_dict(orient="records"))
    bfs=load_json(out/"bfs_result.json")
    with (root/"source_register.csv").open(encoding="utf-8",newline="") as f: sources=list(csv.DictReader(f))
    shutil.copy2(root/"source_register.csv",out/"source_register.csv")
    facts={"report_status":"DRAFT - Bagian A-C selesai; URL video presentasi belum tersedia.",
      "title":"Perancangan Sistem Smart Grid untuk Pemantauan dan Prediksi Konsumsi Listrik Kos Mahasiswa di Surabaya Menggunakan Regresi Linear guna Mendukung Efisiensi Energi dan Penghematan Biaya Listrik",
      "identity":{"nrp":config["report"]["student_nrp"],"name":config["report"]["student_name"],"term":config["report"]["term"]},
      "dataset":{"publisher":"Greater London Authority; data berasal dari UK Power Networks Low Carbon London","source_url":"https://data.london.gov.uk/dataset/smartmeter-energy-consumption-data-in-london-households-vqm0d",
        "license":"Creative Commons Attribution (London Datastore metadata)","doi":"Tidak tercantum pada laman sumber yang diperiksa.",
        "local_file":"data/raw/LCL-June2015v2_0.csv","full_release_rows_approx":167000000,"local_rows":quality["rows_before_cleaning"],
        "unique_households":quality["unique_households"],"timestamp_min":quality["timestamp_min"],"timestamp_max":quality["timestamp_max"],
        "valid_energy_rows":quality["rows_with_valid_numeric_energy_after_cleaning"],"energy_missing_or_invalid":quality["energy_missing_or_invalid_rows"],
        "duplicate_household_timestamps_removed":quality["duplicate_household_timestamp_rows_removed"],"valid_zero_energy":quality["valid_zero_energy_rows"],
        "customer_categories":quality["customer_categories"],"interval_30min_count":quality["interval_30_minutes_count"],
        "other_interval_count":quality["interval_other_than_30_minutes_count"],"sum_valid_kwh":quality["valid_energy_sum_kwh"],"quality":quality},
      "tariffs":quality["tariffs_audit"],"insights":insights,"experiment":metrics,"anomalies":anomalies,"cost_scenarios":costs,"bfs":bfs,
      "sources":sources,"figures":["outputs/figures/Arsitektur_SmartGrid_Kos_Mahasiswa_LONDON.png","outputs/figures/energy_distribution.png",
        "outputs/figures/hourly_profile.png","outputs/figures/weekday_profile.png","outputs/figures/monthly_profile.png","outputs/figures/model_comparison.png","outputs/figures/actual_vs_predicted.png",
        "outputs/figures/residuals.png","outputs/figures/time_series_example.png","outputs/figures/anomaly_example.png","outputs/figures/cost_scenarios.png"]}
    write_json(out/"report_facts.json",facts)
    main=facts["experiment"]["metrics_test"]
    by={x["model"]:x for x in main}; lr=by["linear_regression"]; base=by["persistence_same_household"]
    a=facts["dataset"]; c=facts["cost_scenarios"]
    summary=f"""# Ringkasan hasil eksperimen

Status laporan: **DRAFT** sampai URL video diisi. Uraian ini dibuat otomatis dari artefak audit, metrik, anomali, dan biaya. Cakupan laporan mengikuti Bagian A-C pada instruksi tugas.

Dataset utama adalah potongan London `LCL-June2015v2_0.csv`, bukan data Surabaya. Audit membaca {a['local_rows']:,} baris; setelah waktu tidak valid dan kunci duplikat ditangani tersisa {a['quality']['rows_after_timestamp_and_duplicate_cleaning']:,} baris, dengan {a['unique_households']} ID rumah tangga. Energi valid ada {a['valid_energy_rows']:,} baris pada periode {a['timestamp_min'][:10]} sampai {a['timestamp_max'][:10]}. Nilai nol tetap dipertahankan. Sebanyak {a['energy_missing_or_invalid']} nilai energi kosong/tidak numerik dan {a['duplicate_household_timestamps_removed']} timestamp duplikat per ID tidak digunakan.

Insight deskriptif sampel: rata-rata {fmt(insights['energy_kwh_per_30min']['mean'],4)} kWh dan median {fmt(insights['energy_kwh_per_30min']['median'],4)} kWh per 30 menit; rerata tertinggi pada jam {insights['temporal_profiles']['highest_mean_hour']:02d}. Ini pola sampel London, bukan temuan lapangan Surabaya.

Target adalah energi kWh pada timestamp tepat 30 menit setelah pengukuran saat ini, untuk ID yang sama. Split kronologis menghasilkan train {facts['experiment']['splits']['train']['observations']:,}, validation {facts['experiment']['splits']['validation']['observations']:,}, dan test {facts['experiment']['splits']['test']['observations']:,} contoh valid.

| Model | MAE (kWh/30 menit) | RMSE (kWh/30 menit) | R² | n test |
|---|---:|---:|---:|---:|
| Persistence | {fmt(base['MAE_kWh_per_30min'])} | {fmt(base['RMSE_kWh_per_30min'])} | {fmt(base['R2'])} | {base['observations']:,} |
| Linear Regression | {fmt(lr['MAE_kWh_per_30min'])} | {fmt(lr['RMSE_kWh_per_30min'])} | {fmt(lr['R2'])} | {lr['observations']:,} |

Pada test ini, regresi memiliki RMSE dan R² lebih baik, sedangkan persistence memiliki MAE lebih rendah. Hasil tidak menunjukkan satu model unggul di semua metrik.

Isolation Forest fit hanya pada sampel train sebanyak {facts['anomalies']['fit_sample_rows']:,}; skor seluruh test dilaporkan untuk contamination {', '.join(facts['anomalies']['sensitivity'].keys())}. Tidak ada label insiden terverifikasi, sehingga flag perlu tinjauan manusia.

Skenario ekonomi memakai rata-rata energi household-bulan dari data London dan tarif asumsi R-1/TR Indonesia. Baris dasar: {fmt(c[0]['mean_household_month_kwh'],2)} kWh/household-bulan dengan estimasi Rp{c[0]['estimated_cost_idr_per_household_month']:,.0f}; reduksi 5% dan 10% adalah simulasi. Ini bukan tagihan aktual kos Surabaya.
"""
    (root/"docs/results_summary.md").write_text(summary,encoding="utf-8")
    # Every quantitative statement in generated report can be traced to artifacts/fields.
    rows=[("Raw local observations","outputs/data_quality_report.json","rows_before_cleaning"),("Unique households","outputs/data_quality_report.json","unique_households"),
      ("Energy missing or invalid","outputs/data_quality_report.json","energy_missing_or_invalid_rows"),("Duplicate timestamps removed","outputs/data_quality_report.json","duplicate_household_timestamp_rows_removed"),
      ("Valid energy rows and zero readings","outputs/data_quality_report.json","rows_with_valid_numeric_energy_after_cleaning; valid_zero_energy_rows"),
      ("Observed timestamp period and interval frequencies","outputs/data_quality_report.json","timestamp_min; timestamp_max; interval_counts_minutes"),
      ("Tariff workbook sheets, schema, dates, and categories","outputs/data_quality_report.json","tariffs_audit.sheets.*"),
      ("Target valid examples and exact horizon","outputs/metrics.json","valid_examples; target"),
      ("Train/validation/test counts and boundaries","outputs/metrics.json","splits.*.observations; temporal_boundaries"),
      ("Historical high-use reference","outputs/data_quality_report.json","high_energy_reference.percentile; threshold_kwh_per_30min"),
      ("Model MAE/RMSE/R2","outputs/model_comparison.csv","MAE_kWh_per_30min; RMSE_kWh_per_30min; R2"),
      ("Anomaly sample, seed, counts, scores","outputs/anomaly_summary.json","fit_sample_rows; random_state; sensitivity.*"),
      ("Monthly cost scenarios and assumed rate","outputs/cost_scenarios.csv","mean_household_month_kwh; tariff_idr_per_kwh; estimated_cost_idr_per_household_month"),
      ("Tariff class and dated source","config.yaml","economics.customer_class; source_url; access_date"),
      ("EDA statistics and descriptive peaks","outputs/data_insights.json","energy_kwh_per_30min; temporal_profiles"),
      ("Prior-study results and publication dates","outputs/source_register.csv","S3; S4"),
      ("Full London release metadata and DOI statement","outputs/report_facts.json","dataset.full_release_rows_approx; dataset.license; dataset.doi"),
      ("BFS path and explored nodes","outputs/bfs_result.json","path; explored_count; complexity")]
    with (root/"docs/report_traceability.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,lineterminator="\n"); w.writerow(["report_claim","source_artifact","source_field"]); w.writerows(rows)
    guide=f"""# Panduan pembaruan laporan ETS

**Status: DRAFT sampai URL video presentasi tersedia.** Laporan mengikuti Bagian A-C pada instruksi tugas. Isi `report.student_nrp`, `report.student_name`, dan `report.video_url` pada `config.yaml` sebelum membuat berkas pengumpulan. Hindari membagikan konfigurasi berisi identitas ke repositori publik.

## Angka aktual dari artefak

- Sampel lokal: {a['local_rows']:,} baris; {a['unique_households']} household; {a['timestamp_min']} hingga {a['timestamp_max']}.
- Data numerik energi: {a['valid_energy_rows']:,}; missing/non-numeric {a['energy_missing_or_invalid']}; duplicate timestamp per LCLid dihapus {a['duplicate_household_timestamps_removed']}.
- Test n={lr['observations']:,}. Persistence MAE {base['MAE_kWh_per_30min']:.6f}, RMSE {base['RMSE_kWh_per_30min']:.6f}, R2 {base['R2']:.6f}. Linear Regression MAE {lr['MAE_kWh_per_30min']:.6f}, RMSE {lr['RMSE_kWh_per_30min']:.6f}, R2 {lr['R2']:.6f}. Satuan MAE/RMSE kWh per 30 menit.
- Prediksi vs baseline bersifat campuran: persistence memiliki MAE lebih baik, regresi memiliki RMSE dan R2 lebih baik.
- Anomali, biaya, split, tanggal, dan semua fakta tercatat dalam `outputs/report_facts.json`.

## Gambar

`outputs/figures/Arsitektur_SmartGrid_Kos_Mahasiswa_LONDON.png`, `energy_distribution.png`, `hourly_profile.png`, `weekday_profile.png`, `monthly_profile.png`, `model_comparison.png`, `actual_vs_predicted.png`, `residuals.png`, `time_series_example.png`, `anomaly_example.png`, dan `cost_scenarios.png`.

## Batas klaim dan pekerjaan tersisa

Data mengukur household London; generalisasi ke kos Surabaya belum diuji. CSV lokal hanya potongan satu juta baris dari sekitar 167 juta baris pada rilis penuh. Semua pelanggan lokal berkategori Std; label tarif dinamis workbook tidak cocok untuk merge baris lokal. Tidak ada label kejadian anomali. Biaya memakai energi London dan asumsi tarif rupiah, bukan tagihan aktual. Tidak ada perangkat keras, kontrol relay, audit keamanan, pengukuran lapangan, atau penghematan terverifikasi. Identitas dan URL video diambil dari konfigurasi lokal.
"""
    (root/"reports/REPORT_UPDATE_GUIDE.md").write_text(guide,encoding="utf-8")
    print({"facts":str(out/"report_facts.json"),"summary":str(root/"docs/results_summary.md"),"traceability_rows":len(rows)})

if __name__=="__main__": main()
