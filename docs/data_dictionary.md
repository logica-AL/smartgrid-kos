# Kamus data

| Nama sumber | Bentuk lokal | Satuan/arti | Peran | Transformasi |
|---|---|---|---|---|
| `LCLid` | String pseudonim | Identitas rumah tangga pada sampel | Kunci grup | Tidak digunakan sebagai angka/fitur kontinu; hanya mengelompokkan riwayat dan memastikan target tetap pada rumah yang sama |
| `stdorToU` | Kategori (`Std`) | Jenis tarif pada sumber | Audit | Tidak menjadi fitur; seluruh sampel lokal hanya `Std` |
| `DateTime` | Timestamp lokal sumber | Waktu akhir/label pembacaan | Index waktu, fitur siklik, batas split, alignment target | Parse pandas, urut per ID dan waktu, timestamp harus tepat `t + 30 menit` untuk target |
| `KWH/hh (per half hour)` | Numerik kWh/interval | Energi dalam interval setengah jam | Fitur saat ini, lag, rolling, target | `pd.to_numeric(errors='coerce')`; nilai nol sah dipertahankan; nilai kosong/tidak numerik tetap missing |
| `energy_t` | Numerik kWh/30 menit | Konsumsi yang telah diketahui pada waktu prediksi | Fitur one-step-ahead dan baseline persistence | Diambil dari pengukuran saat ini |
| `energy_lag_1/2/4/48` | Numerik kWh/30 menit | Riwayat pada jumlah interval tertulis sebelumnya | Fitur | Dibuat dalam grup `LCLid`; tidak mengisi nilai masa depan |
| `energy_roll_mean/std_4/48` | Numerik kWh/30 menit | Statistik interval sebelumnya | Fitur | Pergeseran satu interval ke masa lalu sebelum rolling |
| `target_energy_kwh` | Numerik kWh/30 menit | Energi observasi berikutnya pada ID sama | Label supervised | Baris valid hanya jika timestamp target persis 30 menit kemudian |
| `hour_sin/cos`, `weekday_sin/cos` | Numerik tanpa satuan | Siklus waktu | Fitur waktu | Transformasi sinus/cosinus timestamp saat ini |

Dataset London tidak menyediakan `Voltage`, `Global_intensity`, ataupun daya kW. Energi interval sudah dalam kWh, sehingga untuk total konsumsi nilainya dijumlahkan tanpa dikalikan 0,5 lagi.
