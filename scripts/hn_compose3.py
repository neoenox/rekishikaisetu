"""Honnoji composite v3: Blender frames + Pillow overlays -> FFmpeg NVENC; loudness-normalised final.
Readability rule: on-screen body text >= 30px (credits >= 28px, chart axes 24px) so it survives a phone screen.
usage: hn_compose3.py part A B   |   hn_compose3.py final"""
from pathlib import Path
import json,subprocess,sys,math,glob,os,re
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
FONT='C:/Windows/Fonts/YuGothM.ttc';BOLD='C:/Windows/Fonts/YuGothB.ttc'
SIZES=(22,24,26,28,30,32,34,36,40,44,46,52,56,64,72,96,110)
F={n:ImageFont.truetype(FONT,n) for n in SIZES};FB={n:ImageFont.truetype(BOLD,n) for n in SIZES}
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
timeline=load('data/hn_timeline.json');ana=load('data/hn_analysis.json');audio=load('out/hn_audio_report.json');segs=audio['segments']
N=round(timeline[-1]['end']*30);FR_DIR=ROOT/'cache'/'hn_v3'
BG=(7,24,36,240);GOLD=(239,201,118);WHITE=(245,243,232);DIM=(190,205,208);EDGE=(176,153,100)
COL={'kameyama':(150,110,255),'oinosaka':(255,160,40),'honnoji':(255,95,80),'honnoji_now':(150,185,255),'nijo':(255,95,80),'army':(150,110,255)}
NAME={'kameyama':'亀山城','oinosaka':'老ノ坂(最高点・仮)','honnoji':'本能寺(当時・推定)','honnoji_now':'本能寺(現在)','nijo':'二条新御所(仮置き)','army':'明智軍(模式)'}
DATE={0:'天正10年6月2日',1:'天正10年（1582）',2:'6月1日',3:'6月1日〜2日未明',4:'6月2日 未明',6:'6月2日 午前4時ごろ',7:'6月2日',9:'動機は諸説',10:'6月2日 → 13日'}
SUB={'nobunaga':'像：長興寺蔵','mitsuhide':'像：本徳寺蔵','nobutada':'像：総見寺蔵','hideyoshi':'像：高台寺蔵'}
NAMEP={'nobunaga':'織田信長','mitsuhide':'明智光秀','nobutada':'織田信忠','hideyoshi':'羽柴秀吉'}
CROP={'nobunaga':(.12,.07,.76),'mitsuhide':(.27,.45,.65),'nobutada':(.08,.0,.78),'hideyoshi':(.17,.36,.66)}
FRAME={'nobunaga':(255,95,80),'mitsuhide':(150,110,255),'nobutada':(255,95,80),'hideyoshi':(255,160,40)}
# (id,(x,y,w),reveal_after_n_sentences)
SPEC={0:[('nobunaga',(330,215,360),0),('mitsuhide',(1230,215,360),0)],
 1:[('nobunaga',(1300,185,170),0),('hideyoshi',(1485,185,170),2),('mitsuhide',(1670,185,170),2)],
 2:[('mitsuhide',(1640,185,240),0)],3:[('mitsuhide',(1640,185,240),0)],4:[('mitsuhide',(1640,185,240),0)],
 6:[('nobunaga',(45,445,200),0),('print',(1330,185,560),0)],
 7:[('nobutada',(1420,185,230),0),('nobunaga',(1660,185,230),0)],
 9:[('mitsuhide',(1420,185,230),0),('nobunaga',(1660,185,230),0)],
 10:[('hideyoshi',(1420,185,230),0),('mitsuhide',(1660,185,230),0)],
 11:[('nobunaga',(1440,175,200),0),('mitsuhide',(1670,175,200),0),('nobutada',(1440,515,200),0),('hideyoshi',(1670,515,200),0)]}
