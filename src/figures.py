"""PNG charts generated with Pillow to keep the report build self-contained."""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def _font(size=17, bold=False):
    candidates = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
                  "/System/Library/Fonts/Supplemental/Arial.ttf"]
    for p in candidates:
        try: return ImageFont.truetype(p, size)
        except OSError: pass
    return ImageFont.load_default()


def draw_series(path, title, y_label, lines, source="LCL-June2015v2_0.csv; London, half-hourly kWh"):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    W,H=1200,680; im=Image.new("RGB",(W,H),"white"); d=ImageDraw.Draw(im)
    d.text((90,22),title,fill="#14233a",font=_font(27,True))
    d.text((90,58),f"Sumber: {source}",fill="#596b7c",font=_font(15))
    L,T,R,B=105,112,1150,560
    vals=[v for _,a,_ in lines for v in a if v is not None and v==v and abs(v)!=float('inf')]
    if not vals: vals=[0,1]
    lo,hi=min(vals),max(vals); pad=(hi-lo)*.06 or 1; lo-=pad; hi+=pad
    for i in range(6):
        y=T+(B-T)*i/5; d.line((L,y,R,y),fill="#e8edf3",width=1)
        d.text((10,y-8),f"{hi-(hi-lo)*i/5:.3g}",fill="#596b7c",font=_font(14))
    d.line((L,T,L,B),fill="#526174",width=2); d.line((L,B,R,B),fill="#526174",width=2)
    d.text((10,86),y_label,fill="#354b62",font=_font(15)); d.text((L,B+15),"Urutan interval uji",fill="#596b7c",font=_font(14))
    for j,(name,arr,color) in enumerate(lines):
        pts=[]; n=len(arr)
        for i,v in enumerate(arr):
            if v is None or v!=v: continue
            pts.append((L+(R-L)*i/max(1,n-1),B-(v-lo)/(hi-lo)*(B-T)))
        if len(pts)>1: d.line(pts,fill=color,width=2)
        x=L+j*270; d.line((x,620,x+25,620),fill=color,width=4); d.text((x+32,610),name,fill="#14233a",font=_font(15))
    im.save(path)


def draw_histogram(path,title,values,x_label,source="LCL-June2015v2_0.csv; London, half-hourly kWh"):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    im=Image.new("RGB",(1200,680),"white"); d=ImageDraw.Draw(im)
    d.text((90,22),title,fill="#14233a",font=_font(27,True)); d.text((90,58),f"Sumber: {source}",fill="#596b7c",font=_font(15))
    nums=[float(v) for v in values if v is not None and v==v and abs(v)!=float('inf')]
    if not nums: nums=[0.0]
    lo,hi=min(nums),max(nums); hi=hi if hi>lo else lo+1; bins=35; counts=[0]*bins
    for v in nums: counts[min(bins-1,max(0,int((v-lo)/(hi-lo)*bins)))]+=1
    L,T,R,B=110,120,1150,555; peak=max(counts) or 1
    for j,n in enumerate(counts):
        x0=L+j*(R-L)/bins+2; x1=L+(j+1)*(R-L)/bins-2; y=B-n/peak*(B-T)
        d.rectangle((x0,y,x1,B),fill="#2878c8")
    d.line((L,B,R,B),fill="#526174",width=2); d.text((L,B+16),f"{x_label} ({lo:.3g} sampai {hi:.3g})",fill="#596b7c",font=_font(14))
    d.text((10,90),"Jumlah observasi",fill="#354b62",font=_font(14)); im.save(path)


def draw_cost_scenarios(path, scenarios):
    """Plot savings scenarios with meaningful categorical x-axis labels."""
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    im=Image.new("RGB",(1200,680),"white"); d=ImageDraw.Draw(im)
    d.text((90,22),"Simulasi biaya rata-rata rumah tangga per bulan",fill="#14233a",font=_font(27,True))
    d.text((90,58),"Sumber: energi interval London x asumsi tarif PLN Indonesia; simulasi",fill="#596b7c",font=_font(15))
    vals=[float(x["estimated_cost_idr_per_household_month"]) for x in scenarios]
    labels=[f"{float(x['reduction_percent']):g}%" for x in scenarios]
    lo=min(vals); hi=max(vals); pad=(hi-lo)*.12 or max(1,hi*.05); lo-=pad; hi+=pad
    L,T,R,B=145,120,1150,555
    for i in range(6):
        y=T+(B-T)*i/5; val=hi-(hi-lo)*i/5
        d.line((L,y,R,y),fill="#e8edf3",width=1)
        d.text((8,y-8),f"Rp {val:,.0f}",fill="#596b7c",font=_font(14))
    d.line((L,T,L,B),fill="#526174",width=2); d.line((L,B,R,B),fill="#526174",width=2)
    pts=[]
    for i,(label,val) in enumerate(zip(labels,vals)):
        x=L+(R-L)*i/max(1,len(vals)-1); y=B-(val-lo)/(hi-lo)*(B-T)
        pts.append((x,y)); d.ellipse((x-6,y-6,x+6,y+6),fill="#2878c8")
        d.text((x-18,B+15),label,fill="#596b7c",font=_font(16))
    if len(pts)>1: d.line(pts,fill="#2878c8",width=4)
    d.text((8,88),"Biaya (Rupiah / household-bulan)",fill="#354b62",font=_font(15))
    d.text((L,B+48),"Pengurangan energi (simulasi)",fill="#596b7c",font=_font(14))
    im.save(path)


def draw_architecture(path):
    im=Image.new("RGB",(1600,1050),"white"); d=ImageDraw.Draw(im)
    d.text((80,36),"Arsitektur Smart Grid Kos Mahasiswa - Dataset London",fill="#14233a",font=_font(34,True))
    d.text((80,90),"Desain konseptual; data eksperimen berisi energi kWh per interval 30 menit",fill="#526174",font=_font(20))
    layers=[("POWER-SYSTEM",150,"#eaf2fb",["Jaringan PLN -> panel distribusi kos","Sirkuit cabang -> beban kamar/peralatan"]),
            ("POWER-FLOW",405,"#e9f6f1",["Smart meter per kamar / titik ukur konseptual","Menghasilkan energi interval (kWh / 30 menit)","Dataset London: kolom energi, ID pseudonim, waktu, jenis tarif"]),
            ("INFORMATION",705,"#fff4e5",["HAN / LAN -> gateway/router -> WAN","Ingesti -> validasi -> API / penyimpanan","Linear Regression + Isolation Forest","Dashboard penghuni/admin -> notifikasi -> tinjauan manusia"])]
    for title,y,color,rows in layers:
        d.rounded_rectangle((80,y,1520,y+210),radius=22,fill=color,outline="#718096",width=2)
        d.text((115,y+18),title,fill="#14233a",font=_font(24,True))
        for i,row in enumerate(rows): d.text((150,y+64+i*38),"• "+row,fill="#26364a",font=_font(20))
    d.text((80,955),"Kontrol akses: RBAC, TLS, kredensial terbatas, logging, retensi, pseudonymous ID. Tidak ada pemutus listrik otomatis.",fill="#354b62",font=_font(18))
    im.save(path)
