"""World-map video compositor: Pillow 2D (Natural Earth 110m, own projections) + narration timeline -> FFmpeg NVENC.
usage: gm_compose.py part A B | gm_compose.py final | gm_compose.py remix DB BGM.wav     (STILLS=f1,f2 env -> png stills, no encode)"""
from pathlib import Path
import json,subprocess,sys,math,glob,os,re
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from hn_text import display
import gm_geo as G
import gm_proj as P
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];FD='C:/Windows/Fonts/';_FC={}
SPEC_F={'sans':('NotoSansJP-VF.ttf',560),'sub':('NotoSansJP-VF.ttf',640),'serif':('NotoSerifJP-VF.ttf',800)}
def vfont(kind,size):
    k=(kind,size)
    if k not in _FC:
        f=ImageFont.truetype(FD+SPEC_F[kind][0],size);f.set_variation_by_axes([SPEC_F[kind][1]]);_FC[k]=f
    return _FC[k]
class _Fam:
    def __init__(s,kind):s.kind=kind
    def __getitem__(s,n):return vfont(s.kind,n)
F=_Fam('sans');FB=_Fam('serif');FSUB=_Fam('sub');SS=2
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
timeline=load('data/gm_timeline.json');audio=load('out/gm_audio_report.json');segs=audio['segments']
N=round(timeline[-1]['end']*30);KEYS=[c['key'] for c in timeline]
BG=(7,24,36,240);GOLD=(239,201,118);WHITE=(245,243,232);DIM=(190,205,208);EDGE=(176,153,100);NAVY=(9,22,34)
C_AFR=(255,150,90);C_GRL=(120,190,255);C_JPN=(170,135,255);LAND=(66,98,112);LINE=(150,178,188)
TITLES={'intro':'アフリカとグリーンランド、どちらが大きい？','why':'なぜ、地図は歪むのか','mercator':'メルカトル図法','measure':'歪みを、計算で測る','others':'ほかの図法','webmap':'ウェブ地図の図法','end':'地図は、間違いなのか'}
# ---------------- geometry (Natural Earth 110m, Antarctica omitted)
COUNTRIES=[c for c in G.load() if c['attr']['ADMIN']!='Antarctica']
RINGS=[];GROUP=[]
for c in COUNTRIES:
    g=1 if c['attr'].get('CONTINENT')=='Africa' else (2 if c['attr']['ADMIN']=='Greenland' else (3 if c['attr']['ADMIN']=='Japan' else 0))
    for r in c['rings']:
        if G.ring_area(r)>0:RINGS.append(np.array(r));GROUP.append(g)
LON=np.concatenate([r[:,0] for r in RINGS]);LAT=np.concatenate([r[:,1] for r in RINGS]);SL=[];o=0
for r in RINGS:SL.append((o,o+len(r)));o+=len(r)
PR={k:np.stack(P.PROJ[k](LON,LAT),1) for k in ('merc','gp','ee','plate')}
def graticule():
    L=[]
    for la in range(-60,91,30):L.append((np.linspace(-180,180,121),np.full(121,float(la))))
    for lo in range(-180,181,30):L.append((np.full(61,float(lo)),np.linspace(-60,85,61)))
    return L
GRAT=graticule();GPR=[{k:np.stack(P.PROJ[k](a,b),1) for k in ('merc','gp','ee','plate')} for a,b in GRAT]
def blend(arrs,w):return sum(arrs[k]*v for k,v in w.items() if v>0)
def fit(XY,rect,margin=.97):
    W,H=rect[2]-rect[0],rect[3]-rect[1];x0,y0=XY.min(0);x1,y1=XY.max(0);s=min(W/(x1-x0),H/(y1-y0))*margin;return (x0+x1)/2,(y0+y1)/2,s
class View:
    def __init__(s,cx,cy,sc,rect):s.cx,s.cy,s.s,s.r=cx,cy,sc,rect;s.W=rect[2]-rect[0];s.H=rect[3]-rect[1]
    def px(s,XY,k=SS):return np.stack([((XY[:,0]-s.cx)*s.s+s.W/2)*k,((s.cy-XY[:,1])*s.s+s.H/2)*k],1)
def draw_map(w,rect,hl=None,grat=True,view=None,tissot=None,alpha=255,clipbox=None):
    """returns an RGBA layer (size of rect, supersampled then reduced) with countries in the blended projection w={'merc':a,'ee':b,..}"""
    hl=hl or {};XY=blend(PR,w);W,H=rect[2]-rect[0],rect[3]-rect[1]
    if view is None:cx,cy,sc=fit(XY,rect);view=View(cx,cy,sc,rect)
    lay=Image.new('RGBA',(W*SS,H*SS),(0,0,0,0));d=ImageDraw.Draw(lay);pts=view.px(XY)
    if grat:
        for gp_ in GPR:
            q=view.px(blend(gp_,w));d.line([tuple(p) for p in q],fill=(120,150,160,110),width=2)
    for (a,b),g in zip(SL,GROUP):
        col=hl.get(g,LAND);poly=[tuple(p) for p in pts[a:b]];d.polygon(poly,fill=col+(255,),outline=LINE+(255,))
    if tissot:
        for (lo,la,rad,col) in tissot:
            th=np.linspace(0,2*np.pi,48);ll=P.dest_point(lo,la,th,np.radians(rad));q=view.px(blend({k:np.stack(P.PROJ[k](ll[0],ll[1]),1) for k in ('merc','gp','ee','plate')},w))
            d.polygon([tuple(p) for p in q],fill=col+(150,),outline=col+(255,))
    out=lay.resize((W,H),Image.BOX)
    if alpha<255:out.putalpha(out.getchannel('A').point(lambda v:int(v*alpha/255)))
    return out,view