_IMG={}
def portrait(pid,w,prog):
    key=(pid,w,round(prog*40))
    if key in _IMG:return _IMG[key]
    im=Image.open(ROOT/'assets'/'portraits'/f'{pid}.jpg').convert('RGB')
    if pid=='print':out=im.resize((w,int(w*im.height/im.width)),Image.LANCZOS)
    else:
        x0,top,wf=CROP[pid];h=int(w*1.25);cw=im.width*wf*(1-.07*prog);ch=cw*1.25;cx=im.width*x0+im.width*wf/2;cy=im.height*top+im.width*wf*1.25/2
        out=im.crop(tuple(int(v) for v in (cx-cw/2,cy-ch/2,cx+cw/2,cy+ch/2))).resize((w,h),Image.LANCZOS)
    _IMG[key]=out;return out
def draw_cards(im,ci,t,local,shown,used):
    for pid,(x,y,w),after in SPEC.get(ci,[]):
        if shown<after:continue
        fade=min(1,max(0,(t-timeline[ci]['start']-.15)/.8))
        if ci==0:fade=min(1,max(0,(t-HOOK_END-.2)/.8))
        if fade<=0:continue
        p=portrait(pid,w,local);h=p.height;col=(200,170,100) if pid=='print' else FRAME[pid]
        bar=0 if pid=='print' else (74 if w>=190 else 48);cap=64 if pid=='print' else 0;tot=h+bar+cap
        layer=Image.new('RGBA',(w+12,tot+12),(0,0,0,0));ld=ImageDraw.Draw(layer)
        ld.rounded_rectangle((0,0,w+11,tot+11),10,fill=(7,24,36,240),outline=col+(255,),width=3);layer.paste(p,(6,6))
        if pid=='print':
            ld.text((12,h+10),'錦絵「本能寺焼討之図」',font=F[28],fill=WHITE);ld.text((12,h+40),'楊斎延一・1896年・名古屋市蔵',font=F[22],fill=DIM)
        elif w>=190:
            ld.text((12,h+8),NAMEP[pid],font=FB[34] if w<300 else FB[40],fill=WHITE);ld.text((12,h+48),SUB[pid],font=F[24],fill=DIM)
        else:ld.text((10,h+8),NAMEP[pid],font=FB[28],fill=WHITE)
        if fade<1:
            r,g,b,a=layer.split();layer=Image.merge('RGBA',(r,g,b,a.point(lambda v:int(v*fade))))
        im.alpha_composite(layer,(x-6,y-6));used.append((x-6,y-6,x+w+6,y+tot+6))
