# Asal dan cakupan data

## Sumber utama

Publisher pada London Datastore adalah Greater London Authority; pengumpulan berasal dari UK Power Networks melalui Low Carbon London. Dataset penuh berisi sekitar 167 juta observasi setengah jam untuk sekitar 5.567 rumah tangga antara November 2011 dan Februari 2014. London Datastore menyebut lisensi Creative Commons Attribution. DOI tidak tercantum di laman sumber yang diperiksa.

Eksperimen ini memakai file lokal `data/raw/LCL-June2015v2_0.csv`, sebuah potongan satu juta baris dari dataset London penuh. File ini mempunyai ID rumah tangga teracak, jenis pelanggan, waktu, dan energi kWh per interval 30 menit. File yang dianalisis tidak mewakili seluruh 167 juta observasi.

File mentah disalin dari workspace tanpa perubahan. SHA-256 salinan dibandingkan dengan sumber lokal: `LCL-June2015v2_0.csv` `4997141df1efb62488305936c3d2aee395c456f475542bfbdcd5a2145479bd61`; `Tariffs.xlsx` `8a2eff6dcb737aee96cfa6c357d2947604d7f812896405c2ab5f98433d2cb150`. Audit terbaru adalah `outputs/data_quality_report.json`.

## Data pendamping

`data/raw/Tariffs.xlsx` diaudit pada semua sheet. Sheet1 berisi jadwal Normal, Low, dan High pada 2013. CSV lokal hanya memuat pelanggan Std, sehingga label tarif ToU tidak ditempelkan pada baris lokal. Jadwal tidak berisi harga rupiah per kWh.

## Representativitas

London berbeda dari Surabaya dalam cuaca, bentuk bangunan, perangkat, perilaku penghuni, tarif, dan pola sewa. CSV hanya berisi konsumsi energi, bukan arus, tegangan, hunian, cuaca, maupun identitas ruang yang dapat ditautkan. Dataset menjadi bukti eksperimen forecast pada subset London; pengujian pada kos Indonesia tetap diperlukan.

## Graf pencarian

Graf lorong dan kamar pada `outputs/bfs_result.json` dibuat khusus sebagai contoh algoritma BFS. Graf sintetis ini bukan observasi sensor maupun denah kos nyata.