# ---------------- text helpers
def tw(d,t,f):return d.textlength(t,font=f)
def wrap(d,text,font,maxw):
    if tw(d,text,font)<=maxw:return [text]
    best=None
    for k in range(1,len(text)):
        l1,l2=text[:k],text[k:];w1,w2=tw(d,l1,font),tw(d,l2,font)
        if w1>maxw or w2>maxw or text[k-1] in '（「『' or text[k] in '）」』、':continue
        score=max(w1,w2)+(400 if ('゠'<=text[k-1]<='ヿ' and '゠'<=text[k]<='ヿ') else 0)+(0 if text[k-1] in '、，。' else (70 if text[k-1] in 'はがをにのでとも' and not ('\u4e00'<=text[k]<='\u9fff' and '\u4e00'<=text[k-1]<='\u9fff') else 160))
        if best is None or score<best[0]:best=(score,[l1,l2])
    if best:return best[1]
    lines=[];cur=''
    for ch in text:
        if tw(d,cur+ch,font)>maxw and cur:lines.append(cur);cur=ch
        else:cur+=ch
    lines.append(cur);return lines
def panel(d,box,title=None):
    d.rounded_rectangle(box,12,fill=BG,outline=EDGE,width=2)
    if title:d.text((box[0]+22,box[1]+12),title,font=FB[36],fill=GOLD)
def line_text(d,xy,text,font=F[40],fill=WHITE,a=1.0,stroke=False):
    kw=dict(stroke_width=4,stroke_fill=(5,10,16,int(255*a))) if stroke else {}
    d.text(xy,text,font=font,fill=tuple(fill[:3])+(int(255*a),),**kw)
def ptext(d,x,y,text,font,maxw,fill=WHITE,a=1.0,stroke=False):
    lh=int(font.size*1.32)
    for l in wrap(d,text,font,maxw):line_text(d,(x,y),l,font,fill,a,stroke=stroke);y+=lh
    return y
def ease(x):x=min(1,max(0,x));return x*x*(3-2*x)
class Ctx:
    def __init__(s,ci,t):
        s.ci=ci;s.t=t;s.key=KEYS[ci];ch=timeline[ci];s.local=min(1,max(0,(t-ch['start'])/ch['duration']));s.segl=[x for x in segs if x['scene']==ci];s.st=[x['start'] for x in s.segl]
    def on(s,i):return i<len(s.st) and s.t>=s.st[i]
    def a(s,i,dur=.5):return 0.0 if not s.on(i) else min(1,(s.t-s.st[i])/dur)
    def idx(s):return sum(1 for x in s.st if s.t>=x)-1
    def prog(s,i,j,dur=None):
        """0..1 progress from start of sentence i to start (or end) of sentence j"""
        t0=s.st[min(i,len(s.st)-1)];t1=s.segl[min(j,len(s.segl)-1)]['end'] if dur is None else t0+dur;return min(1,max(0,(s.t-t0)/max(t1-t0,1e-6)))
def header(d,key):
    d.text((48,16),TITLES[key],font=FB[60],fill=WHITE,stroke_width=5,stroke_fill=(5,10,16));d.text((48,94),'地図の歪みを検証する',font=F[28],fill=(200,210,214),stroke_width=4,stroke_fill=(5,10,16))
MAP_R=(50,165,1150,845)
_jr=[r for r,g in zip(RINGS,GROUP) if g==3]
_v=np.concatenate([np.stack([np.cos(np.radians(r[:,1]))*np.cos(np.radians(r[:,0])),np.cos(np.radians(r[:,1]))*np.sin(np.radians(r[:,0])),np.sin(np.radians(r[:,1]))],1) for r in _jr]).mean(0)
JP_LON0=math.degrees(math.atan2(_v[1],_v[0]));JP_LAT0=math.degrees(math.asin(_v[2]/np.linalg.norm(_v)));JP_DELTA=60.0-JP_LAT0   # centroid of Japan -> 60N along its meridian
def shapes_ratio(d,x,y,a,hscale=1.0):
    """two squares with areas proportional to Africa (30.0M) and Greenland (2.17M km2): side ratio sqrt(13.8)"""
    sa=128;sg=sa/math.sqrt(30.04/2.19)
    d.rectangle((x,y,x+sa,y+sa),fill=C_AFR+(int(255*a),));d.rectangle((x+sa+30,y+sa-sg,x+sa+30+sg,y+sa),fill=C_GRL+(int(255*a),))
    line_text(d,(x,y+sa+6),'アフリカ',F[28],WHITE,a);line_text(d,(x+sa+14,y+sa+6),'グリーンランド',F[28],WHITE,a)
# ---------------- scenes
def sc_intro(im,d,cx):
    lay,view=draw_map({'merc':1},MAP_R,{1:C_AFR,2:C_GRL});im.alpha_composite(lay,(MAP_R[0],MAP_R[1]))
    for i,(txt,lo,la,col,dx,dy) in enumerate([('アフリカ',20,5,C_AFR,0,0),('グリーンランド',-42,72,C_GRL,0,-60)]):
        x,y=view.px(np.stack([np.array(P.PROJ['merc'](lo,la))],0) if False else np.array([[P.merc(np.array([lo]),np.array([la]))[0][0],P.merc(np.array([lo]),np.array([la]))[1][0]]]),1)[0]
        a=cx.a(0,.6);line_text(d,(MAP_R[0]+x-70+dx,MAP_R[1]+y-20+dy),txt,F[34],WHITE,a,stroke=True)
    line_text(d,(MAP_R[0]+10,MAP_R[1]-4),'メルカトル図法',FB[34],GOLD,cx.a(0),stroke=True)
    px_=1190
    if cx.on(3):
        panel(d,(px_,170,1870,640),'実際の面積')
        line_text(d,(px_+30,236),'アフリカ',F[34],C_AFR,cx.a(3));line_text(d,(px_+260,230),'約3,000万 km²',F[44],WHITE,cx.a(3))
        if cx.on(4):line_text(d,(px_+30,306),'グリーンランド',F[34],C_GRL,cx.a(4));line_text(d,(px_+330,300),'約217万 km²',F[44],WHITE,cx.a(4))
        if cx.on(5):
            line_text(d,(px_+30,376),'差',F[40],DIM,cx.a(5));line_text(d,(px_+110,356),'約14倍',FB[72],GOLD,cx.a(5));shapes_ratio(d,px_+60,458,cx.a(5))
    if cx.on(6):
        panel(d,(px_,656,1870,845));a=cx.a(6)
        for j,l in enumerate(wrap(d,'世界地図は、陸地の大きさを間違えているのか？',F[40],620)):line_text(d,(px_+30,668+j*50),l,F[40],WHITE,a)
        if cx.on(7):line_text(d,(px_+30,778),'計算で確かめる',F[38],GOLD,cx.a(7))
        if cx.on(8):line_text(d,(px_+300,778),'→ 間違いか考える',F[38],GOLD,cx.a(8))
