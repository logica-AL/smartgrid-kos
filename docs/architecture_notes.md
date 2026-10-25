# Catatan arsitektur Smart Grid

- **Power-system:** suplai jaringan, panel distribusi kos, sirkuit cabang, dan beban kamar.
- **Power-flow:** titik meter konseptual mengukur energi per interval. Dataset London menyediakan energi interval dan kategori pelanggan, bukan arus/tegangan.
- **Information:** HAN/LAN ke gateway/router dan WAN; ingesti, validasi, API, penyimpanan, analitik, dashboard, dan notifikasi.

Alur operasional: physical world → sensing → connectivity → analytics → decision/action. Penerima notifikasi adalah penghuni terkait dan admin; teknisi ikut bila tinjauan memerlukan pemeriksaan. Pengguna manusia mengambil keputusan. Ambang notifikasi tinggi diturunkan dari persentil train dan hanya menjadi pembanding historis, bukan batas keselamatan instalasi.
