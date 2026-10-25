# Metodologi eksperimen

1. Baca CSV lokal, catat header sumber, lalu normalkan nama kolom dengan `strip()`. Parse `DateTime`, konversi energi menggunakan `to_numeric(errors='coerce')`, hitung nilai nol valid dan nilai kosong/gagal secara terpisah.
2. Urutkan per `LCLid` dan timestamp. Hapus duplikat pasangan ID-waktu dengan kebijakan retain-first yang dicatat di audit. Energi yang hilang tetap NaN. Interval yang melintasi timestamp tidak berurutan tidak diperlakukan sebagai 30 menit.
3. Label untuk contoh pada waktu `t` adalah energi baris berikutnya hanya apabila ID sama dan timestamp baris berikutnya tepat `t + 30 menit`. Pola pengukuran berurutan berdasarkan posisi saja tidak cukup.
4. Fitur meliputi energi saat ini, lag 1/2/4/48 interval pada ID yang sama, perubahan dari interval sebelumnya, rolling mean/std 4 dan 48 interval dari timestamp historis tepat, serta encoding siklik jam dan hari. Setiap lag memakai pencarian timestamp aktual; baris sebelumnya yang berjarak tidak tepat 30 menit tidak dianggap sebagai lag interval. Semua ringkasan histori berakhir pada t-30 menit.
5. Bagi waktu unik global secara kronologis menjadi 70% train, 15% validation, 15% test. Label dibatasi agar masuk ke periode split yang sama dengan fitur, mencegah target train melewati batas berikutnya.
6. Latih `sklearn.linear_model.LinearRegression` hanya pada train. Persistence memprediksi energi berikutnya memakai energi saat ini pada ID yang sama. Bandingkan MAE, RMSE, dan R² pada observasi test yang identik.
7. Latih Isolation Forest hanya pada sampel train yang diambil deterministik menggunakan seed 42 dan batas konfigurasi 100.000 contoh; skor seluruh test pada contamination 0,005, 0,01, dan 0,02. Tidak ada label insiden untuk menguji akurasi klasifikasi.
8. Hitung konsumsi per pasangan rumah-bulan dengan menjumlahkan kWh interval valid. Skenario biaya memakai rata-rata kWh rumah-bulan dikali tarif asumsi. Skenario 0%, 5%, dan 10% adalah simulasi penerapan tarif Indonesia pada pola energi London.

Artefak uji: `tests/test_target_alignment.py`, `tests/test_cost_calculation.py`, `tests/test_energy_calculation.py`, dan `tests/test_data_audit.py`. Perintah yang dijalankan tercatat di README.