def ortho(lon,lat,lon0,lat0=18):
    l=np.radians(lon-lon0);p=np.radians(lat);p0=math.radians(lat0)
    x=np.cos(p)*np.sin(l);y=math.cos(p0)*np.sin(p)-math.sin(p0)*np.cos(p)*np.cos(l);vis=math.sin(p0)*np.sin(p)+math.cos(p0)*np.cos(p)*np.cos(l)
    return x,y,vis
def draw_globe(im,center,rad,lon0,hl=True):
    S=2;sz=int(rad*2+20);lay=Image.new('RGBA',(sz*S,sz*S),(0,0,0,0));d=ImageDraw.Draw(lay);c=sz*S/2
    d.ellipse((c-rad*S,c-rad*S,c+rad*S,c+rad*S),fill=(14,40,60,255),outline=EDGE+(255,),width=3)
    for (a,b),g in zip(SL,GROUP):
        x,y,v=ortho(LON[a:b],LAT[a:b],lon0);r=np.hypot(x,y)+1e-9;f=np.where(v>0,1.0,1.0/r)
        if (v>0).sum()<3:continue
        pts=[(c+xx*ff*rad*S,c-yy*ff*rad*S) for xx,yy,ff in zip(x,y,f)];col=(C_AFR if g==1 else C_GRL if g==2 else LAND) if hl else LAND
        d.polygon(pts,fill=col+(255,),outline=LINE+(255,))
    for la in (-60,-30,0,30,60):
        lo=np.linspace(-180,180,181);x,y,v=ortho(lo,np.full(181,float(la)),lon0);seg=[(c+xx*rad*S,c-yy*rad*S) for xx,yy,vv in zip(x,y,v) if vv>0];
        if len(seg)>1:d.line(seg,fill=(120,150,160,140),width=2)
    out=lay.resize((sz,sz),Image.BOX);im.alpha_composite(out,(int(center[0]-sz/2),int(center[1]-sz/2)))
def gore_lines(d,x0,y0,s,a):
    """12 sinusoidal gores of the sphere (peeled orange): 30-degree wide, with gaps"""
    for k in range(12):
        lo0=-180+30*k;mid=lo0+15;gx=x0+k*(math.pi/6*s+10)+math.pi/12*s
        edge=[];
        for la in np.linspace(-90,90,60):
            edge.append((gx+math.radians(lo0-mid)*math.cos(math.radians(la))*s,y0-math.radians(la)*s))
        edge2=[(gx+math.radians(lo0+30-mid)*math.cos(math.radians(la))*s,y0-math.radians(la)*s) for la in np.linspace(90,-90,60)]
        d.polygon(edge+edge2,fill=(60,130,150,int(160*a)),outline=(200,220,225,int(255*a)))
        for la in (-60,-30,0,30,60):
            d.line([(gx+math.radians(lo)*math.cos(math.radians(la))*s,y0-math.radians(la)*s) for lo in np.linspace(-15,15,10)],fill=(200,220,225,int(160*a)),width=2)
def stretched_grid(d,x0,y0,w,h,a):
    """plate carree: 15-degree bands coloured by horizontal stretch 1/cos(lat)"""
    for i in range(12):
        la0=-90+15*i;la1=la0+15;mid=math.radians((la0+la1)/2);st=min(1/math.cos(mid),6.0);t=(st-1)/5
        col=(int(60+195*t),int(150-90*t),int(150-110*t))
        for j in range(24):
            xa=x0+w*j/24;xb=x0+w*(j+1)/24;ya=y0+h*(1-(la1+90)/180);yb=y0+h*(1-(la0+90)/180);d.rectangle((xa,ya,xb,yb),fill=col+(int(235*a),),outline=(8,20,30,int(255*a)))
def sc_why(im,d,cx):
    draw_globe(im,(330,520),250,15+cx.t*8)
    if cx.on(0):line_text(d,(70,190),'地球：球体',F[40],WHITE,cx.a(0),stroke=True)
    if cx.on(1):line_text(d,(780,190),'地図：平らな紙や画面',F[40],WHITE,cx.a(1),stroke=True)
    X0,Y0=640,265
    if cx.on(3) and not cx.on(5):
        panel(d,(640,250,1870,840),'切れ目を細かく入れた皮（模式図）');ov=Image.new('RGBA',(1920,1080),(0,0,0,0));od=ImageDraw.Draw(ov);gore_lines(od,672,545,150,cx.a(3));im.alpha_composite(ov)
        if cx.on(4):line_text(d,(665,798),'平らに近づくが、陸地や海がつながっていない',F[32],WHITE,cx.a(4))
    if cx.on(5):
        panel(d,(640,250,1870,840),'つないだまま平らにすると');ov=Image.new('RGBA',(1920,1080),(0,0,0,0));od=ImageDraw.Draw(ov);stretched_grid(od,670,320,1170,440,cx.a(5));im.alpha_composite(ov)
        if cx.on(6):line_text(d,(670,775),'極に近いほど、横に大きく伸びる（赤い所）',F[34],WHITE,cx.a(6))
    if cx.on(8):
        panel(d,(640,250,1870,840),'地図が守れる性質');
        for k,(t_,i_) in enumerate([('面積',9),('形',9),('角度',9),('距離',9)]):
            if cx.on(9):d.rounded_rectangle((680+k*290,330,940+k*290,430),14,outline=GOLD+(int(255*cx.a(9)),),width=3,fill=(12,34,50,int(255*cx.a(9))));line_text(d,(724+k*290,352),t_,F[44],WHITE,cx.a(9))
        if cx.on(10):line_text(d,(680,500),'面積 と 形 を同時に守ることは',F[44],WHITE,cx.a(10));line_text(d,(680,566),'できない',FB[72],GOLD,cx.a(10))
        if cx.on(11):line_text(d,(680,690),'だから、世界地図には いくつもの種類がある',F[40],WHITE,cx.a(11))
