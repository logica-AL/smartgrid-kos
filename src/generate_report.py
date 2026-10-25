"""Generate editable ETS A-C draft from outputs/report_facts.json."""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

NAVY="203B5B"; PALE="EAF1F7"; BORDER="C7D2DE"; BLACK="000000"

def idr(n): return "Rp"+format(float(n),",.0f").replace(",",".")
def nfmt(n,d=3): return format(float(n),f",.{d}f").replace(",","X").replace(".",",").replace("X",".")
def cell_shading(cell,fill):
    tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement("w:shd"); shd.set(qn("w:fill"),fill); tcPr.append(shd)
def cell_margins(cell,top=90,start=110,bottom=90,end=110):
    tc=cell._tc; tcPr=tc.get_or_add_tcPr(); mar=tcPr.first_child_found_in("w:tcMar")
    if mar is None: mar=OxmlElement("w:tcMar"); tcPr.append(mar)
    for tag,val in (("top",top),("start",start),("bottom",bottom),("end",end)):
        el=mar.find(qn("w:"+tag))
        if el is None: el=OxmlElement("w:"+tag); mar.append(el)
        el.set(qn("w:w"),str(val)); el.set(qn("w:type"),"dxa")
def table_borders(table):
    pr=table._tbl.tblPr; borders=OxmlElement("w:tblBorders")
    for edge in ("top","left","bottom","right","insideH","insideV"):
        e=OxmlElement("w:"+edge); e.set(qn("w:val"),"single"); e.set(qn("w:sz"),"5"); e.set(qn("w:color"),BORDER); borders.append(e)
    pr.append(borders)
def set_repeat_table_header(row):
    trPr=row._tr.get_or_add_trPr(); el=OxmlElement("w:tblHeader"); el.set(qn("w:val"),"true"); trPr.append(el)
TABLE_COUNT = 0
def add_table(doc,headers,rows,widths=None,font_size=8.5):
    global TABLE_COUNT
    TABLE_COUNT += 1
    add_caption(doc,f"Tabel {TABLE_COUNT}. Ringkasan {headers[0].lower()}.")
    table=doc.add_table(rows=1,cols=len(headers)); table.alignment=WD_TABLE_ALIGNMENT.CENTER; table.autofit=False
    for i,h in enumerate(headers):
        cell=table.rows[0].cells[i]; cell.text=str(h); cell_shading(cell,NAVY); cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER; cell_margins(cell)
        for r in cell.paragraphs[0].runs: r.font.bold=True; r.font.color.rgb=RGBColor(255,255,255); r.font.size=Pt(font_size)
    set_repeat_table_header(table.rows[0])
    for row in rows:
        cells=table.add_row().cells
        for i,val in enumerate(row):
            cells[i].text=str(val); cells[i].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER; cell_margins(cells[i])
            if len(table.rows)%2==0: cell_shading(cells[i],"F4F7FA")
            for p in cells[i].paragraphs:
                p.paragraph_format.space_after=Pt(0)
                for run in p.runs: run.font.size=Pt(font_size); run.font.name="Arial"
    if widths:
        for row in table.rows:
            for i,w in enumerate(widths): row.cells[i].width=Inches(w)
    table_borders(table); doc.add_paragraph().paragraph_format.space_after=Pt(1)
    return table
def add_caption(doc,text):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(6)
    r=p.add_run(text); r.italic=True; r.font.size=Pt(8.5); r.font.color.rgb=RGBColor(70,84,100)
def add_image(doc,path,width,caption):
    doc.add_picture(str(path),width=Inches(width)); doc.paragraphs[-1].alignment=WD_ALIGN_PARAGRAPH.CENTER; add_caption(doc,caption)
def add_para(doc,text,style=None,after=6):
    p=doc.add_paragraph(style=style); p.paragraph_format.space_after=Pt(after); p.paragraph_format.line_spacing=1.08; p.add_run(text); return p
def add_heading(doc,text,level=1):
    p=doc.add_heading(text,level=level)
    for run in p.runs: run.font.color.rgb=RGBColor(0,0,0)
    p.paragraph_format.keep_with_next=True
    return p
def page(doc): doc.add_page_break()
def add_page_field(p):
    p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    r=p.add_run("Halaman "); r.font.size=Pt(8)
    fld=OxmlElement("w:fldSimple"); fld.set(qn("w:instr"),"PAGE"); p._p.append(fld)
