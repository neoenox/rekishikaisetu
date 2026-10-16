"""Honnoji composite: Blender frames + Pillow overlays (labels, charts, subtitles) -> FFmpeg NVENC.
usage: hn_compose.py part A B   |   hn_compose.py final   |   hn_compose.py all"""
from pathlib import Path
import json,subprocess,sys,math,time,glob
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
FONT='C:/Windows/Fonts/YuGothM.ttc';BOLD='C:/Windows/Fonts/YuGothB.ttc'
F={n:ImageFont.truetype(FONT,n) for n in (18,20,22,24,26,28,32,36,40,44,46,52)};FB={n:ImageFont.truetype(BOLD,n) for n in (24,28,32,52,64)}
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
timeline=load('data/hn_timeline.json');ana=load('out/../data/hn_analysis.json');audio=load('out/hn_audio_report.json');segs=audio['segments']
N=round(timeline[-1]['end']*30)
BG=(7,24,36,238);GOLD=(239,201,118);WHITE=(245,243,232);DIM=(167,185,189)
COL={'kameyama':(150,110,255),'oinosaka':(255,160,40),'honnoji':(255,95,80),'honnoji_now':(150,185,255),'nijo':(255,95,80),'army':(150,110,255)}
NAME={'kameyama':'亀山城','oinosaka':'老ノ坂(最高点・仮)','honnoji':'本能寺(当時・推定)','honnoji_now':'本能寺(現在)','nijo':'二条新御所(仮置き)','army':'明智軍(模式)'}
CAT_COL=GOLD
DATE={0:'天正10年6月2日',1:'天正10年（1582）',2:'6月1日',3:'6月1日〜2日未明',4:'6月2日 未明',6:'6月2日 午前4時ごろ',7:'6月2日',9:'動機は諸説',10:'6月2日 → 13日'}
SUB={'nobunaga':'像：長興寺蔵','mitsuhide':'像：本徳寺蔵','nobutada':'像：総見寺蔵','hideyoshi':'像：高台寺蔵'}
NAMEP={'nobunaga':'織田信長','mitsuhide':'明智光秀','nobutada':'織田信忠','hideyoshi':'羽柴秀吉'}
CROP={'nobunaga':(.12,.07,.76),'mitsuhide':(.27,.45,.65),'nobutada':(.08,.0,.78),'hideyoshi':(.17,.36,.66)}  # x0,top,width fraction of image width
FRAME={'nobunaga':(255,95,80),'mitsuhide':(150,110,255),'nobutada':(255,95,80),'hideyoshi':(255,160,40)}
# slots: (id,(x,y,w),reveal_after_sentence_count)
SPEC={0:[('nobunaga',(330,205,360),0),('mitsuhide',(1230,205,360),0)],
 1:[('nobunaga',(1470,480,128),0),('hideyoshi',(1613,480,128),2),('mitsuhide',(1756,480,128),2)],
 2:[('mitsuhide',(1470,480,200),0)],3:[('mitsuhide',(1470,480,200),0)],4:[('mitsuhide',(1470,480,200),0)],
 6:[('nobunaga',(45,350,190),0),('print',(1470,470,415),0)],
 7:[('nobutada',(1470,480,200),0),('nobunaga',(1685,480,200),0)],
 9:[('mitsuhide',(1470,480,190),0),('nobunaga',(1685,480,190),0)],
 10:[('hideyoshi',(1470,480,190),0),('mitsuhide',(1685,480,190),0)],
 11:[('nobunaga',(1440,205,200),0),('mitsuhide',(1665,205,200),0),('nobutada',(1440,525,200),0),('hideyoshi',(1665,525,200),0)]}
_IMG={}
def portrait(pid,w,prog):
    key=(pid,w,round(prog*40))
    if key in _IMG:return _IMG[key]
    im=Image.open(ROOT/'assets'/'portraits'/f'{pid}.jpg').convert('RGB')
    if pid=='print':h=int(w*im.height/im.width);out=im.resize((w,h),Image.LANCZOS)
    else:
        x0,top,wf=CROP[pid];h=int(w*1.25);cw=im.width*wf*(1-.07*prog);ch=cw*1.25;cx=im.width*x0+im.width*wf/2;cy=im.height*top+im.width*wf*1.25/2
        box=(cx-cw/2,cy-ch/2,cx+cw/2,cy+ch/2);out=im.crop(tuple(int(v) for v in box)).resize((w,h),Image.LANCZOS)
    _IMG[key]=out;return out