def sc_mercator(im,d,cx):
    mr=(50,165,1150,845);lay,view=draw_map({'merc':1},mr,{1:C_AFR,2:C_GRL},alpha=255);im.alpha_composite(lay,(mr[0],mr[1]))
    mpx=lambda lo,la:(lambda a,b:(mr[0]+view.px(np.array([[a[0],b[0]]]),1)[0][0],mr[1]+view.px(np.array([[a[0],b[0]]]),1)[0][1]))(*P.merc(np.array([lo]),np.array([la])))
    ov=Image.new('RGBA',(1920,1080),(0,0,0,0));od=ImageDraw.Draw(ov)
    if cx.on(2) and not cx.on(4):
        panel(d,(1190,170,1870,430),'1569年の世界地図の題名の一部');line_text(d,(1215,242),'ad usum navigantium',F[38],GOLD,cx.a(2));line_text(d,(1215,304),'＝ 航海者の使用のために',F[36],WHITE,cx.a(2));line_text(d,(1215,364),'（長いラテン語の題名の一部）',F[28],DIM,cx.a(2))
    if cx.on(4):
        panel(d,(1190,170,1870,470),'メルカトル図法の特徴');line_text(d,(1215,236),'線と線が交わる角度が',F[40],WHITE,cx.a(4));line_text(d,(1215,292),'狭い範囲で、正しく表される',F[40],GOLD,cx.a(4))
        if cx.on(5):
            line_text(d,(1215,358),'一定の針路 ＝ 直線',F[44],WHITE,cx.a(5))
    if cx.on(5) and not cx.on(7):
        a0=mpx(-10,38);a1=mpx(-80,22);al=int(255*cx.a(5));od.line([a0,a1],fill=C_AFR+(al,),width=6)
        for q in (a0,a1):od.ellipse((q[0]-9,q[1]-9,q[0]+9,q[1]+9),fill=WHITE+(al,))
        # equal-angle ticks along the line: meridians crossing the straight line
        for lo in range(-70,-15,15):
            la=38+(22-38)*(lo+10)/(-80+10);q=mpx(lo,la);od.line([(q[0],q[1]-60),(q[0],q[1]+60)],fill=(255,255,255,int(90*cx.a(5))),width=2)
    if cx.on(7):
        a=cx.a(7);lo1,la1,lo2,la2=-0.13,51.5,-74.0,40.7;gx,gy=P.great_circle(lo1,la1,lo2,la2)
        q=[mpx(x,y) for x,y in zip(gx,gy)];od.line(q,fill=C_GRL+(int(255*a),),width=7);od.line([mpx(lo1,la1),mpx(lo2,la2)],fill=C_AFR+(int(255*a),),width=5)
        for lo,la in ((lo1,la1),(lo2,la2)):
            z=mpx(lo,la);od.ellipse((z[0]-9,z[1]-9,z[0]+9,z[1]+9),fill=WHITE+(int(255*a),))
        panel(d,(1190,500,1870,720));line_text(d,(1215,520),'■ 最短（大圏）航路',F[36],C_GRL,a);line_text(d,(1215,578),'■ 一定の針路',F[36],C_AFR,a);line_text(d,(1215,646),'最短とは限らない',F[40],WHITE,cx.a(8))
    if cx.on(9):
        a=cx.a(9)
        for la,lab in ((60,'緯度60°'),(80,'緯度80°')):
            q=mpx(-178,la);q2=mpx(178,la);od.line([q,q2],fill=GOLD+(int(200*a),),width=3);line_text(d,(q[0]+6,q[1]-40),lab,F[30],GOLD,a,stroke=True)
        line_text(d,(1215,760),'高緯度ほど、面積が大きく見える',F[38],GOLD,cx.a(9))
    im.alpha_composite(ov)