def hyperlink(p,text,url):
    part=p.part; rid=part.relate_to(url,"http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",is_external=True)
    h=OxmlElement("w:hyperlink"); h.set(qn("r:id"),rid); r=OxmlElement("w:r"); pr=OxmlElement("w:rPr"); col=OxmlElement("w:color"); col.set(qn("w:val"),"0563C1"); pr.append(col); und=OxmlElement("w:u"); und.set(qn("w:val"),"single"); pr.append(und); r.append(pr); t=OxmlElement("w:t"); t.text=text; r.append(t); h.append(r); p._p.append(h)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--facts",default="outputs/report_facts.json"); args=ap.parse_args()
    root=Path.cwd(); f=json.loads((root/args.facts).read_text(encoding="utf-8")); rep=root/"reports"; rep.mkdir(exist_ok=True)
    doc=Document(); sec=doc.sections[0]; sec.page_width=Inches(8.27); sec.page_height=Inches(11.69); sec.top_margin=Inches(.68); sec.bottom_margin=Inches(.68); sec.left_margin=Inches(.78); sec.right_margin=Inches(.78)
    styles=doc.styles
    normal=styles["Normal"]; normal.font.name="Arial"; normal.font.size=Pt(9.5); normal.font.color.rgb=RGBColor(0,0,0); normal.paragraph_format.space_after=Pt(5)
    for name,size in (("Title",26),("Heading 1",16),("Heading 2",12),("Heading 3",10)):
        s=styles[name]; s.font.name="Arial"; s.font.size=Pt(size); s.font.bold=True; s.font.color.rgb=RGBColor(0,0,0)
    header=sec.header.paragraphs[0]; header.text="ETS TEKNOLOGI BERBASIS KOMPUTER  |  DRAF LAPORAN A-C"; header.runs[0].font.size=Pt(7.5); header.runs[0].font.color.rgb=RGBColor(80,95,110)
    footer=sec.footer.paragraphs[0]; footer.add_run(f"{f['identity']['nrp']}  •  DRAFT  •  ").font.size=Pt(8); add_page_field(footer)
    src={s["id"]:s for s in f["sources"]}; srcnum={sid:str(i+1) for i,sid in enumerate(src.keys())}
    def cite(*ids): return " ".join(f"[{srcnum[i]}]" for i in ids)
    m=f["experiment"]; q=f["dataset"]; qdetail=q["quality"]; by={r["model"]:r for r in m["metrics_test"]}
    base=by["persistence_same_household"]; lr=by["linear_regression"]; split=m["splits"]; ano=f["anomalies"]["sensitivity"]; costs=f["cost_scenarios"]
    # Page 1: title
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(82)
    r=p.add_run("LAPORAN ETS\nTEKNOLOGI BERBASIS KOMPUTER"); r.bold=True; r.font.name="Arial"; r.font.size=Pt(16)
    p=doc.add_paragraph(style="Title"); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(38)
    p.add_run(f["title"])
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(26)
    rr=p.add_run("STATUS DRAFT | BAGIAN A-C"); rr.bold=True; rr.font.size=Pt(14); rr.font.color.rgb=RGBColor(145,65,25)
    add_para(doc,"Dataset eksperimen: smart meter rumah tangga London, interval setengah jam",after=18).alignment=WD_ALIGN_PARAGRAPH.CENTER
    add_para(doc,f"Disusun oleh\n{f['identity']['name']}\nNRP {f['identity']['nrp']}\nMata kuliah Teknologi Berbasis Komputer\nSemester {f['identity']['term']}",after=6).alignment=WD_ALIGN_PARAGRAPH.CENTER
    page(doc)
    # Page 2: abstract
    add_heading(doc,"Ringkasan",1)
    add_para(doc,"Laporan ini menguji rancangan pemantauan energi untuk konteks kos mahasiswa di Surabaya menggunakan satu potongan dataset smart meter London. Eksperimen memakai nilai energi kWh per interval setengah jam; data tidak memuat tegangan atau arus. Tujuan prediksi adalah energi pada interval tepat berikutnya untuk rumah yang sama. Surabaya adalah konteks penerapan konseptual, bukan tempat pengambilan data.")
    add_para(doc,f"Dari {q['local_rows']:,} baris lokal, {q['valid_energy_rows']:,} memiliki nilai energi numerik setelah penanganan timestamp duplikat. Model uji mencakup {lr['observations']:,} contoh. Linear Regression memperoleh MAE {nfmt(lr['MAE_kWh_per_30min'])}, RMSE {nfmt(lr['RMSE_kWh_per_30min'])}, dan R² {nfmt(lr['R2'])}. Persistence memperoleh MAE {nfmt(base['MAE_kWh_per_30min'])}, RMSE {nfmt(base['RMSE_kWh_per_30min'])}, dan R² {nfmt(base['R2'])}. Persistence memiliki MAE lebih rendah, sedangkan regresi memiliki RMSE dan R² lebih tinggi.")
    add_para(doc,"Isolation Forest menandai pola konsumsi tidak biasa pada test. Dataset tidak menyediakan label kejadian yang terverifikasi, sehingga hasil memerlukan tinjauan manusia. Skenario biaya menggunakan rata-rata konsumsi household-bulan London dikalikan asumsi tarif Indonesia dan bukan tagihan aktual.")
    add_para(doc,"Batas dokumen: materi lokal hanya merinci Bagian A-C. Bagian D-E belum dapat diisi tanpa rubrik dosen/LMS. Nama mahasiswa dan URL video juga masih berupa placeholder. Karena itu dokumen tetap DRAFT.")
    add_heading(doc,"Kata kunci",2); add_para(doc,"Smart grid, smart meter, kos mahasiswa, energi kWh, Linear Regression, Isolation Forest")
    page(doc)
    # Page 3: TOC and figure list
    add_heading(doc,"Daftar isi",1)
    for item in ["Ringkasan","Bagian A. Masalah, inovasi, nilai, dan dampak","Bagian B. Desain dan arsitektur sistem IoT","Bagian C. Data dan inti AI","Analisis agen, lingkungan, dan pencarian","Kesimpulan","Daftar pustaka","Lampiran. Status Bagian D-E"]:
        add_para(doc,item,after=2)
    add_heading(doc,"Daftar gambar",2)
    for item in ["Gambar 1. Arsitektur tiga lapis Smart Grid yang diusulkan","Gambar 2. Aktual dan prediksi pada data test","Gambar 3. Distribusi residual test","Gambar 4. Contoh deret waktu test","Gambar 5. Contoh flag Isolation Forest","Gambar 6. Skenario biaya rata-rata household-bulan"]: add_para(doc,item,after=1)
    page(doc)
    # Page 4: Part A problem / stakeholders
    add_heading(doc,"Bagian A  Masalah, inovasi, nilai, dan dampak",1)
    add_heading(doc,"Masalah dan konteks",2)
    add_para(doc,f"Penelitian pada rumah kos di Indonesia menjelaskan bahwa pembagian tagihan yang sama dapat terasa tidak sebanding ketika pemakaian tiap kamar berbeda. Studi yang berafiliasi dengan Universitas Negeri Surabaya juga menyoroti kebutuhan pemantauan energi dan tagihan dari jarak jauh. Temuan publik tersebut memberi konteks masalah; laporan ini tidak melakukan survei atau audit di Keputih maupun kos tertentu di Surabaya. {cite('S4')}")
    add_para(doc,"Skenario rancangan adalah kos dengan beberapa kamar dan satu atau beberapa titik meter. Penghuni memerlukan catatan yang mudah dipahami, sedangkan pengelola memerlukan dasar transparan untuk memeriksa pola konsumsi dan menyusun perkiraan biaya. Ketidaksepakatan soal pembagian biaya, beban menyala saat kamar kosong, dan keterlambatan mengetahui perubahan konsumsi adalah masalah yang akan diuji pada tahap penerapan lokal.")
    add_heading(doc,"Pemangku kepentingan",2)
    add_table(doc,["Pihak","Kebutuhan dalam rancangan"],[["Penghuni","Melihat energi dan perkiraan biaya kamar sendiri; menerima peringatan yang dapat ditinjau."],["Pemilik/admin","Melihat ringkasan dan mengelola pembagian biaya sesuai kesepakatan penghuni."],["Teknisi","Memeriksa status perangkat/jaringan dengan akses minimum."],["Penyedia listrik","Relevan untuk tarif/aturan meter; bukan operator dashboard kos."]],[1.4,5.4],9)
    add_para(doc,"Kontribusi eksperimen ini adalah membandingkan prediksi one-step-ahead dengan baseline persistence pada sampel London, serta menambahkan deteksi pola tidak biasa. Manfaat untuk kos Surabaya masih berupa rancangan yang perlu diuji dengan data dan aturan tarif setempat.")
    page(doc)
    # Page 5: prior work comparison
    add_heading(doc,"Solusi terdahulu",1)
    add_heading(doc,"Monitoring dan pembagian tagihan",2)
    add_para(doc,f"Kusumah, Jayusman, dan Hakim (2023) merancang pemantauan IoT menggunakan ESP8266 dan sensor PZEM-004T. Data dikirim ke server dan website menampilkan grafik pemakaian serta jumlah tagihan tiap kamar. Artikel menempatkan pembagian yang sama saat konsumsi berbeda sebagai masalah utama. Artikel membuktikan rancangan monitoring dan pembagian biaya; abstraknya tidak melaporkan model forecast atau deteksi anomali. Harga perangkat tidak dinyatakan, sehingga laporan ini tidak menambahkan estimasi biaya perangkat. {cite('S3')}")
    add_heading(doc,"Monitoring dan kendali daya",2)
    add_para(doc,f"Haryudo, Alfian, dan Kholis (2021) membangun alat berbasis NodeMCU ESP8266, PZEM-004T, relay, LCD, RTC, dan Blynk untuk memantau energi serta biaya dan mengendalikan daya. Pengujian yang dilaporkan mencatat error tegangan rata-rata 1,4% dan arus 3,7%; pengujian sampel beban selama 150 menit menggunakan 0,175 kWh dan menghasilkan biaya Rp246. Angka tersebut adalah hasil penelitian terdahulu, bukan hasil proyek ini. Harga komponennya tidak tersedia di artikel yang ditelaah. {cite('S4')}")
    add_table(doc,["Aspek","Solusi 1","Solusi 2","Rancangan laporan"],[["Fokus","Grafik konsumsi dan tagihan kamar","Monitoring dan kendali relay","Forecast energi dan flag anomali, selain monitoring"],["Konektivitas/alat","ESP8266, PZEM-004T, server, website","NodeMCU, PZEM, relay, LCD, RTC, Blynk","Smart meter konseptual, pipeline, dashboard/notifikasi"],["Batas","Tidak dijelaskan forecast/anomali di abstrak","Mengendalikan daya; berisiko mengintervensi beban","Tidak memutus daya otomatis; perlu data kamar lokal"],["Harga perangkat","Tidak dilaporkan","Tidak dilaporkan","Tidak dihitung tanpa sumber harga"]],[.8,2.0,2.0,2.0],7.7)
    page(doc)
    # Page 6: innovation and impacts
    add_heading(doc,"Solusi yang diusulkan dan nilai dampak",1)
    add_para(doc,"Rancangan menggabungkan pemantauan smart meter, Linear Regression untuk memprediksi kWh interval selanjutnya, Isolation Forest untuk menandai pola tidak biasa, dan dashboard/peringatan yang ditinjau manusia. Pada prototipe perangkat lunak tidak ada relay pemutus listrik. Kemampuan perkiraan dan manfaat operasional harus divalidasi di lokasi sebelum dipakai untuk keputusan biaya atau intervensi.")
    impact_rows=[["Teknis",f"Test n={lr['observations']:,}. MAE/RMSE/R² tersedia dalam Bagian C. Data freshness konsep mengikuti interval 30 menit; latency implementasi belum diukur."],
      ["Ekonomi",f"Skenario dasar {nfmt(costs[0]['mean_household_month_kwh'],2)} kWh per household-bulan dan {idr(costs[0]['estimated_cost_idr_per_household_month'])} memakai tarif asumsi Indonesia. Ini bukan tagihan kos."],
      ["Sosial","Tampilan per kamar dapat mendukung transparansi dan diskusi penghuni-pengelola. ID harus dipseudonimkan; manfaat penerimaan pengguna belum dievaluasi."],
      ["Lingkungan",f"Reduksi energi 5%/10% hanya skenario. Faktor emisi yang cocok dan tervalidasi untuk perhitungan ini tidak tersedia, sehingga CO2 tidak dihitung."]]
    add_table(doc,["Dimensi","Bukti dan batas dampak"],impact_rows,[1.2,5.6],9)
    add_para(doc,"Harga sensor, gateway, instalasi, jaringan, dan pemeliharaan tidak dihitung. Dua penelitian pembanding yang ditelaah tidak memberi daftar harga yang memadai untuk membuat rentang rupiah yang dapat diverifikasi. Nilai ekonomi di atas hanya menggunakan rumus energi × tarif asumsi, bukan manfaat kausal dari sistem.")
    page(doc)
    # Page 7: architecture
    add_heading(doc,"Bagian B  Desain dan arsitektur sistem IoT",1)
    add_para(doc,"Arsitektur mengikuti alur physical world → sensing → connectivity → analytics → decision/action. Pada eksperimen lokal, sumbernya adalah data smart meter London. Pada penerapan kos, smart meter per kamar adalah komponen konseptual yang memerlukan pengadaan, kalibrasi, dan persetujuan penghuni.")
    add_image(doc,root/"outputs/figures/Arsitektur_SmartGrid_Kos_Mahasiswa_LONDON.png",6.65,"Gambar 1. Arsitektur tiga lapis yang diusulkan. Dataset eksperimen hanya menyediakan energi interval, ID, waktu, dan kategori pelanggan.")
    add_para(doc,"Dashboard menampilkan energi interval dan ringkasan yang dapat ditelusuri. Peringatan memberi sinyal untuk pemeriksaan manual; penghuni/admin menilai konteks sebelum teknisi dilibatkan.")
    page(doc)
    # Page 8: layers and alert
    add_heading(doc,"Tiga lapisan dan alur peringatan",1)
    add_table(doc,["Lapisan","Komponen rancangan","Data/aksi"],[["Power-system","Jaringan PLN, panel distribusi, sirkuit dan beban kamar","Aliran daya fisik. Tidak ada perintah proteksi otomatis dari model."],["Power-flow","Smart meter/titik ukur konseptual","Energi interval kWh. CSV London tidak memuat tegangan atau arus."],["Information","HAN/LAN, gateway/router, WAN, API, penyimpanan, analitik, dashboard","Kirim data, validasi, prediksi, flag pola, log dan notifikasi."]],[1.1,2.65,3.05],8.4)
    add_heading(doc,"Ambang dan penanganan",2)
    thr=qdetail["high_energy_reference"]; add_para(doc,f"Acuan konsumsi tinggi ditetapkan sebagai persentil {nfmt(thr['percentile']*100,0)} energi interval dari data train. Nilai aktual ambang adalah {nfmt(thr['threshold_kwh_per_30min'],4)} kWh/30 menit. Ambang ini menggambarkan histori sampel dan bukan standar keselamatan instalasi. Batas proteksi listrik harus mengikuti spesifikasi panel, kabel, MCB, serta aturan teknis yang berlaku.")
    add_para(doc,"Urutan notifikasi yang diusulkan: rekam data dan waktu, tampilkan alasan flag, beri tahu penghuni kamar terkait dan admin, minta konfirmasi konteks, lalu eskalasi teknisi jika diperlukan. Sistem tidak boleh memutus aliran listrik secara otomatis.")
    page(doc)
    # Page 9: security
    add_heading(doc,"Kontrol akses, keamanan, dan privasi",1)
    add_para(doc,"Data konsumsi dapat mengungkap pola hunian. Desain membatasi akses berdasarkan kebutuhan operasional dan memisahkan identitas penghuni dari ID pada analitik.")
    add_table(doc,["Peran","Hak minimum"],[["Penghuni","Melihat pengukuran, prediksi, dan notifikasi kamar sendiri."],["Admin kos","Mengelola kamar dan melihat agregat/tagihan sesuai kewenangan serta persetujuan."],["Teknisi","Melihat status perangkat/jaringan yang diperlukan untuk perbaikan."],["Layanan AI","Kredensial mesin-ke-mesin dengan izin baca terbatas pada fitur yang diperlukan."]],[1.3,5.5],9)
    add_para(doc,"Gunakan HTTPS/TLS atau MQTT over TLS, autentikasi API, kunci unik per perangkat/layanan, secret manager atau environment, rotasi dan pencabutan kunci, logging akses, backup terenkripsi, retensi terbatas, dan pseudonymous room ID. Buat prosedur pencabutan kredensial, isolasi perangkat, investigasi log, dan pemberitahuan insiden sesuai kewajiban yang berlaku.")
    add_para(doc,"Keamanan di atas adalah rancangan dokumentasi. Proyek ini tidak memasang perangkat, memproses data penghuni kos, mengaudit sistem, atau menjalankan penetration test. Model hanya membantu pemantauan; teknisi/manusia tetap menentukan tindakan.")
    page(doc)
    # Page 10: C data audit
    add_heading(doc,"Bagian C  Data dan inti AI",1)
    add_heading(doc,"Metadata dan audit lokal",2)
    add_para(doc,f"Sumber: {q['publisher']}. File analisis: `{q['local_file']}`. Laman London Datastore menjelaskan rilis penuh sekitar {q['full_release_rows_approx']:,} baris; file lokal adalah potongan yang diberikan, bukan rilis penuh. Lisensi dicantumkan sebagai Creative Commons Attribution; DOI tidak tercantum pada laman yang diperiksa. {cite('S1','S2')}")
    add_table(doc,["Pemeriksaan","Hasil audit"],[["Baris mentah",f"{q['local_rows']:,}"],["Baris setelah timestamp valid dan deduplikasi",f"{q['quality']['rows_after_timestamp_and_duplicate_cleaning']:,}"],["Energi numerik valid",f"{q['valid_energy_rows']:,}"],["ID household",str(q['unique_households'])],["Kategori pelanggan",", ".join(q['customer_categories'].keys())],["Periode",f"{q['timestamp_min']} sampai {q['timestamp_max']}"],["Energi hilang/tidak numerik",f"{q['energy_missing_or_invalid']:,}"],["Timestamp (LCLid, DateTime) duplikat dihapus",f"{q['duplicate_household_timestamps_removed']:,}"],["Nilai nol yang dipertahankan",f"{q['valid_zero_energy']:,}"]],[2.6,4.2],8.7)
    ta=f['tariffs']; sh=ta['sheets']; sheet1=sh['Sheet1']; categories=sheet1['categories']
    add_para(doc,f"Workbook Tariffs.xlsx diperiksa seluruh sheet: Sheet1 memiliki {sheet1['rows']:,} baris, kolom {', '.join(sheet1['columns'])}, periode {sheet1['timestamp_min']} sampai {sheet1['timestamp_max']}, kategori {', '.join(f'{k}={v:,}' for k,v in categories.items())}; Sheet2 dan Sheet3 kosong. Workbook tidak memuat tarif rupiah per kWh. Karena sampel lokal hanya berkategori {', '.join(q['customer_categories'].keys())}, jadwal ToU ini tidak digabung ke baris konsumen Std. Header CSV mentah memiliki spasi akhir pada nama kolom energi; nama dibersihkan dengan strip dan kedua bentuk dicatat. Nilai energi hilang tidak diubah menjadi nol. Ada interval selain 30 menit dan timestamp duplikat. Lihat `outputs/household_frequency.csv` untuk frekuensi per rumah.")
    page(doc)
    # Page 11: fit method
    add_heading(doc,"Target, fitur, dan pemisahan waktu",1)
    add_para(doc,"Untuk pengamatan (LCLid, t), target E(t+1) diterima hanya bila baris berikut untuk LCLid yang sama bertimestamp tepat t+30 menit dan energinya tersedia. Ini adalah prediksi one-step-ahead: pembacaan pada t sudah diketahui ketika membuat prediksi interval berikutnya.")
    add_para(doc,"Fitur memasukkan energi saat ini, lag 1/2/4/48 interval, perubahan dari interval sebelumnya, rolling mean/std 4 dan 48 interval yang digeser ke masa lalu, serta siklus jam dan hari. LCLid hanya dipakai sebagai kunci grup dan bukan bilangan kontinu. Gap timestamp, nilai kosong dalam fitur, dan target tidak tepat +30 menit menggugurkan contoh. DST ditangani melalui timestamp yang tercatat; waktu lokal naive tidak ditafsirkan sebagai interval tetap jika terdapat gap atau duplikasi.")
    add_table(doc,["Split kronologis","Contoh valid","Waktu fitur"],[["Train",f"{split['train']['observations']:,}",f"{split['train']['timestamp_min']} - {split['train']['timestamp_max']}"],["Validation",f"{split['validation']['observations']:,}",f"{split['validation']['timestamp_min']} - {split['validation']['timestamp_max']}"],["Test",f"{split['test']['observations']:,}",f"{split['test']['timestamp_min']} - {split['test']['timestamp_max']}"]],[1.2,1.4,4.2],8)
    add_para(doc,"Waktu unik global dibagi 70/15/15 tanpa shuffle. Label tiap split dibatasi agar tidak melewati akhir periode splitnya. Linear Regression fit hanya di train. Validation dicatat untuk pemeriksaan, dan metrik test dilaporkan pada satu himpunan observasi bersama baseline.")
    page(doc)
    # Page 12: regression results
    add_heading(doc,"Hasil regresi dan baseline",1)
    result_rows=[]
    for key,label in (("persistence_same_household","Persistence E(t)"),("linear_regression","Linear Regression")):
        r=by[key]; result_rows.append([label,nfmt(r["MAE_kWh_per_30min"],5),nfmt(r["RMSE_kWh_per_30min"],5),nfmt(r["R2"],5),f"{r['observations']:,}"])
    add_table(doc,["Model","MAE kWh/30m","RMSE kWh/30m","R²","n test"],result_rows,[1.85,1.25,1.35,1.0,.9],8.1)
    add_para(doc,"Persistence memakai energi interval t untuk memprediksi energi interval berikutnya pada LCLid yang sama. Hasil menunjukkan persistence memiliki MAE lebih rendah. Linear Regression memiliki RMSE lebih rendah dan R² lebih tinggi. Karena metrik memberi gambaran berbeda, pemilihan model perlu mempertimbangkan biaya kesalahan dan kebutuhan operasional, bukan menyatakan regresi selalu lebih baik.")
    add_image(doc,root/"outputs/figures/actual_vs_predicted.png",6.25,"Gambar 2. Energi aktual dan prediksi Linear Regression pada urutan observasi test.")
    add_para(doc,"MAE dan RMSE berada dalam kWh per interval 30 menit. R² membandingkan variasi prediksi dengan nilai aktual pada split uji yang sama. Hasil satu sampel London ini belum menguji generalisasi ke Surabaya.")
    page(doc)
    # Page 13: residual and series
    add_heading(doc,"Pemeriksaan residual dan deret waktu",1)
    add_para(doc,"Residual dihitung sebagai aktual dikurangi prediksi. Distribusinya membantu melihat besar kesalahan dan nilai ekstrem. Gambar deret waktu memberikan contoh lokal pada test; satu cuplikan tidak mewakili seluruh variasi 30 household.")
    add_image(doc,root/"outputs/figures/residuals.png",5.7,"Gambar 3. Distribusi residual pada data test, dalam kWh per interval 30 menit.")
    add_image(doc,root/"outputs/figures/time_series_example.png",5.7,"Gambar 4. Contoh aktual dan prediksi pada rentang test.")
    page(doc)
    # Page 14: anomaly
    add_heading(doc,"Isolation Forest dan pola tidak biasa",1)
    add_para(doc,f"Isolation Forest dilatih hanya menggunakan sampel train berukuran {f['anomalies']['fit_sample_rows']:,} dengan random state {f['anomalies']['random_state']}. Sampel dipakai untuk membatasi waktu dan memori; seluruh {f['anomalies']['test_rows']:,} baris test diberi skor.")
    rows=[]
    for c,v in ano.items(): rows.append([c,f"{v['flagged_count']:,}",f"{nfmt(v['flagged_percent'],3)}%",nfmt(v['decision_score_threshold'],4),f"{nfmt(v['score_min'],3)}; {nfmt(v['score_median'],3)}; {nfmt(v['score_max'],3)}"])
    add_table(doc,["Contamination","Flag test","Persentase","Ambang skor","Min; median; maks skor"],rows,[1.05,1.05,1.15,1.25,2.6],7.7)
    add_image(doc,root/"outputs/figures/anomaly_example.png",6.05,"Gambar 5. Pengukuran test dan flag contoh pada contamination 1%.")
    examples=ano.get("0.01",{}).get("examples",[])[:3]
    if examples:
        add_para(doc,"Contoh bertimestamp ditampilkan menggunakan ID rumah tangga yang dipseudonimkan:")
        add_table(doc,["Timestamp","ID pseudonim","Energi kWh/30 menit"],[[x["timestamp"],x["household_pseudonym"],nfmt(x["energy_kwh_per_30min"],4)] for x in examples],[3.0,1.65,2.45],7.6)
    add_para(doc,"Contamination adalah hyperparameter sensitivitas, bukan taksiran kejadian rusak. Sampel tidak memiliki label insiden; precision, recall, dan akurasi terhadap ground truth tidak dihitung. Admin perlu memeriksa tren, kualitas sensor, dan konteks pemakaian.")
    page(doc)
    # Page 15: economics and limitations
    add_heading(doc,"Skenario biaya dan batas ekonomi",1)
    econ=f["experiment"].get("mean_household_month_energy_kwh",0); rate=costs[0]["tariff_idr_per_kwh"]
    add_para(doc,f"Tarif rupiah dipakai sebagai asumsi penerapan Indonesia untuk pelanggan rumah tangga R-1/TR 1.300 VA, sebesar Rp{rate:,.2f}/kWh. PLN memuat nilai tarif rumah tangga 1.300 VA tersebut; ESDM menyatakan tarif triwulan IV 2026 bagi pelanggan nonsubsidi tidak berubah dari triwulan III. Tarif kos dapat berbeda karena golongan, daya, pajak daerah, biaya admin, atau kesepakatan pemilik. {cite('S6','S9')}")
    rows=[[f"{int(x['reduction_percent'])}%",nfmt(x["mean_household_month_kwh"],2),idr(x["estimated_cost_idr_per_household_month"])] for x in costs]
    add_table(doc,["Reduksi simulasi","Energi rata-rata kWh/household-bulan","Biaya skenario"],rows,[1.35,3.0,2.75],8.5)
    add_image(doc,root/"outputs/figures/cost_scenarios.png",5.7,"Gambar 6. Estimasi per household-bulan; energi London dikalikan asumsi tarif Indonesia.")
    add_para(doc,"Nilai tersebut adalah simulasi atas energi rata-rata household-bulan dalam subset London, bukan tagihan kos Surabaya atau penghematan yang tercapai. Konsumsi per interval sudah dalam kWh; energi total tidak dikalikan 0,5. Tidak ada konversi ke GBP karena fokus skenario rupiah dan bukan penagihan London. Biaya perangkat belum dihitung karena tidak ada sumber harga dan tanggal yang dapat diverifikasi.")
    page(doc)
    # Appendix: agents and BFS
    add_heading(doc,"Analisis agen, lingkungan, dan pencarian",1)
    add_para(doc,"Sistem konseptual adalah learning agent dengan komponen berbasis aturan. Simple reflex menggunakan ambang konsumsi; model-based memakai status dan riwayat; goal-based memandu target pemeriksaan; utility-based menimbang manfaat, biaya, dan kenyamanan; learning agent memakai regresi dan Isolation Forest. Kategori ini menjelaskan desain, bukan lima model terpisah.")
    add_para(doc,"Lingkungan bersifat partially observable, stochastic, dan dynamic. Nilai energi kontinu, status alert diskret. Penghuni, admin, teknisi, dan sistem bertindak sebagai beberapa pelaku operasional; kondisi perangkat/kegiatan kamar tidak seluruhnya terlihat. Kemampuan AI adalah ANI dengan limited memory karena memakai histori/model; bukan AGI/ASI, theory-of-mind, self-aware, atau reactive machine murni.")
    add_heading(doc,"Demo BFS pada graf sintetis",2)
    b=f["bfs"]
    add_para(doc,f"State adalah node posisi teknisi; action berpindah ke node tetangga; goal adalah {b['goal']}; biaya satu per edge. Graf ini dibuat ilustratif untuk algoritma, bukan denah atau data sensor. BFS menemukan jalur {' -> '.join(b['path'])}. Urutan simpul yang dieksplorasi: {', '.join(b['explored_nodes'])} ({b['explored_count']} simpul).")
    add_para(doc,f"Pada graf berhingga BFS lengkap jika goal dapat dicapai dan optimal untuk graf tanpa bobot karena meminimalkan jumlah edge. Kompleksitas {b['complexity']['time']} waktu dan {b['complexity']['space']} ruang. Jika jarak atau biaya edge berbeda, gunakan Dijkstra atau A*.")
    add_heading(doc,"Kesimpulan",2)
    add_para(doc,"Pipeline berhasil menjalankan audit, regresi, persistence, Isolation Forest, skenario biaya, dan BFS. Pada subset yang diuji, perbandingan metrik regresi-baseline bercampur. Penerapan memerlukan data smart meter kos yang representatif, pembagian household/kamar yang sah, validasi tarif, serta uji manusia terhadap notifikasi. Dokumen tetap DRAFT sampai rubrik Bagian D-E dan placeholder dipenuhi.")
    page(doc)
    # References pages
    add_heading(doc,"Daftar pustaka",1)
    for sid,s in src.items():
        p=doc.add_paragraph(); p.paragraph_format.left_indent=Inches(.25); p.paragraph_format.first_line_indent=Inches(-.25); p.paragraph_format.space_after=Pt(5)
        p.add_run(f"[{srcnum[sid]}] {s['title']}. {s['publisher']}. {s['publication_date']}. ")
        hyperlink(p,s["url"],s["url"])
    add_para(doc,"Video presentasi: [ISI SETELAH VIDEO DIUNGGAH].",after=3)
    page(doc)
    add_heading(doc,"Lampiran  Status Bagian D-E",1)
    add_para(doc,"Direktori lokal tidak menyediakan rincian rubrik D-E. BRIEF_CODEX_SMARTGRID.md dan PROMPT_AWAL_CODEX.txt adalah spesifikasi terdahulu yang memilih dataset rumah tangga Prancis, sedangkan instruksi tugas terbaru menetapkan dataset London. Proyek ini mengikuti instruksi terbaru; angka eksperimen Prancis pada REPORT_UPDATE_GUIDE.md di folder induk tidak digunakan. Tidak satu pun berkas terdahulu tersebut memerinci isi rubrik D-E. Laporan ini memuat draft Bagian A-C dan tidak menyimpulkan kepatuhan pada seluruh soal ETS. Minta rubrik D-E dari dosen/LMS sebelum melengkapi dan menyusun berkas final.")
    add_para(doc,"Nama mahasiswa masih `[ISI NAMA MAHASISWA]`. Ganti placeholder setelah identitas dikonfirmasi. Tautan video tetap `[ISI SETELAH VIDEO DIUNGGAH]`; jangan menggantinya dengan tautan rekaan.")
    add_para(doc,"Sumber angka dalam dokumen adalah `outputs/report_facts.json`, yang dibangun dari audit, metrik, CSV perbandingan, ringkasan anomali, skenario biaya, dan hasil BFS. Jejak klaim kuantitatif tersedia di `docs/report_traceability.csv`.")
    dest=rep/"ETS_Tekber_Gasal26-27_DRAFT.docx"
    doc.save(dest); print(dest)

if __name__=="__main__": main()
