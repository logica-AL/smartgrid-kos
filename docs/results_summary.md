# Ringkasan hasil eksperimen

Status laporan: **DRAFT**. Uraian ini dibuat otomatis dari artefak audit, metrik, anomali, dan biaya. Rubrik D-E belum ditemukan di direktori lokal.

Dataset utama adalah potongan London `LCL-June2015v2_0.csv`, bukan data Surabaya. Audit membaca 1,000,000 baris; setelah waktu tidak valid dan kunci duplikat ditangani tersisa 999,312 baris, dengan 30 ID rumah tangga. Energi valid ada 999,283 baris pada periode 2011-12-06 sampai 2014-02-28. Nilai nol tetap dipertahankan. Sebanyak 29 nilai energi kosong/tidak numerik dan 688 timestamp duplikat per ID tidak digunakan.

Target adalah energi kWh pada timestamp tepat 30 menit setelah pengukuran saat ini, untuk ID yang sama. Split kronologis menghasilkan train 678,694, validation 162,423, dan test 151,602 contoh valid.

| Model | MAE (kWh/30 menit) | RMSE (kWh/30 menit) | R² | n test |
|---|---:|---:|---:|---:|
| Persistence | 0,1039 | 0,2636 | 0,6526 | 151,602 |
| Linear Regression | 0,1060 | 0,2463 | 0,6966 | 151,602 |

Pada test ini, regresi memiliki RMSE dan R² lebih baik, sedangkan persistence memiliki MAE lebih rendah. Hasil tidak menunjukkan satu model unggul di semua metrik.

Isolation Forest fit hanya pada sampel train sebanyak 100,000; skor seluruh test dilaporkan untuk contamination 0.005, 0.01, 0.02. Tidak ada label insiden terverifikasi, sehingga flag perlu tinjauan manusia.

Skenario ekonomi memakai rata-rata energi household-bulan dari data London dan tarif asumsi R-1/TR Indonesia. Baris dasar: 342,92 kWh/household-bulan dengan estimasi Rp495,412; reduksi 5% dan 10% adalah simulasi. Ini bukan tagihan aktual kos Surabaya.