def sc_measure(im,d,cx):
    i=cx.idx()
    if i<6:
        panel(d,(50,170,830,660),'歪みの倍率（地球を球体とみなす）')
        if cx.on(1):line_text(d,(80,236),'長さの倍率',F[36],DIM,cx.a(1));line_text(d,(80,284),'＝ 1 ÷ cos（緯度）',F[44],WHITE,cx.a(1))
        if cx.on(3):line_text(d,(80,370),'面積の倍率',F[36],DIM,cx.a(3));line_text(d,(80,418),'＝（1 ÷ cos 緯度）²',F[44],WHITE,cx.a(3))
        if cx.on(4):line_text(d,(80,500),'緯度60°　→ 面積 約4倍',F[44],GOLD,cx.a(4))
        if cx.on(5):line_text(d,(80,568),'緯度80°　→ 面積 約33倍',F[44],GOLD,cx.a(5))
        gx0,gy0,gx1,gy1=900,230,1850,780;panel(d,(870,170,1870,840),'緯度と面積の倍率')
        d.line([(gx0,gy1),(gx1,gy1)],fill=DIM,width=2);d.line([(gx0,gy0),(gx0,gy1)],fill=DIM,width=2)
        la_max=84;pts=[]
        for la in np.linspace(0,la_max,120):
            f=1/math.cos(math.radians(la))**2;f=min(f,110);pts.append((gx0+(la/la_max)*(gx1-gx0-20),gy1-(math.log10(f)/math.log10(110))*(gy1-gy0-20)))
        show=len(pts) if cx.on(3) else int(len(pts)*max(cx.prog(0,3),0.05) if cx.on(0) else 0);
        if show>1:d.line(pts[:show],fill=GOLD,width=5)
        for la,lab in ((0,'0°'),(30,'30°'),(60,'60°'),(80,'80°')):
            x=gx0+(la/la_max)*(gx1-gx0-20);d.text((x-20,gy1+8),lab,font=F[30],fill=DIM)
        for fv in (1,4,33):
            y=gy1-(math.log10(fv)/math.log10(110))*(gy1-gy0-20);d.line([(gx0-8,y),(gx0,y)],fill=DIM,width=2);d.text((gx0-62,y-18),f'×{fv}',font=F[30],fill=DIM)
        if cx.on(4):
            x=gx0+(60/la_max)*(gx1-gx0-20);y=gy1-(math.log10(4)/math.log10(110))*(gy1-gy0-20);d.ellipse((x-10,y-10,x+10,y+10),fill=WHITE);line_text(d,(x+16,y-52),'60° → 4倍',F[40],WHITE,cx.a(4))
        if cx.on(5):
            x=gx0+(80/la_max)*(gx1-gx0-20);y=gy1-(math.log10(33.16)/math.log10(110))*(gy1-gy0-20);d.ellipse((x-10,y-10,x+10,y+10),fill=WHITE);line_text(d,(x-330,y-12),'80° → 約33倍',F[40],WHITE,cx.a(5))
        d.text((1500,196),'（縦軸は対数）',font=F[26],fill=DIM)
        return
    mr=MAP_R
    if i<=9:
        lay,view=draw_map({'merc':1},mr,{1:C_AFR,2:C_GRL});im.alpha_composite(lay,(mr[0],mr[1]))
        panel(d,(1190,170,1870,740),'見かけの面積の倍率')
        if cx.on(7):line_text(d,(1215,520),'アフリカ：赤道をまたぐ',F[34],C_AFR,cx.a(7));line_text(d,(1215,564),'→ 誇張が小さい',F[34],WHITE,cx.a(7))
        if cx.on(8):line_text(d,(1215,630),'グリーンランド：北緯60°〜83.6°',F[34],C_GRL,cx.a(8));line_text(d,(1215,674),'→ 誇張が大きい',F[34],WHITE,cx.a(8))
        for k,(la,txt) in enumerate([(0,'赤道　　×1.0'),(30,'緯度30°　×1.3'),(60,'緯度60°　×4.0'),(80,'緯度80°　×33')]):
            if cx.on(7 if k<2 else 8):line_text(d,(1215,236+k*70),txt,F[40],WHITE,cx.a(7 if k<2 else 8))
        return
    if i in (10,11):
        tis=[(lo,la,6,(255,220,120)) for la in (0,30,55,72) for lo in range(-150,151,50)]
        lay,view=draw_map({'merc':1},mr,{1:C_AFR,2:C_GRL},grat=True,tissot=tis if cx.on(11) else [(lo,la,6,(255,220,120)) for la in (0,30,55,72) for lo in (-150,-50,50,150)] if cx.on(10) else None);im.alpha_composite(lay,(mr[0],mr[1]))
        panel(d,(1190,170,1870,480),'同じ大きさの円');yy=ptext(d,1215,236,'地球の上では、すべて同じ大きさ',F[36],610,WHITE,cx.a(10))
        if cx.on(11):ptext(d,1215,yy+14,'メルカトル図法では、北の円ほど大きく見える',F[36],610,GOLD,cx.a(11))
        return
    # Japan moved north (zoomed Mercator)
    base,_=None,None;cxm,cym=P.merc(np.array([138.0]),np.array([48.0]));s0=380.0;rect=(50,165,1150,845);view=View(float(cxm[0]),float(cym[0]),s0,rect);XY=PR['merc']
    lay=Image.new('RGBA',(1100*SS,680*SS),(0,0,0,0));dd=ImageDraw.Draw(lay);pts=view.px(XY)
    for (a,b),g in zip(SL,GROUP):dd.polygon([tuple(p) for p in pts[a:b]],fill=(LAND if g!=3 else C_JPN)+(255,) if True else None,outline=LINE+(255,)) if g!=3 else None
    sh=ease(cx.prog(12,13,3.0)) if cx.on(12) else 0.0;dlat=JP_DELTA*sh
    ghost=[];moved=[]
    for (a,b),g in zip(SL,GROUP):
        if g!=3:continue
        lo,la=LON[a:b],LAT[a:b];x,y=P.merc(lo,la);xy=np.stack([x,y],1);ghost.append(view.px(xy));lo2,la2=P.move_north(lo,la,JP_LON0,dlat);x2,y2=P.merc(lo2,la2);moved.append(view.px(np.stack([x2,y2],1)))
    for gq in ghost:dd.polygon([tuple(p) for p in gq],fill=C_JPN+(110,),outline=C_JPN+(255,))
    for mq in moved:dd.polygon([tuple(p) for p in mq],fill=C_JPN+(255,),outline=WHITE+(255,))
    lat_line=lambda la,col:dd.line([tuple(view.px(np.array([[-3.2,P.merc(np.array([0.]),np.array([la]))[1][0]],[6.3,P.merc(np.array([0.]),np.array([la]))[1][0]]]))[0]),tuple(view.px(np.array([[-3.2,P.merc(np.array([0.]),np.array([la]))[1][0]],[6.3,P.merc(np.array([0.]),np.array([la]))[1][0]]]))[1])],fill=col+(180,),width=3)
    lat_line(37.3,C_JPN);lat_line(60,GOLD)
    out=lay.resize((1100,680),Image.BOX);im.alpha_composite(out,(rect[0],rect[1]))
    for la,txt,col in ((37.3,'北緯37°（現在の日本）',C_JPN),(60,'北緯60°',GOLD)):
        yy=view.px(np.array([[0.0,P.merc(np.array([0.]),np.array([la]))[1][0]]]),1)[0][1]+rect[1];line_text(d,(rect[0]+12,yy-40),txt,F[30],col,1.0,stroke=True)
    panel(d,(1190,170,1870,520),'日本を北へ動かす');line_text(d,(1215,236),'球面上で、形を変えずに北へ',F[36],WHITE,cx.a(12))
    if cx.on(13):line_text(d,(1215,300),'北緯60°付近まで',F[40],WHITE,cx.a(13));line_text(d,(1215,356),'見かけの面積',F[40],WHITE,cx.a(13));line_text(d,(1215,412),'約2.6倍',FB[72],GOLD,cx.a(13))
    if cx.on(14):line_text(d,(1215,540),'見かけの大きさは、緯度で変わる',F[38],GOLD,cx.a(14))
