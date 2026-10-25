# Proyek Smart Grid Kos Mahasiswa

Proyek eksperimen ETS ini menggunakan potongan dataset smart meter London yang disediakan lokal. Dataset utama adalah energi kWh per 30 menit dari `LCL-June2015v2_0.csv`. Surabaya adalah konteks rancangan; data London bukan pengukuran kos Surabaya. Laporan saat ini berstatus DRAFT karena rincian Bagian D-E belum ditemukan. Proyek ini menggunakan dataset London; dataset Prancis yang tersedia di workspace bukan dataset eksperimen proyek ini.

## Data lokal

`data/raw/LCL-June2015v2_0.csv` dan `data/raw/Tariffs.xlsx` adalah salinan byte-identik dari file sumber di workspace. File mentah tidak diubah. Ukuran dataset penuh London sekitar 167 juta baris; file lokal hanya potongan satu juta baris. Workbook tarif di-audit semua sheet, tetapi tidak digabungkan karena lokal hanya berkategori Std sementara workbook memuat jadwal dinamis ToU.

## Menjalankan ulang

Jalankan dari folder `smartgrid-kos/` dengan Python yang menyediakan paket di `requirements.txt`:

```bash
python3 src/audit_data.py --config config.yaml
python3 src/train_regression.py --config config.yaml
python3 src/detect_anomalies.py --config config.yaml
python3 src/search_demo.py
python3 src/build_report_facts.py
python3 -m pytest -q
```

Untuk membuat DOCX dan PDF setelah DOCX generator tersedia:

```bash
python3 src/build_report_facts.py
python3 src/generate_report.py
python3 src/export_report.py
```

`requirements.txt` mencatat dependensi yang diperlukan pada lingkungan Python proyek. Perintah audit, train, deteksi anomali, BFS, pembangun fakta, pengujian, generator DOCX, ekspor PDF, dan render QA sudah dicoba pada salinan proyek ini. Hasil aktual berada di `outputs/`; ringkasan laporan dibuat otomatis dari `outputs/report_facts.json`. LibreOffice harus tersedia sebagai `soffice` di PATH untuk ekspor PDF.

Render halaman PNG untuk pemeriksaan visual dapat dijalankan dengan `render_docx.py` dari skill Documents yang tersedia di lingkungan kerja. Laporan ini tetap berstatus DRAFT sampai rubrik D-E dikonfirmasi.

## Artefak penting

- `outputs/data_quality_report.json`, `household_frequency.csv`
- `outputs/metrics.json`, `model_comparison.csv`, `linear_regression.joblib`, `model_config.json`
- `outputs/anomaly_summary.json`, `cost_scenarios.csv`, `bfs_result.json`
- `outputs/source_register.csv`, `report_facts.json`, `outputs/figures/`
- `docs/` berisi provenance, kamus, metodologi, keamanan, ringkasan aktual, dan traceability
- `reports/` berisi panduan laporan dan dokumen ETS DRAFT
- `notebooks/01_data_audit.ipynb`, `02_regression_forecast.ipynb`, dan `03_isolation_forest.ipynb` menyediakan walkthrough yang memanggil pipeline yang sama

## Status laporan

Rubrik A-C sudah dibangun berdasarkan hasil run. Bagian D-E dan nama mahasiswa belum diketahui. Jangan mengirimkan berkas DRAFT sebagai laporan final sebelum rubrik lengkap, placeholder identitas/video diisi, dan PDF diperbarui serta diperiksa kembali.