def overlap(a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
def tw(d,t,f):return d.textlength(t,font=f)
def label(d,text,x,y,used,color,font=F[34]):
    w=math.ceil(tw(d,text,font))+30;hgt=52
    for dx,dy in [(0,-66),(0,16),(-w/2-30,-22),(w/2+30,-22),(0,-126),(0,76),(0,-190)]:
        xx=max(30,min(1890-w,x-w/2+dx));yy=y+dy;box=(int(xx),int(yy),int(xx+w),int(yy+hgt))
        if yy<165 or yy+hgt>840 or any(overlap(box,b) for b in used):continue
        d.line([(x,y),(xx+w/2,yy+hgt/2)],fill=color,width=2);d.rounded_rectangle(box,8,fill=BG,outline=color,width=2);d.text((xx+15,yy+4),text,font=font,fill=WHITE);used.append(box);return box
    return None
def wrap(d,text,font,maxw):
    lines=[];cur=''
    for ch in text:
        if tw(d,cur+ch,font)>maxw and cur:
            k=max(cur.rfind('、'),cur.rfind('，'))
            if k>len(cur)*.45:lines.append(cur[:k+1]);cur=cur[k+1:]+ch
            else:lines.append(cur);cur=ch
        else:cur+=ch
    lines.append(cur);return lines
def panel(d,box,title,used):
    used.append(box);d.rounded_rectangle(box,12,fill=BG,outline=EDGE,width=2);d.text((box[0]+22,box[1]+12),title,font=FB[34],fill=GOLD)
def static_layer(ci,sc):
    im=Image.new('RGBA',(1920,1080),(0,0,0,0));d=ImageDraw.Draw(im)
    d.rectangle((0,0,1920,150),fill=(8,27,41,245));d.text((48,18),sc['title'],font=FB[64] if len(sc['title'])<14 else FB[52],fill=WHITE);d.text((48,96),sc['category'],font=F[34],fill=GOLD)
    if ci in DATE:
        f=FB[56];w=d.textlength(DATE[ci],font=f);d.text((1872-w,14),DATE[ci],font=f,fill=GOLD)
    if ci!=11:
        b='高さ2倍強調｜現代の地形・写真';w=d.textlength(b,font=F[30]);d.text((1872-w,96),b,font=F[30],fill=DIM)
    d.rectangle((0,1018,1920,1080),fill=(8,27,41,245));d.text((48,1027),'地理院タイルを加工｜肖像・錦絵：Wikimedia Commons(PD)｜VOICEVOX:四国めたん',font=F[30],fill=WHITE)
    return im
def profile_chart(d,box,p):
    prof=ana['profile'];D=ana['horizontal_distance_m'];e=prof['elevation_m'];dist=prof['distance_m'];mi,ma=0,300
    x0,y0,x1,y1=box[0]+30,box[1]+118,box[2]-30,box[3]-62
    pts=[(x0+v/D*(x1-x0),y1-(z-mi)/(ma-mi)*(y1-y0)) for v,z in zip(dist,e)]
    d.polygon(pts+[(x1,y1),(x0,y1)],fill=(60,90,100,200));d.line(pts,fill=GOLD,width=4)
    for k,lab in [('oinosaka_zone','老ノ坂'),('katsura','桂'),('honnoji','本能寺')]:
        v=ana['waypoint_dist_m'][k];xx=x0+v/D*(x1-x0);d.line([(xx,y0),(xx,y1)],fill=(120,150,160),width=1);d.text((xx-28 if k!='honnoji' else xx-84,y1+4),lab,font=F[24],fill=DIM)
    d.text((x0-4,y1+4),'亀山城',font=F[24],fill=DIM)
    cx=x0+p*(x1-x0);i=min(range(len(dist)),key=lambda j:abs(dist[j]/D-p));cy=pts[i][1]
    d.line([(cx,y0),(cx,y1)],fill=(150,110,255),width=3);d.ellipse((cx-9,cy-9,cx+9,cy+9),fill=(150,110,255),outline='white')
    d.text((box[0]+22,box[1]+58),f'{p*D/1000:4.1f} / {D/1000:.1f} km　標高 {np.interp(p*D,dist,e):3.0f} m',font=F[32],fill=WHITE)
# ---- hook (scene 0)
S0=[x for x in segs if x['scene']==0];HOOK_END=S0[2]['end']
PRINT=Image.open(ROOT/'assets'/'portraits'/'print.jpg').convert('RGB');PRINT=PRINT.resize((int(1080*PRINT.width/PRINT.height*1.0),1080),Image.LANCZOS)
def hook_layer(t):
    z=1.0+.10*min(1,t/HOOK_END);w=PRINT.width/z;h=PRINT.height/z;cx=PRINT.width*(.62-.12*min(1,t/HOOK_END));x0=max(0,min(PRINT.width-w,cx-w/2));y0=(PRINT.height-h)/2
    base=PRINT.crop((int(x0),int(y0),int(x0+w),int(y0+h))).resize((1920,1080),Image.LANCZOS).convert('RGBA')
    ov=Image.new('RGBA',(1920,1080),(6,12,20,0));px=ov.load()
    grad=Image.new('L',(1,1080));gd=grad.load()
    for y in range(1080):gd[0,y]=int(120+110*(y/1080)**2)
    ov=Image.new('RGBA',(1920,1080),(6,12,20,255));ov.putalpha(grad.resize((1920,1080)));base.alpha_composite(ov);d=ImageDraw.Draw(base,'RGBA')
    d.text((60,44),'天正10年6月2日 未明',font=FB[72],fill=GOLD)
    if t>=S0[0]['start']+.4:
        s='本能寺の変';d.text((60,150),s,font=FB[110],fill=WHITE)
    if t>=S0[1]['start']:
        d.rounded_rectangle((60,430,900,700),14,fill=(7,24,36,225),outline=(255,95,80),width=3)
        d.text((92,448),'信長の側近',font=FB[44],fill=WHITE);d.text((92,520),'20〜30人',font=FB[96],fill=(255,130,110));d.text((92,636),'〜 150〜160人（諸説）',font=F[40],fill=DIM)
    if t>=S0[2]['start']-.2:
        d.rounded_rectangle((960,430,1860,700),14,fill=(7,24,36,225),outline=(150,110,255),width=3)
        d.text((992,448),'光秀の軍勢',font=FB[44],fill=WHITE);d.text((992,520),'約1万3千',font=FB[96],fill=(185,160,255));d.text((992,636),'（一説・史料により異なる）',font=F[40],fill=DIM)
    d.text((60,812),'錦絵「本能寺焼討之図」楊斎延一・1896年・名古屋市蔵（Wikimedia Commons／PD）',font=F[26],fill=DIM)
    return base
def render(a,b):
    reports=[json.loads(Path(p).read_text()) for p in sorted(glob.glob(str(FR_DIR/'report_*.json')),key=os.path.getmtime)];fr={m['frame']:m for r in reports for m in r['frames']}
    statics={ci:static_layer(ci,sc) for ci,sc in enumerate(timeline)};scene_segs={ci:[x for x in segs if x['scene']==ci] for ci in range(len(timeline))}
    stills=[int(x) for x in os.environ['STILLS'].split(',')] if os.environ.get('STILLS') else None
    out=ROOT/'cache'/f'hn3_part_{a}_{b}.mp4';log=(ROOT/'logs'/f'hn3_enc_{a}.log').open('wb')
    class _P:
        class stdin:
            write=staticmethod(lambda b:None);close=staticmethod(lambda:None)
        def wait(self):pass
        returncode=0
    proc=_P() if stills else subprocess.Popen(['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','pipe:0','-an','-c:v','h264_nvenc','-preset','p4','-cq','19','-b:v','0','-pix_fmt','yuv420p',str(out)],stdin=subprocess.PIPE,stderr=log)
    layout=[];omitted=0
    try:
        for i in (stills or range(a,min(b,N))):
            m=fr[i];ci=m['scene'];t=i/30;local=m['local']
            im=Image.open(FR_DIR/f'{i:05}.jpg').convert('RGBA');seg_list=scene_segs[ci];shown=sum(1 for x in seg_list if t>=x['start'])
            hook=0.0
            if ci==0:hook=1.0 if t<HOOK_END else max(0.0,1-(t-HOOK_END)/1.0)
            st=statics[ci]
            if hook>0:
                hl=hook_layer(t)
                if hook<1:
                    st=st.copy();r,g,b_,al=st.split();st.putalpha(al.point(lambda v:int(v*(1-hook))))
                    r,g,b_,al=hl.split();hl.putalpha(al.point(lambda v:int(v*hook)))
                    im.alpha_composite(st);im.alpha_composite(hl)
                else:im=hl
            else:im.alpha_composite(st)
            d=ImageDraw.Draw(im,'RGBA')
            used=[(0,0,1920,150),(0,1018,1920,1080),(40,850,1880,1010)]
            P=(45,170,745,545)
            if ci in (3,4,8):
                panel(d,P,'経路の標高プロファイル（模式経路）',used);profile_chart(d,P,m['army_progress']);d.text((P[0]+22,P[3]-40),'直線で結んだ模式経路。実際の街道ではない',font=F[24],fill=DIM)
            if ci==1:
                panel(d,(45,170,880,530),'天正10年（1582）の流れ',used)
                items=['5/17　光秀、備中出陣の準備を命じられる','5/29　信長、少数の供回りで入京','6/1　光秀、亀山城を出発','6/2未明　光秀勢、本能寺を包囲']
                for k,txt in enumerate(items):
                    if shown>k:d.text((70,230+k*78),txt,font=F[32],fill=WHITE)
            if ci==2:
                P=(45,170,745,470);panel(d,P,'出発地点',used);d.text((70,230),'亀山城（現・亀岡市）',font=F[36],fill=WHITE);d.text((70,284),f'標高 約{ana["start_elev_m"]:.0f} m（現代DEM）',font=F[32],fill=WHITE);d.text((70,336),'約1万3千は一説。史料により異なる',font=F[30],fill=DIM);d.text((70,382),'（兵数は画面では実数を表さない）',font=F[28],fill=DIM)
            if ci==3:
                bx=(45,560,745,780);d.rounded_rectangle(bx,12,fill=BG,outline=EDGE,width=2);used.append(bx)
                d.text((68,575),'峠の標高（出典）　約230 m',font=F[32],fill=WHITE);d.text((68,625),f'模式経路の最高点　{ana["max_elev_m"]:.0f} m',font=F[32],fill=WHITE);d.text((68,675),f'登り {ana["ascent_m"]:.0f} m / 下り {ana["descent_m"]:.0f} m',font=F[32],fill=WHITE);d.text((68,727),'（高低差は現代のDEMによる）',font=F[26],fill=DIM)
            if ci==5:
                panel(d,(45,170,850,470),'二つの「本能寺」',used);d.ellipse((70,240,94,264),fill=COL['honnoji']);d.text((108,230),'当時：蛸薬師通の北・約120m四方',font=F[32],fill=WHITE)
                d.ellipse((70,298,94,322),fill=COL['honnoji_now']);d.text((108,288),'現在：寺町御池（1591–92年に移転）',font=F[32],fill=WHITE);d.text((70,364),f'二地点の距離　約{ana["honnoji_old_to_now_m"]/1000:.2f} km',font=FB[40],fill=GOLD)
            if ci==6:
                panel(d,(45,170,930,420),'6/2 午前4時ごろ（諸説）',used);d.text((70,232),'包囲の配置・炎は説明用の演出',font=F[32],fill=WHITE);d.text((70,284),'側近：20〜30人とも150〜160人とも',font=F[32],fill=WHITE);d.text((70,336),'（諸説あり確定していない）',font=F[28],fill=DIM)
            if ci==7:
                panel(d,(45,170,850,410),'本能寺跡 ↔ 二条新御所',used);d.text((70,232),f'距離　約{ana["honnoji_to_nijo_m"]/1000:.1f} km',font=FB[44],fill=GOLD);d.text((70,300),'二条側の位置は仮置き',font=F[32],fill=WHITE);d.text((70,350),'（誤差 数百m）',font=F[30],fill=DIM)
            if ci==8:
                P2=(45,560,745,845);panel(d,P2,'行軍時間の感度分析（速度は仮定）',used)
                if shown>=4:
                    for k,v in enumerate(ana['sensitivity']):
                        y=625+k*60;d.text((70,y),f'時速{v["assumed_speed_km_h"]}km',font=F[30],fill=WHITE);L=v['minutes']/360*300;d.rectangle((240,y+8,240+L,y+38),fill=(187,165,110));d.text((248+L,y+2),f'{v["minutes"]/60:.1f}時間',font=F[30],fill=WHITE)
                d.text((70,800),'休息・渡河を含まない。史実の時刻とは照合しない',font=F[26],fill=DIM)
            if ci==9 and shown>=3:
                panel(d,(45,170,880,700),'動機の主な説（結論は出ていない）',used)
                items=['怨恨説（信長への不満）','野望説（天下を狙った）','朝廷守護説','秀吉ライバル視説','黒幕存在説（議論が分かれる）']
                for k,txt in enumerate(items):
                    if t>=seg_list[2]['start']+k*1.4:d.text((70,235+k*76),'・'+txt,font=F[36],fill=WHITE)
                if shown>=len(seg_list):d.text((70,640),'地形データでは判定できない',font=FB[36],fill=GOLD)
            if ci==10:
                panel(d,(45,170,880,470),'その後',used);d.text((70,232),'6/2　本能寺の変',font=F[36],fill=WHITE);d.text((70,290),'6/13　山崎の戦い（11日後）',font=F[36],fill=WHITE);d.text((70,350),'山崎は地図の南の外側にある',font=F[30],fill=DIM)
            if ci==11:
                panel(d,(45,170,1390,840),'出典・制作クレジット',used)
                cr=['地形・写真：国土地理院 地理院タイル（標高・オルソ画像）を加工','歴史概要：Wikipedia（日本語版）本能寺の変ほか（CC BY-SA 4.0）','座標：国土地理院 住所検索（旧本能寺跡・二条付近・経由地）','肖像画・錦絵：Wikimedia Commons（パブリックドメイン）','　長興寺・本徳寺・総見寺・高台寺・名古屋市蔵','経路・軍勢・炎・包囲：模式表現（史実の再現ではない）','一次史料（信長公記など）の直接校訂は未実施','音声：VOICEVOX:四国めたん　制作：Blender・FFmpeg']
                for k,txt in enumerate(cr):d.text((72,232+k*72),txt,font=F[30],fill=WHITE)
            draw_cards(im,ci,t,local,shown,used);d=ImageDraw.Draw(im,'RGBA')
            if ci==0 and hook<1:
                al=int(255*(1-hook));tx=960-tw(d,'天正10年',FB[72])/2;d.text((tx,330),'天正10年',font=FB[72],fill=GOLD+(al,));tx=960-tw(d,'6月2日',FB[72])/2;d.text((tx,420),'6月2日',font=FB[72],fill=WHITE+(al,))
            if hook<1:
                for L in m['labels']:
                    if not(.04<L['x']<.96 and .22<L['y']<.8 and L['depth']>0):continue
                    if not label(d,NAME[L['id']],L['x']*1920,L['y']*1080,used,COL[L['id']]):omitted+=1
            active=next((x for x in seg_list if x['start']<=t<x['end']),None);sub=None
            if active:
                f=F[46];lines=wrap(d,active['text'],f,1700)
                if len(lines)>2:f=F[40];lines=wrap(d,active['text'],f,1720)
                assert len(lines)<=2,active['text'];sub=(60,860,1860,1008);d.rounded_rectangle(sub,12,fill=(5,18,29,242))
                for j,txt in enumerate(lines):
                    w=tw(d,txt,f);assert w<1760;d.text(((1920-w)/2,872+j*62),txt,font=f,fill='#fffcef')
            d.rectangle((48,1012,48+1824*(i+1)/N,1018),fill=(201,173,112))
            proc.stdin.write(im.convert('RGB').tobytes())
            if stills:im.convert('RGB').save(ROOT/'cache'/f'still3_{i}.png')
            if i%30==0:layout.append(dict(frame=i,scene=ci,subtitle_box=sub))
            if i%600==0:print(a,i,flush=True)
    finally:
        proc.stdin.close();proc.wait();log.close()
    assert proc.returncode==0
    if not stills:(ROOT/'cache'/f'hn3_part_{a}_{b}.json').write_text(json.dumps(dict(range=[a,b],omitted_labels=omitted,layout=layout),ensure_ascii=False),encoding='utf8')
def final():
    parts=sorted(ROOT.glob('cache/hn3_part_*.mp4'),key=lambda p:int(p.stem.split('_')[2]))
    lst=ROOT/'cache'/'hn3_parts.txt';lst.write_text(''.join(f"file '{p.as_posix()}'\n" for p in parts))
    wav=str(ROOT/'out'/'hn_narration.wav')
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',wav,'-af','loudnorm=I=-15:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True)
    j=json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}',r.stderr,re.S).group(0))
    af=f"loudnorm=I=-15:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
    subprocess.run(['ffmpeg','-y','-v','warning','-f','concat','-safe','0','-i',str(lst),'-i',wav,'-map','0:v','-map','1:a','-c:v','h264_nvenc','-preset','p5','-cq','25','-b:v','0','-pix_fmt','yuv420p','-af',af,'-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest',str(ROOT/'out'/'honnoji.mp4')],check=True)
    print('loudnorm input',j['input_i'],'LUFS')
if __name__=='__main__':
    if sys.argv[1]=='part':render(int(sys.argv[2]),int(sys.argv[3]))
    elif sys.argv[1]=='final':final()