def sc_others(im,d,cx):
    i=cx.idx()
    rect=(50,165,1150,845)
    if i<3:w={'merc':1.0}
    if i<=0:w={'merc':1.0}
    if i==1:w={'merc':1-ease(cx.prog(1,2,3.0)),'gp':ease(cx.prog(1,2,3.0))}
    elif i==2:w={'gp':1.0}
    elif i==3:w={'gp':1-ease(cx.prog(3,4,3.0)),'ee':ease(cx.prog(3,4,3.0))}
    elif i>=4:w={'ee':1.0}
    if i==5:
        u=cx.prog(5,5);tri=1-abs(2*u-1);w={'merc':ease(tri),'ee':1-ease(tri)}
    w={k:v for k,v in w.items() if v>0} or {'merc':1.0}
    tis=[(lo,la,6,(255,220,120)) for la in (0,30,55,72) for lo in range(-150,151,75)] if i>=7 else None
    lay,view=draw_map(w,rect,{1:C_AFR,2:C_GRL},tissot=tis);im.alpha_composite(lay,(rect[0],rect[1]))
    names={0:'メルカトル図法',1:'ガル・ピーターズ図法',2:'ガル・ピーターズ図法',3:'イコール・アース図法',4:'イコール・アース図法'}
    nm=('メルカトル図法' if w.get('merc',0)>.5 else 'イコール・アース図法') if i==5 else 'メルカトル図法' if i==0 else '→ ガル・ピーターズ図法' if i==1 else 'ガル・ピーターズ図法' if i==2 else '→ イコール・アース図法' if i==3 else 'イコール・アース図法'
    line_text(d,(70,175),nm,FB[40],GOLD,1.0,stroke=True)
    px_=1190
    if cx.on(1):
        panel(d,(px_,170,1870,420),'2017年');line_text(d,(px_+25,236),'アメリカ・ボストンの公立学校が',F[34],WHITE,cx.a(1));line_text(d,(px_+25,284),'面積を保つ図法の地図を採用',F[34],WHITE,cx.a(1))
        if cx.on(2):line_text(d,(px_+25,346),'形の歪みが大きいという議論も',F[34],GOLD,cx.a(2))
    if cx.on(3):
        panel(d,(px_,440,1870,720),'2018年　イコール・アース図法');line_text(d,(px_+25,506),'面積を保つ図法の一つ',F[36],WHITE,cx.a(3))
        if cx.on(4):line_text(d,(px_+25,562),'見た目のバランスを重視した',F[34],DIM,cx.a(4));line_text(d,(px_+25,606),'ロビンソン図法に着想を得た',F[34],DIM,cx.a(4))
    if cx.on(6):
        panel(d,(px_,170,1870,420),'見かけの面積比（アフリカ÷グリーンランド）' if False else '見かけの面積比')
        line_text(d,(px_+25,226),'アフリカ ÷ グリーンランド',F[28],DIM,cx.a(6));line_text(d,(px_+25,270),'メルカトル図法',F[32],DIM,cx.a(6));line_text(d,(px_+440,262),'約0.9倍',F[44],WHITE,cx.a(6))
        line_text(d,(px_+25,326),'イコール・アース図法',F[32],DIM,cx.a(6));line_text(d,(px_+440,318),'約14倍',F[44],GOLD,cx.a(6))
        line_text(d,(px_+25,376),'（実際の比率に一致）',F[28],DIM,cx.a(6))
    if cx.on(7):
        panel(d,(px_,440,1870,720));line_text(d,(px_+25,470),'面積を保つ図法も、万能ではない',F[36],WHITE,cx.a(7))
        if cx.on(8):line_text(d,(px_+25,536),'大陸の形は、歪む（黄色い円）',F[36],GOLD,cx.a(8))
        if cx.on(9):line_text(d,(px_+25,620),'絶対の正解は、ない',FB[48],WHITE,cx.a(9))
