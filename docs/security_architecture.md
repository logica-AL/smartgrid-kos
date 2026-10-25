# Rancangan keamanan dan akses

Desain memakai RBAC. Penghuni hanya melihat catatan kamar sendiri; admin melihat agregat dan data operasional sesuai kewenangan; teknisi menerima status minimum yang diperlukan. ID ruang pada dashboard menggunakan pseudonim. Pengelola harus menjelaskan masa retensi, tujuan pemakaian, dan prosedur penghapusan data.

Setiap perangkat atau layanan memakai kredensial unik berhak minimum. Simpan secret di environment/secret manager, bukan di Git; sediakan rotasi dan pencabutan. Gunakan HTTPS/TLS atau MQTT over TLS, autentikasi dan otorisasi API, logging perubahan akses, backup terenkripsi, serta pembatasan ekspor data.

Alur respons yang diusulkan: sistem mencatat flag dan skor, penghuni/admin meninjau konteks, lalu teknisi memeriksa bila diperlukan. Tidak ada relay pemutus otomatis. Smart meter adalah sensor konseptual; implementasi perangkat, audit keamanan, dan penetration test belum dilakukan.