def draw_cards(im,d,ci,t,local,shown,used):
    for pid,(x,y,w),after in SPEC.get(ci,[]):
        if shown<after:continue
        fade=min(1,max(0,(t-timeline[ci]['start']-.15)/.8)) if True else 1
        if fade<=0:continue
        p=portrait(pid,w,local);h=p.height;col=(200,170,100) if pid=='print' else FRAME[pid]
        bar=0 if pid=='print' else (66 if w>=190 else 42);cap=(54 if pid=='print' else 0)
        tot=h+bar+cap;h+=0;layer=Image.new('RGBA',(w+12,tot+12),(0,0,0,0));ld=ImageDraw.Draw(layer)
        ld.rounded_rectangle((0,0,w+11,tot+11),10,fill=(7,24,36,int(235*fade)),outline=col+(int(255*fade),),width=3)
        layer.paste(p,(6,6));
        if pid=='print':
            ld.text((10,h+12),'錦絵「本能寺焼討之図」',font=F[20],fill=WHITE);ld.text((10,h+36),'楊斎延一・1896年・名古屋市蔵',font=F[18],fill=DIM)
        else:
            nm=NAMEP[pid]
            if w>=190:ld.text((12,h+12),nm,font=FB[28] if w<300 else FB[32],fill=WHITE);ld.text((12,h+42),SUB[pid],font=F[18],fill=DIM)
            else:ld.text((10,h+11),nm,font=F[22],fill=WHITE)
        if pid=='print' or True:
            a=layer.split()[3].point(lambda v:v);layer.putalpha(a)
        if fade<1:
            r,g,b,a=layer.split();layer=Image.merge('RGBA',(r,g,b,a.point(lambda v:int(v*fade))))
        im.alpha_composite(layer,(x-6,y-6));used.append((x-6,y-6,x+w+6,y+tot+6))
    return