def sc_webmap(im,d,cx):
    i=cx.idx()
    if i<=3:
        panel(d,(50,170,1000,520),'ウェブメルカトル');line_text(d,(80,236),'メルカトル図法を基にした方式',F[40],WHITE,cx.a(0))
        if cx.on(1):line_text(d,(80,300),'主なウェブ地図の多くが採用（とされる）',F[36],DIM,cx.a(1))
        if cx.on(2):
            a=cx.a(2);panel(d,(1030,170,1870,840),'狭い範囲の形（角度）が保たれる')
            tis=[(lo,la,6,(255,220,120)) for la in (0,35,60) for lo in (-120,-40,40,120)]
            lay,_=draw_map({'merc':1},(1050,230,1850,540),{1:C_AFR,2:C_GRL},grat=False,tissot=tis);im.alpha_composite(lay,(1050,230));ptext(d,1060,545,'メルカトル図法：円は円のまま（大きさは変わる）',F[32],780,WHITE,a)
            lay,_=draw_map({'ee':1},(1050,620,1850,830),{1:C_AFR,2:C_GRL},grat=False,tissot=tis);im.alpha_composite(lay,(1050,620));line_text(d,(1060,586),'比べて、イコール・アース図法：円が歪む',F[30],DIM,a)
        if cx.on(3):line_text(d,(80,380),'理由：角度を保ちやすい／計算が簡単',F[36],WHITE,cx.a(3))
        return
    if i<=5:
        rect=(50,200,690,840);lay,view=draw_map({'merc':1},(50,200,690,840),{1:C_AFR,2:C_GRL},grat=False,view=View(0,0,0,(50,200,690,840)) if False else None);
        # square world (Web Mercator limit 85.05): clip the Mercator map into a square and overlay tile grids
        sq=(60,200,60+620,200+620);XY=PR['merc'];Lm=math.pi;view=View(0,0,620/(2*Lm),sq);lay=Image.new('RGBA',(620*SS,620*SS),(0,0,0,0));dd=ImageDraw.Draw(lay);pts=view.px(XY)
        dd.rectangle((0,0,620*SS,620*SS),fill=(14,40,60,255))
        for (a,b),g in zip(SL,GROUP):dd.polygon([tuple(p) for p in pts[a:b]],fill=(C_AFR if g==1 else C_GRL if g==2 else LAND)+(255,),outline=LINE+(255,))
        out=lay.resize((620,620),Image.BOX);im.alpha_composite(out,(sq[0],sq[1]))
        z=0 if not cx.on(4) else min(3,1+int(cx.prog(4,5,6.0)*3))
        for zz in range(1,z+1):
            n=2**zz
            for k in range(1,n):d.line([(sq[0]+620*k/n,sq[1]),(sq[0]+620*k/n,sq[3])],fill=(255,255,255,140 if zz<z else 220),width=2 if zz<z else 3);d.line([(sq[0],sq[1]+620*k/n),(sq[2],sq[1]+620*k/n)],fill=(255,255,255,140 if zz<z else 220),width=2 if zz<z else 3)
        d.rectangle(sq,outline=GOLD,width=4)
        if cx.on(4):panel(d,(720,200,1870,620),'地図を、正方形のタイルに分ける')
        if cx.on(4):line_text(d,(750,266),'拡大するほど、タイルが細かくなる',F[38],WHITE,cx.a(4));line_text(d,(750,330),f'分割：{2**z}×{2**z}',F[44],GOLD,cx.a(4))
        if cx.on(5):line_text(d,(750,410),'この方式と、この図法は相性がよかった',F[36],WHITE,cx.a(5));line_text(d,(750,466),'と説明される',F[36],DIM,cx.a(5))
        if cx.on(4):line_text(d,(750,550),'（世界を正方形に収める）',F[30],DIM,cx.a(4))
        return
    panel(d,(50,170,930,420),'道案内の地図');line_text(d,(80,236),'道の形・交わる角度が大事',F[40],WHITE,cx.a(6));line_text(d,(80,300),'→ メルカトル系が向く',F[44],GOLD,cx.a(6))
    lay,_=draw_map({'merc':1},(80,440,900,850),{1:C_AFR,2:C_GRL},grat=False,alpha=int(255*cx.a(6)));im.alpha_composite(lay,(80,440))
    if cx.on(7):
        panel(d,(960,170,1870,420),'国の大きさの比較');line_text(d,(990,236),'面積を保つ図法が向く',F[40],WHITE,cx.a(7));line_text(d,(990,300),'→ イコール・アースなど',F[44],GOLD,cx.a(7))
        lay,_=draw_map({'ee':1},(990,440,1850,850),{1:C_AFR,2:C_GRL},grat=False,alpha=int(255*cx.a(7)));im.alpha_composite(lay,(990,440))
    if cx.on(8):line_text(d,(260,800),'同じ地球でも、目的が違えば、選ぶ地図が違う',FB[44],WHITE,cx.a(8),stroke=True)
def sc_end(im,d,cx):
    rows=[('図法','守るもの','犠牲にするもの','向く目的'),('メルカトル図法','角度・一定の針路','面積（高緯度で誇張）','航海、ウェブ地図の道案内'),('ガル・ピーターズ図法','面積','形（大きく歪む）','面積の比較'),('イコール・アース図法','面積','形（大陸の形が歪む）','面積の比較')]
    xs=[70,500,860,1330];y0=190
    panel(d,(50,170,1870,610))
    for r,row in enumerate(rows):
        if r==0 or cx.on(r):
            a=1.0 if r==0 else cx.a(r)
            for c,txt in enumerate(row):ptext(d,xs[c],y0+r*98-(0 if r else 0),txt,F[34] if r else F[30],[400,340,440,500][c],GOLD if r==0 else WHITE,a if r else 1.0)
            if r:d.line([(70,y0+r*98-14),(1850,y0+r*98-14)],fill=EDGE+(120,),width=1)
    if cx.on(5):
        d.rounded_rectangle((50,640,930,840),14,fill=BG,outline=GOLD,width=3);line_text(d,(80,656),'分かること',F[40],GOLD,cx.a(5));ptext(d,80,716,'何かを守るために、何かを犠牲にする',F[34],800,WHITE,cx.a(6))
    if cx.on(7):
        d.rounded_rectangle((960,640,1870,840),14,fill=BG,outline=GOLD,width=3);line_text(d,(990,656),'一つに決められないこと',F[40],GOLD,cx.a(7));ptext(d,990,716,'最適な図法は、使う目的しだい',F[34],840,WHITE,cx.a(8))
