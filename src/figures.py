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
    """Create the black-and-white, hand-sketched architecture infographic."""
    import random
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    scale=2; W,H=1600,1050; ink="#111111"
    im=Image.new("RGBA",(W*scale,H*scale),"white"); d=ImageDraw.Draw(im)
    def font(size,bold=False):
        choices=(
            ["/System/Library/Fonts/Supplemental/ChalkboardSE.ttc",
             "/System/Library/Fonts/Supplemental/Comic Sans MS Bold.ttf"] if bold else
            ["/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf",
             "/System/Library/Fonts/Supplemental/Chalkboard.ttc",
             "/System/Library/Fonts/Supplemental/Comic Sans MS.ttf"])
        for candidate in choices:
            try: return ImageFont.truetype(candidate,size*scale)
            except OSError: pass
        return _font(size*scale,bold)
    def text(x,y,value,size=19,bold=False,anchor=None):
        d.text((x*scale,y*scale),value,fill=ink,font=font(size,bold),anchor=anchor)
    def line(points,width=2):
        d.line([(int(x*scale),int(y*scale)) for x,y in points],fill=ink,width=width*scale,joint="curve")
    def box(x0,y0,x1,y1,seed=1,width=2):
        rng=random.Random(seed); pts=[]
        for x in range(x0,x1+1,22): pts.append((x,y0+rng.randint(-2,2)))
        for y in range(y0,y1+1,22): pts.append((x1+rng.randint(-2,2),y))
        for x in range(x1,x0-1,-22): pts.append((x,y1+rng.randint(-2,2)))
        for y in range(y1,y0-1,-22): pts.append((x0+rng.randint(-2,2),y))
        pts.append(pts[0]); line(pts,width)
    def arrow(x0,y0,x1,y1=None):
        if y1 is None: y1=y0
        line([(x0,y0),(x1,y1)],2)
        if abs(y1-y0)<2: line([(x1-10,y1-7),(x1,y1),(x1-10,y1+7)],2)
        else: line([(x1-7,y1-10),(x1,y1),(x1+7,y1-10)],2)
    def centered(x,y,value,size=17,bold=False): text(x,y,value,size,bold,"mm")
    def crop_icon(crop_box,target_box):
        if not sheet: return
        art=sheet.crop(crop_box); x0,y0,x1,y1=target_box
        max_size=((x1-x0)*scale,(y1-y0)*scale); art.thumbnail(max_size,Image.Resampling.LANCZOS)
        pos=(x0*scale+(max_size[0]-art.width)//2,y0*scale+(max_size[1]-art.height)//2)
        im.alpha_composite(art,pos)
    def bulb(cx,cy):
        d.ellipse(((cx-12)*scale,(cy-14)*scale,(cx+12)*scale,(cy+12)*scale),outline=ink,width=2*scale)
        line([(cx-7,cy+10),(cx-5,cy+18),(cx+5,cy+18),(cx+7,cy+10)],2)
        line([(cx-5,cy+21),(cx+5,cy+21)],2)
        for dx,dy in [(-19,-17),(0,-26),(19,-17)]: line([(cx+dx,cy+dy),(cx+dx*1.3,cy+dy*1.3)],2)
    def chart(cx,cy):
        line([(cx-46,cy+32),(cx-46,cy-32)],2); line([(cx-46,cy+32),(cx+50,cy+32)],2)
        for i,h in enumerate([15,26,37,48,60]):
            x=cx-30+i*15; d.rectangle((x*scale,(cy+30-h)*scale,(x+8)*scale,(cy+30)*scale),outline=ink,width=2*scale)
    def small_doc(cx,cy):
        box(cx-25,cy-38,cx+25,cy+38,seed=41,width=2)
        for yy in (-18,-4,10,24): line([(cx-14,cy+yy),(cx+15,cy+yy)],1)
    def wifi(cx,cy):
        for r in (17,31,45):
            d.arc(((cx-r)*scale,(cy-r)*scale,(cx+r)*scale,(cy+r)*scale),220,320,fill=ink,width=2*scale)
        d.ellipse(((cx-4)*scale,(cy+25)*scale,(cx+4)*scale,(cy+33)*scale),fill=ink)
    def database(cx,cy):
        d.ellipse(((cx-28)*scale,(cy-29)*scale,(cx+28)*scale,(cy-10)*scale),outline=ink,width=2*scale)
        line([(cx-28,cy-20),(cx-28,cy+28)],2); line([(cx+28,cy-20),(cx+28,cy+28)],2)
        d.arc(((cx-28)*scale,(cy+17)*scale,(cx+28)*scale,(cy+38)*scale),0,180,fill=ink,width=2*scale)
        d.arc(((cx-28)*scale,(cy+2)*scale,(cx+28)*scale,(cy+22)*scale),0,180,fill=ink,width=2*scale)
    def bulb_group(cx,cy):
        for dx in (-34,0,34): bulb(cx+dx,cy)
    sheet_path=path.with_name("Arsitektur_doodles_sheet.png")
    sheet=Image.open(sheet_path).convert("RGBA") if sheet_path.exists() else None

    # Title and three horizontal, hand-drawn architecture layers.
    box(405,10,1195,78,seed=7,width=3)
    centered(800,44,"ARSITEKTUR SMART GRID KOS",34,True)
    box(45,98,1555,375,seed=11,width=3)
    box(45,390,1555,585,seed=12,width=3)
    box(45,600,1555,970,seed=13,width=3)
    box(58,108,300,150,seed=14,width=2); centered(179,130,"POWER-SYSTEM",23,True)
    box(58,400,290,442,seed=15,width=2); centered(174,421,"POWER-FLOW",23,True)
    box(58,610,310,652,seed=16,width=2); centered(184,631,"INFORMATION",23,True)

    # Power-system: PLN -> distribution panel -> room circuits -> loads.
    crop_icon((38,55,315,630),(73,166,270,330))
    centered(170,347,"PLN",20,True)
    arrow(270,250,330,250)
    crop_icon((325,145,655,590),(325,185,485,325))
    centered(405,347,"Panel distribusi kos",17)
    line([(490,250),(605,250)],2); line([(605,178),(605,322)],2)
    for idx,(yy,label,load) in enumerate([(178,"Sirkuit kamar 1","Beban kamar 1"),(250,"Sirkuit kamar 2","Beban kamar 2"),(322,"Sirkuit kamar N","Beban kamar N")]):
        line([(605,yy),(640,yy)],2); box(640,yy-24,1030,yy+24,seed=20+idx,width=2)
        centered(835,yy,label,19)
        arrow(1032,yy,1113,yy)
        box(1120,yy-24,1518,yy+24,seed=30+idx,width=2)
        bulb(1155,yy); text(1190,yy-15,load,20)

    # Power-flow: conceptual meter and 30-minute energy readings.
    crop_icon((682,105,1142,635),(360,445,575,562))
    centered(465,565,"Smart meter (konseptual)",17)
    arrow(590,505,730,505)
    box(745,438,1065,560,seed=45,width=2); chart(900,494)
    centered(900,548,"tiap 30 menit",16)
    text(1100,477,"Energi kWh",25,True); text(1100,516,"per 30 menit",25,True)

    # Information pipeline: data -> networking -> storage -> AI -> decision.
    cols=[(65,205),(246,386),(427,577),(620,760),(794,1014),(1048,1178),(1211,1351),(1384,1530)]
    top,bottom=690,918; mid=800
    # Data source.
    box(cols[0][0],top,cols[0][1],bottom,seed=51,width=2); small_doc(135,739)
    centered(135,805,"Data meter",18,True); centered(135,835,"kWh, waktu,",15); centered(135,858,"ID pseudonim",15)
    # Local network.
    box(cols[1][0],top,cols[1][1],bottom,seed=52,width=2); wifi(316,753)
    centered(316,818,"HAN / LAN",18,True); centered(316,848,"jaringan kos",15)
    # Gateway/router.
    box(cols[2][0],top,cols[2][1],bottom,seed=53,width=2); crop_icon((1120,315,1550,680),(438,710,565,790))
    centered(502,818,"Gateway /",17,True); centered(502,848,"Router",17,True)
    # API and storage.
    box(cols[3][0],top,cols[3][1],bottom,seed=54,width=2); database(690,748)
    centered(690,818,"API &",18,True); centered(690,848,"Penyimpanan",17,True); centered(690,878,"(database)",14)
    # Two parallel analysis models, each with its own incoming/outgoing branch.
    box(cols[4][0],top,cols[4][1],790,seed=55,width=2)
    line([(807,766),(807,720),(846,720)],2); line([(807,766),(848,766)],2)
    line([(816,757),(825,747),(834,739),(845,727)],2)
    centered(930,728,"Linear Regression",16,True); centered(930,756,"prediksi t+30 menit",14)
    box(cols[4][0],805,cols[4][1],bottom,seed=56,width=2)
    for i,h in enumerate((18,30,23,43)):
        x=805+i*11; d.rectangle((x*scale,(883-h)*scale,(x+6)*scale,883*scale),outline=ink,width=2*scale)
    centered(930,840,"Isolation Forest",16,True); centered(930,868,"pola tidak biasa",14)
    # Dashboard and warning.
    box(cols[5][0],top,cols[5][1],bottom,seed=57,width=2)
    d.rectangle((1071*scale,720*scale,1155*scale,778*scale),outline=ink,width=3*scale)
    chart(1113,751)
    centered(1113,810,"Dashboard &",17,True); centered(1113,839,"peringatan",17,True)
    # People receiving the alert.
    box(cols[6][0],top,cols[6][1],bottom,seed=58,width=2)
    d.ellipse((1248*scale,720*scale,1278*scale,750*scale),outline=ink,width=2*scale)
    d.ellipse((1290*scale,720*scale,1320*scale,750*scale),outline=ink,width=2*scale)
    d.arc((1238*scale,742*scale,1288*scale,793*scale),180,360,fill=ink,width=3*scale)
    d.arc((1280*scale,742*scale,1330*scale,793*scale),180,360,fill=ink,width=3*scale)
    centered(1281,822,"Penghuni /",17,True); centered(1281,850,"Admin",17,True)
    # Human review / decision.
    box(cols[7][0],top,cols[7][1],bottom,seed=59,width=2); small_doc(1455,739)
    d.ellipse((1463*scale,746*scale,1492*scale,775*scale),outline=ink,width=3*scale)
    line([(1488,771),(1504,787)],2)
    centered(1457,822,"Tinjauan",17,True); centered(1457,850,"manusia",17,True)
    for left,right in [(205,246),(386,427),(577,620),(1178,1211),(1351,1384)]: arrow(left,mid,right)
    line([(760,mid),(780,mid)],2); line([(780,740),(780,860)],2)
    arrow(780,740,794,740); arrow(780,860,794,860)
    line([(1014,740),(1032,740)],2); line([(1014,860),(1032,860)],2); line([(1032,740),(1032,860)],2)
    arrow(1032,mid,1048,mid)
    text(68,934,"Akses berbasis peran, TLS, API key terbatas, logging, dan retensi data.",17)
    text(865,934,"Peringatan ditinjau manusia; tidak ada pemutus listrik otomatis.",17)
    im.resize((W,H),Image.Resampling.LANCZOS).convert("RGB").save(path)


def draw_energy_histogram(path, values, title="Distribusi konsumsi energi"):
    """Plot valid public-dataset readings in kWh per 30-minute interval."""
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    nums=[float(v) for v in values if v is not None and v==v and abs(v)!=float('inf')]
    if not nums: nums=[0.0]
    lo=max(0.0,min(nums)); hi=max(nums) or 1.0; bins=40; counts=[0]*bins
    for v in nums: counts[min(bins-1,max(0,int((v-lo)/(hi-lo)*bins)))]+=1
    im=Image.new("RGB",(1200,680),"white"); d=ImageDraw.Draw(im)
    d.text((90,22),title,fill="#14233a",font=_font(27,True))
    d.text((90,58),"Sumber: LCL-June2015v2_0.csv; pembacaan valid, kWh per 30 menit",fill="#596b7c",font=_font(15))
    L,T,R,B=110,120,1150,555; peak=max(counts) or 1
    for i in range(6):
        y=T+(B-T)*i/5; d.line((L,y,R,y),fill="#e8edf3",width=1)
    for j,n in enumerate(counts):
        x0=L+j*(R-L)/bins+2; x1=L+(j+1)*(R-L)/bins-2; y=B-n/peak*(B-T)
        d.rectangle((x0,y,x1,B),fill="#2878c8")
    d.line((L,B,R,B),fill="#526174",width=2)
    d.text((L,B+18),f"Energi interval: {lo:.3g} sampai {hi:.3g} kWh",fill="#596b7c",font=_font(15))
    d.text((10,90),"Jumlah pembacaan",fill="#354b62",font=_font(15)); im.save(path)


def draw_profile(path, values, title, x_title):
    """Plot an ordered profile from category/value pairs."""
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    labels=[str(x[0]) for x in values]; nums=[float(x[1]) for x in values]
    im=Image.new("RGB",(1200,680),"white"); d=ImageDraw.Draw(im)
    d.text((90,22),title,fill="#14233a",font=_font(27,True))
    d.text((90,58),"Sumber: LCL-June2015v2_0.csv; rata-rata kWh per 30 menit",fill="#596b7c",font=_font(15))
    L,T,R,B=110,120,1150,555; lo=min([0.0]+nums); hi=max(nums) or 1.0
    for i in range(6):
        y=T+(B-T)*i/5; d.line((L,y,R,y),fill="#e8edf3",width=1)
        d.text((12,y-8),f"{hi-(hi-lo)*i/5:.3g}",fill="#596b7c",font=_font(13))
    d.line((L,T,L,B),fill="#526174",width=2); d.line((L,B,R,B),fill="#526174",width=2)
    step=(R-L)/max(1,len(nums)); bw=min(36,step*.62)
    for i,(label,val) in enumerate(zip(labels,nums)):
        x=L+(i+.5)*step; y=B-(val-lo)/(hi-lo)*(B-T)
        d.rounded_rectangle((x-bw/2,y,x+bw/2,B),radius=4,fill="#2878c8")
        if len(labels)<=24: d.text((x-17,B+10),label,fill="#596b7c",font=_font(13))
    d.text((L,B+42),x_title,fill="#596b7c",font=_font(14)); im.save(path)


def draw_model_comparison(path, rows):
    """Compare errors on identical held-out examples."""
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    names=[r["model"] for r in rows]; metrics=[("MAE_kWh_per_30min","MAE"),("RMSE_kWh_per_30min","RMSE")]
    maximum=max(float(r[k]) for r in rows for k,_ in metrics) or 1.0
    im=Image.new("RGB",(1200,680),"white"); d=ImageDraw.Draw(im)
    d.text((90,22),"Perbandingan model pada data test",fill="#14233a",font=_font(27,True))
    d.text((90,58),"Observasi identik; makin rendah MAE/RMSE makin baik",fill="#596b7c",font=_font(15))
    L,T,R,B=160,130,1130,530
    for i in range(6):
        y=T+(B-T)*i/5; d.line((L,y,R,y),fill="#e8edf3",width=1)
        d.text((20,y-8),f"{maximum*(1-i/5):.3f}",fill="#596b7c",font=_font(14))
    colors=["#64748b","#2878c8"]; group_w=(R-L)/len(metrics); bar_w=min(130,group_w/(len(rows)+1))
    for j,(key,label) in enumerate(metrics):
        center=L+(j+.5)*group_w
        for i,row in enumerate(rows):
            val=float(row[key]); x=center+(i-(len(rows)-1)/2)*(bar_w+10); y=B-val/maximum*(B-T)
            d.rounded_rectangle((x-bar_w/2,y,x+bar_w/2,B),radius=5,fill=colors[i%len(colors)])
            d.text((x-42,y-26),f"{val:.4f}",fill="#14233a",font=_font(13))
        d.text((center-30,B+16),label,fill="#354b62",font=_font(17,True))
    for i,name in enumerate(names):
        x=300+i*300; d.rectangle((x,600,x+20,620),fill=colors[i%len(colors)])
        d.text((x+30,599),name.replace("_"," "),fill="#14233a",font=_font(15))
    im.save(path)