def overlap(a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
def tw(d,t,f):return d.textlength(t,font=f)
def label(d,text,x,y,used,color,font=F[32]):
    w=math.ceil(tw(d,text,font))+28;hgt=48
    for dx,dy in [(0,-62),(0,14),(-w/2-30,-20),(w/2+30,-20),(0,-120),(0,70),(0,-180)]:
        xx=max(30,min(1890-w,x-w/2+dx));yy=y+dy;box=(int(xx),int(yy),int(xx+w),int(yy+hgt))
        if yy<180 or yy+hgt>850 or any(overlap(box,b) for b in used):continue
        d.line([(x,y),(xx+w/2,yy+hgt/2)],fill=color,width=2);d.rounded_rectangle(box,7,fill=BG,outline=color,width=2);d.text((xx+14,yy+3),text,font=font,fill=WHITE);used.append(box);return box
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
    used.append(box);d.rounded_rectangle(box,12,fill=BG,outline=(176,153,100),width=2);d.text((box[0]+20,box[1]+12),title,font=FB[28],fill=GOLD)
def static_layer(ci,sc):
    im=Image.new('RGBA',(1920,1080),(0,0,0,0));d=ImageDraw.Draw(im)
    d.rectangle((0,0,1920,170),fill=(8,27,41,245));d.text((48,22),sc['title'],font=FB[64] if len(sc['title'])<14 else FB[52],fill=WHITE);d.text((48,108),sc['category'],font=F[32],fill=CAT_COL)
    if ci in DATE:
        f=FB[52];w=d.textlength(DATE[ci],font=f);d.text((1872-w,50),DATE[ci],font=f,fill=GOLD)
    d.rectangle((0,1015,1920,1080),fill=(8,27,41,240));d.text((48,1030),'出典：'+(' / '.join(sc['source_ids']) if ci!=11 else '下記クレジット参照')+'　|　地理院タイル（標高・写真）を加工'+('　|　肖像：Commons(PD)' if ci in SPEC else '')+'　|　VOICEVOX:四国めたん',font=F[24],fill=WHITE)
    if ci not in (0,11):
        d.rounded_rectangle((1470,185,1885,448),10,fill=BG,outline=(176,153,100),width=2)
        rows=[((150,110,255),'明智軍・亀山城（模式）'),((255,95,80),'本能寺（当時）・二条（仮）'),((150,185,255),'本能寺（現在）'),((255,160,40),'老ノ坂・経路（模式）')]
        for k,(c,t) in enumerate(rows):d.ellipse((1490,205+k*38,1510,225+k*38),fill=c);d.text((1522,198+k*38),t,font=F[24],fill=WHITE)
        d.text((1490,352),'高さ2倍強調｜現代の地形',font=F[22],fill=GOLD);d.text((1490,384),'植生・建物は現代の空中写真',font=F[22],fill=DIM);d.text((1490,414),'旗・兵は説明用の拡大',font=F[22],fill=DIM)
    return im
def route_xy_at(p):
    dd=np.array(ana['profile']['distance_m']);return p*ana['horizontal_distance_m']
def profile_chart(d,box,p,reveal_bars=None):
    prof=ana['profile'];D=ana['horizontal_distance_m'];e=prof['elevation_m'];dist=prof['distance_m'];mi,ma=0,300
    x0,y0,x1,y1=box[0]+30,box[1]+110,box[2]-30,box[3]-60
    pts=[(x0+v/D*(x1-x0),y1-(z-mi)/(ma-mi)*(y1-y0)) for v,z in zip(dist,e)]
    d.polygon(pts+[(x1,y1),(x0,y1)],fill=(60,90,100,200));d.line(pts,fill=GOLD,width=4)
    for k,lab in [('oinosaka_zone','老ノ坂'),('katsura','桂'),('honnoji','本能寺')]:
        v=ana['waypoint_dist_m'][k];xx=x0+v/D*(x1-x0);d.line([(xx,y0),(xx,y1)],fill=(120,150,160),width=1);d.text((xx-20 if k!='honnoji' else xx-60,y1+4),lab,font=F[20],fill=DIM)
    d.text((x0,y1+4),'亀山城',font=F[20],fill=DIM)
    cx=x0+p*(x1-x0);i=min(range(len(dist)),key=lambda j:abs(dist[j]/D-p));cy=pts[i][1]
    d.line([(cx,y0),(cx,y1)],fill=(150,110,255),width=3);d.ellipse((cx-8,cy-8,cx+8,cy+8),fill=(150,110,255),outline='white')
    d.text((box[0]+20,box[1]+54),f'水平距離 {p*D/1000:4.1f} / {D/1000:.1f} km　標高 {np.interp(p*D,dist,e):3.0f} m',font=F[26],fill=WHITE)
def render(a,b):
    frames_dir=ROOT/'cache'/'hn_main';reports=[json.loads(Path(p).read_text()) for p in glob.glob(str(ROOT/'cache'/'hn_main'/'report_*.json'))]
    fr={m['frame']:m for r in reports for m in r['frames']}
    statics={ci:static_layer(ci,sc) for ci,sc in enumerate(timeline)}
    scene_segs={ci:[x for x in segs if x['scene']==ci] for ci in range(len(timeline))}
    import os
    stills=[int(x) for x in os.environ['STILLS'].split(',')] if os.environ.get('STILLS') else None
    out=ROOT/'cache'/f'hn_part_{a}_{b}.mp4';log=(ROOT/'logs'/f'hn_enc_{a}.log').open('wb')
    class _P:
        class stdin:
            write=staticmethod(lambda b:None);close=staticmethod(lambda:None)
        def wait(self):pass
        returncode=0
    proc=_P() if stills else subprocess.Popen(['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','pipe:0','-an','-c:v','h264_nvenc','-preset','p4','-cq','20','-b:v','0','-pix_fmt','yuv420p',str(out)],stdin=subprocess.PIPE,stderr=log)
    layout=[];omitted=0
    try:
        for i in (stills or range(a,min(b,N))):
            m=fr[i];ci=m['scene'];ch=timeline[ci];t=i/30;local=m['local']
            im=Image.open(frames_dir/f'{i:05}.jpg').convert('RGBA');im.alpha_composite(statics[ci]);d=ImageDraw.Draw(im,'RGBA')
            used=[(0,0,1920,170),(0,1015,1920,1080),(1470,185,1885,448),(60,860,1860,1008)]
            seg_list=scene_segs[ci];shown=sum(1 for x in seg_list if t>=x['start'])
            P=(45,190,705,520)
            if ci in (3,4,8):
                panel(d,P,'経路の標高プロファイル（模式経路・現代DEM）',used);profile_chart(d,P,m['army_progress'])
                d.text((P[0]+20,P[3]-34),'直線で結んだ模式経路。実際の街道ではない',font=F[20],fill=DIM)
            if ci==1:
                panel(d,(45,190,820,500),'天正10年（1582）の流れ',used)
                items=['5/17　光秀、備中出陣の準備を命じられる','5/29　信長、少数の供回りで入京','6/1　光秀、亀山城を出発（約1.3万・諸説）','6/2未明　光秀勢、本能寺を包囲']
                for k,txt in enumerate(items):
                    if shown>k:d.text((70,250+k*58),txt,font=F[28],fill=WHITE)
            if ci==2:
                P=(45,190,705,420);panel(d,P,'出発地点',used);d.text((70,250),'亀山城（現・亀岡市）',font=F[32],fill=WHITE);d.text((70,300),f'標高 約{ana["start_elev_m"]:.0f} m（経路始点・現代DEM）',font=F[26],fill=WHITE);d.text((70,345),'兵数約1万3千は一説（史料により異なる）',font=F[24],fill=DIM)
            if ci==3:
                d.rounded_rectangle((45,535,705,672),10,fill=BG,outline=(176,153,100),width=2);used.append((45,535,705,672))
                d.text((65,545),f'峠の標高（出典）　約230 m',font=F[26],fill=WHITE);d.text((65,585),f'模式経路の最高点（DEM）{ana["max_elev_m"]:.0f} m',font=F[26],fill=WHITE);d.text((65,625),f'登り {ana["ascent_m"]:.0f} m / 下り {ana["descent_m"]:.0f} m',font=F[26],fill=WHITE)
            if ci==5:
                panel(d,(45,190,760,430),'二つの「本能寺」',used);d.ellipse((70,255,92,277),fill=COL['honnoji']);d.text((105,247),'当時：蛸薬師通の北、約120m四方',font=F[26],fill=WHITE)
                d.ellipse((70,305,92,327),fill=COL['honnoji_now']);d.text((105,297),'現在：寺町御池（1591–92年に移転）',font=F[26],fill=WHITE);d.text((70,355),f'二地点の距離　約{ana["honnoji_old_to_now_m"]/1000:.2f} km',font=FB[32],fill=GOLD)
            if ci==6:
                d.rounded_rectangle((45,190,820,330),12,fill=BG,outline=(176,153,100),width=2);used.append((45,190,820,330))
                d.text((70,205),'6/2 午前4時ごろ（諸説）',font=FB[32],fill=GOLD);d.text((70,255),'包囲の配置・炎は説明用の演出',font=F[26],fill=WHITE);d.text((70,292),'側近：20〜30人とも150人以上とも（諸説）',font=F[24],fill=DIM)
            if ci==7:
                panel(d,(45,190,760,380),'本能寺跡 ↔ 二条新御所',used);d.text((70,255),f'距離　約{ana["honnoji_to_nijo_m"]/1000:.1f} km',font=FB[32],fill=GOLD);d.text((70,310),'二条側の位置は仮置き（誤差 数百m）',font=F[26],fill=WHITE)
            if ci==8:
                panel(d,(45,535,705,830),'行軍時間の感度分析（速度は仮定）',used);
                for k,v in enumerate(ana['sensitivity']):
                    if shown>=3 or (shown>=2 and False):
                        y=600+k*68;d.text((70,y),f'時速{v["assumed_speed_km_h"]}km',font=F[26],fill=WHITE);L=v['minutes']/360*330;d.rectangle((215,y+8,215+L,y+34),fill=(187,165,110));d.text((222+L,y+2),f'{v["minutes"]/60:.1f}時間',font=F[24],fill=WHITE)
                d.text((70,800),'休息・渡河を含まない。史実の時刻とは照合しない',font=F[20],fill=DIM)
            if ci==9 and shown>=3:
                panel(d,(45,190,800,640),'動機の主な説（結論は出ていない）',used)
                items=['怨恨説（信長への不満）','野望説（天下を狙った）','朝廷守護説','秀吉ライバル視説','黒幕存在説（議論が分かれる）']
                for k,txt in enumerate(items):
                    if t>=seg_list[min(2,len(seg_list)-1)]['start']+k*1.4:d.text((70,250+k*70),'・'+txt,font=F[32],fill=WHITE)
                if shown>=len(seg_list):d.text((70,590),'地形データでは判定できない',font=FB[28],fill=GOLD)
            if ci==10:
                panel(d,(45,190,820,430),'その後',used);d.text((70,250),'6/2　本能寺の変',font=F[32],fill=WHITE);d.text((70,300),'6/13　山崎の戦い（11日後）',font=F[32],fill=WHITE);d.text((70,350),'山崎は地図の南の外側',font=F[26],fill=DIM)
            if ci==11:
                box=(70,200,1400,690);panel(d,box,'出典・制作クレジット',used)
                cr=['地形・写真：国土地理院 地理院タイル（標高・シームレス空中写真）を加工','歴史概要：Wikipedia（日本語版）本能寺の変・本能寺・亀山城・老ノ坂峠（CC BY-SA 4.0）','座標：国土地理院 住所検索（旧本能寺跡・二条付近・経由地）','経路・兵・炎・包囲：本制作の模式表現（史実の再現ではない）','一次史料（信長公記など）の直接校訂は未実施','肖像画・錦絵：Wikimedia Commons（パブリックドメイン）。長興寺・本徳寺・総見寺・高台寺・名古屋市蔵','音声：VOICEVOX:四国めたん　／　制作：Blender + Pillow + FFmpeg']
                for k,txt in enumerate(cr):d.text((95,262+k*54),txt,font=F[24],fill=WHITE)
            draw_cards(im,d,ci,t,local,shown,used)
            d=ImageDraw.Draw(im,'RGBA')
            if ci==0:
                d.text((960-tw(d,'天正10年',FB[64])/2,330),'天正10年',font=FB[64],fill=GOLD);d.text((960-tw(d,'6月2日',FB[64])/2,415),'6月2日',font=FB[64],fill=WHITE)
            for L in m['labels']:
                if not(.04<L['x']<.96 and .2<L['y']<.8 and L['depth']>0):continue
                if ci==8 and L['id']=='army' and False:continue
                bx=label(d,NAME[L['id']],L['x']*1920,L['y']*1080,used,COL[L['id']])
                if not bx:omitted+=1
            active=next((x for x in seg_list if x['start']<=t<x['end']),None);sub=None
            if active:
                f=F[46];lines=wrap(d,active['text'],f,1700)
                if len(lines)>2:f=F[40];lines=wrap(d,active['text'],f,1720)
                assert len(lines)<=2,active['text'];sub=(60,860,1860,1008);d.rounded_rectangle(sub,12,fill=(5,18,29,240))
                for j,txt in enumerate(lines):
                    w=tw(d,txt,f);assert w<1760;d.text(((1920-w)/2,872+j*62),txt,font=f,fill='#fffcef')
            d.rectangle((48,1010,48+1824*(i+1)/N,1015),fill=(201,173,112))
            proc.stdin.write(im.convert('RGB').tobytes())
            if stills:im.convert('RGB').save(ROOT/'cache'/f'still_{i}.png')
            if i%30==0:layout.append(dict(frame=i,scene=ci,subtitle_box=sub))
            if i%600==0:print(a,i,flush=True)
    finally:
        proc.stdin.close();proc.wait();log.close()
    assert proc.returncode==0
    (ROOT/'cache'/f'hn_part_{a}_{b}.json').write_text(json.dumps(dict(range=[a,b],omitted_labels=omitted,layout=layout),ensure_ascii=False),encoding='utf8')
def final():
    parts=sorted(ROOT.glob('cache/hn_part_*.mp4'),key=lambda p:int(p.stem.split('_')[2]))
    lst=ROOT/'cache'/'hn_parts.txt';lst.write_text(''.join(f"file '{p.as_posix()}'\n" for p in parts))
    subprocess.run(['ffmpeg','-y','-v','warning','-f','concat','-safe','0','-i',str(lst),'-i',str(ROOT/'out'/'hn_narration.wav'),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest',str(ROOT/'out'/'honnoji.mp4')],check=True)
if __name__=='__main__':
    if sys.argv[1]=='part':render(int(sys.argv[2]),int(sys.argv[3]))
    elif sys.argv[1]=='final':final()