SCENES={'intro':sc_intro,'why':sc_why,'mercator':sc_mercator,'measure':sc_measure,'others':sc_others,'webmap':sc_webmap,'end':sc_end}
# ---------------- subtitles (46px, max 2 lines, long sentences are paged instead of shrunk)
_SUBP={}
def sub_lines(d,seg,f,t):
    k=seg['start']
    if k not in _SUBP:
        txt=display(seg['text']);ls=wrap(d,txt,f,1720)
        if len(ls)<=2:_SUBP[k]=[(ls,seg['start'],seg['end'])]
        else:
            allw=[];cur=''
            for ch in txt:
                if tw(d,cur+ch,f)>1720 and cur:allw.append(cur);cur=ch
                else:cur+=ch
            allw.append(cur);pages=[allw[i:i+2] for i in range(0,len(allw),2)];tot=sum(len(''.join(p)) for p in pages);cum=0;out=[]
            for p in pages:
                n=len(''.join(p));out.append((p,seg['start']+(seg['end']-seg['start'])*cum/tot,seg['start']+(seg['end']-seg['start'])*(cum+n)/tot));cum+=n
            _SUBP[k]=out
    for ls,s0,s1 in _SUBP[k]:
        if t<s1:return ls
    return _SUBP[k][-1][0]
def render_frame(i):
    t=i/30;ci=next(k for k,c in enumerate(timeline) if t<c['end']+1e-9);cx=Ctx(ci,t)
    im=Image.new('RGBA',(1920,1080),NAVY+(255,));d=ImageDraw.Draw(im,'RGBA')
    header(d,cx.key);SCENES[cx.key](im,d,cx);d=ImageDraw.Draw(im,'RGBA')
    active=next((x for x in cx.segl if x['start']<=t<x['end']),None)
    if active:
        f=FSUB[46];lines=sub_lines(d,active,f,t);sub=(60,860,1860,1008);d.rounded_rectangle(sub,12,fill=(5,18,29,242))
        for j,txt in enumerate(lines):
            w=tw(d,txt,f);assert w<1760;d.text(((1920-w)/2,872+j*62),txt,font=f,fill='#fffcef')
    d.rectangle((48,1012,48+1824*(i+1)/N,1018),fill=(201,173,112));return im
def render(a,b):
    stills=[int(x) for x in os.environ['STILLS'].split(',')] if os.environ.get('STILLS') else None
    out=ROOT/'cache'/f'gm_part_{a}_{b}.mp4';log=(ROOT/'logs'/f'gm_enc_{a}.log').open('wb')
    class _P:
        class stdin:
            write=staticmethod(lambda b:None);close=staticmethod(lambda:None)
        def wait(self):pass
        returncode=0
    proc=_P() if stills else subprocess.Popen(['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','pipe:0','-an','-c:v','h264_nvenc','-preset','p4','-cq','19','-b:v','0','-pix_fmt','yuv420p',str(out)],stdin=subprocess.PIPE,stderr=log)
    try:
        for i in (stills or range(a,min(b,N))):
            im=render_frame(i);proc.stdin.write(im.convert('RGB').tobytes())
            if stills:im.convert('RGB').save(ROOT/'cache'/f'gmstill_{i}.png')
            if i%600==0:print(a,i,flush=True)
    finally:
        proc.stdin.close();proc.wait();log.close()
    assert proc.returncode==0
    if not stills:(ROOT/'cache'/f'gm_part_{a}_{b}.json').write_text(json.dumps(dict(range=[a,b])),encoding='utf8')
def chk_duration():
    r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(ROOT/'out'/'gm_video.mp4')],capture_output=True,text=True);dur=float(r.stdout.strip())
    assert abs(dur-timeline[-1]['end'])<1.0,f'video {dur:.2f}s != timeline end {timeline[-1]["end"]:.2f}s (truncated parts?)'
def final():
    parts=sorted(ROOT.glob('cache/gm_part_*.mp4'),key=lambda p:int(p.stem.split('_')[2]))
    lst=ROOT/'cache'/'gm_parts.txt';lst.write_text(''.join(f"file '{p.as_posix()}'\n" for p in parts));wav=str(ROOT/'out'/'gm_narration.wav')
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',wav,'-af','loudnorm=I=-15:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True)
    j=json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}',r.stderr,re.S).group(0))
    af=f"loudnorm=I=-15:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
    subprocess.run(['ffmpeg','-y','-v','warning','-f','concat','-safe','0','-i',str(lst),'-i',wav,'-map','0:v','-map','1:a','-c:v','h264_nvenc','-preset','p5','-cq','25','-b:v','0','-pix_fmt','yuv420p','-af',af,'-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest',str(ROOT/'out'/'gm_video.mp4')],check=True)
    chk_duration();print('loudnorm input',j['input_i'],'LUFS')
def remix(bgm_db=-16.0,bgm_file='gm_bgm.wav'):
    nar=str(ROOT/'out'/'gm_narration.wav');bgm=str(ROOT/'out'/bgm_file);mix=str(ROOT/'cache'/'gm_mix.wav')
    fc=f"[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0,asplit=2[n1][n2];[1:a]volume={bgm_db}dB[bg];[bg][n2]sidechaincompress=threshold=0.02:ratio=4:attack=30:release=900:makeup=1[duck];[n1][duck]amix=inputs=2:normalize=0:duration=first[m]"
    subprocess.run(['ffmpeg','-y','-v','warning','-i',nar,'-i',bgm,'-filter_complex',fc,'-map','[m]','-c:a','pcm_s16le',mix],check=True)
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',mix,'-af','loudnorm=I=-15:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True)
    j=json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}',r.stderr,re.S).group(0))
    af=f"loudnorm=I=-15:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
    subprocess.run(['ffmpeg','-y','-v','warning','-i',str(ROOT/'out'/'gm_video_nobgm.mp4'),'-i',mix,'-map','0:v','-map','1:a','-c:v','copy','-af',af,'-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest',str(ROOT/'out'/'gm_video.mp4')],check=True)
    print('mix input',j['input_i'])
if __name__=='__main__':
    if sys.argv[1]=='part':render(int(sys.argv[2]),int(sys.argv[3]))
    elif sys.argv[1]=='final':final()
    elif sys.argv[1]=='remix':remix(float(sys.argv[2]) if len(sys.argv)>2 else -16.0,sys.argv[3] if len(sys.argv)>3 else 'gm_bgm.wav')
