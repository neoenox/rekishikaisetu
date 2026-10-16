"""Honnoji composite v4: 3D frames (Blender) + 2D location-map scenes (GSI hillshade) + Pillow overlays -> FFmpeg NVENC.
Readability: body text >= 30px. usage: hn_compose4.py part A B | hn_compose4.py final"""
from pathlib import Path
import json,subprocess,sys,math,glob,os,re
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from hn_text import display
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
FD='C:/Windows/Fonts/';_FC={}
SPEC_F={'sans':('NotoSansJP-VF.ttf',560),'sub':('NotoSansJP-VF.ttf',640),'serif':('NotoSerifJP-VF.ttf',800)}
def vfont(kind,size):
    k=(kind,size)
    if k not in _FC:
        f=ImageFont.truetype(FD+SPEC_F[kind][0],size);f.set_variation_by_axes([SPEC_F[kind][1]]);_FC[k]=f
    return _FC[k]
class _Fam:
    def __init__(s,kind):s.kind=kind
    def __getitem__(s,n):return vfont(s.kind,n)
F=_Fam('sans');FB=_Fam('serif');FSUB=_Fam('sub')   # body / headlines / subtitles
SS=2  # supersampling factor for the moving overlay (pins, arrows, labels) -> sub-pixel smooth
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
timeline=load('data/hn_timeline.json');ana=load('data/hn_analysis.json');audio=load('out/hn_audio_report.json');segs=audio['segments'];VIS=load('data/hn_scene_visuals.json')
N=round(timeline[-1]['end']*30);FR_DIR=ROOT/'cache'/'hn_v3';FR_DIR4=ROOT/'cache'/'hn_v4';ROUTE_KEYS={'d_depart','d_oi','d_katsura','d_time'}  # route-dependent scenes were re-rendered on the road-following route (numbering of data/hn_timeline_v4.json)
OLDI4={c['key']:c for c in load('data/hn_timeline_v4.json')};HAVE4=set(int(Path(x).stem) for x in glob.glob(str(FR_DIR4/'*.jpg')))
KEYS=[c['key'] for c in timeline]
OLD=load('data/hn_timeline_rendered.json');OLDI={c['key']:c for c in OLD}
HAVE=set(int(Path(x).stem) for x in glob.glob(str(FR_DIR/'*.jpg')))
def old_frame(key,local,OLDI=OLDI,HAVE=HAVE):
    """3D frames were rendered for an earlier narration timing; camera/army motion depends only on scene-local progress, so remap by local progress."""
    o=OLDI[key];a=round(o['start']*30);b=round(o['end']*30)-1;f=a+local*(b-a)
    lo=int(f)
    while lo not in HAVE and lo>a:lo-=1
    while lo not in HAVE and lo<b:lo+=1
    hi=lo+1
    while hi not in HAVE and hi<b:hi+=1
    if hi not in HAVE:hi=lo
    w=0.0 if hi==lo else min(1.0,max(0.0,(f-lo)/(hi-lo)))
    return lo,hi,w
def lerp_labels(m0,m1,w):
    """interpolate projected label positions / army progress between two rendered frames (same ids, same scene)"""
    if m0 is None:return m1
    if m1 is None or w==0:return m0
    out=dict(m0);out['army_progress']=m0['army_progress']+(m1['army_progress']-m0['army_progress'])*w;L1={l['id']:l for l in m1['labels']};labs=[]
    for l in m0['labels']:
        q=L1.get(l['id'],l);labs.append({**l,'x':l['x']+(q['x']-l['x'])*w,'y':l['y']+(q['y']-l['y'])*w,'depth':l['depth']})
    out['labels']=labs;return out
SC=VIS['scenes'];PL=VIS['places']
BG=(7,24,36,240);GOLD=(239,201,118);WHITE=(245,243,232);DIM=(190,205,208);EDGE=(176,153,100)
COL={'kameyama':(150,110,255),'oinosaka':(255,160,40),'honnoji':(255,95,80),'honnoji_now':(150,185,255),'nijo':(255,95,80),'army':(150,110,255),
     'akechi':(170,135,255),'nobunaga':(255,105,90),'gold':(239,201,118),'hideyoshi':(255,160,40),'ieyasu':(239,201,118),'dim':(150,165,170)}
NAME={'kameyama':'亀山城','oinosaka':'老ノ坂(経路の最高点)','honnoji':'本能寺(当時・推定)','honnoji_now':'本能寺(現在)','nijo':'二条新御所(仮置き)','army':'明智軍'}
SUB={'nobunaga':'像：長興寺蔵','mitsuhide':'像：本徳寺蔵','nobutada':'像：総見寺蔵','hideyoshi':'像：高台寺蔵','ieyasu':'像：大阪城天守閣'}
NAMEP={'nobunaga':'織田信長','mitsuhide':'明智光秀','nobutada':'織田信忠','hideyoshi':'羽柴秀吉','ieyasu':'徳川家康'}
CROP={'nobunaga':(.12,.07,.76),'mitsuhide':(.27,.45,.65),'nobutada':(.08,.0,.78),'hideyoshi':(.17,.36,.66),'ieyasu':(.13,.23,.6)}
FRAME={'nobunaga':(255,95,80),'mitsuhide':(150,110,255),'nobutada':(255,95,80),'hideyoshi':(255,160,40),'ieyasu':(239,201,118)}
_IMG={}
def portrait(pid,w,prog):
    key=(pid,w,round(prog*300))
    if key in _IMG:return _IMG[key]
    if ('src',pid) not in _IMG:_IMG[('src',pid)]=Image.open(ROOT/'assets'/'portraits'/f'{pid}.jpg').convert('RGB')
    im=_IMG[('src',pid)]
    if pid=='print':out=im.resize((w,int(w*im.height/im.width)),Image.LANCZOS)
    else:
        x0,top,wf=CROP[pid];h=int(w*1.25);cw=im.width*wf*(1-.07*prog);ch=cw*1.25;cx=im.width*x0+im.width*wf/2;cy=im.height*top+im.width*wf*1.25/2
        out=im.resize((w,h),Image.LANCZOS,box=(cx-cw/2,cy-ch/2,cx+cw/2,cy+ch/2))   # float box: sub-pixel zoom, no stepping
    _IMG[key]=out;return out
def draw_cards(im,ci,t,local,shown,used,key):
    for pid,(x,y,w),after in SC[key].get('cards',[]):
        if shown<after:continue
        fade=min(1,max(0,(t-timeline[ci]['start']-.15)/.8))
        if key=='hook':fade=min(1,max(0,(t-HOOK_END-.2)/.8))
        if fade<=0:continue
        p=portrait(pid,w,local);h=p.height;col=(200,170,100) if pid=='print' else FRAME[pid]
        bar=0 if pid=='print' else (52 if w>=190 else 42);cap=0;tot=h+bar+cap
        layer=Image.new('RGBA',(w+12,tot+12),(0,0,0,0));ld=ImageDraw.Draw(layer)
        ld.rounded_rectangle((0,0,w+11,tot+11),10,fill=(7,24,36,240),outline=col+(255,),width=3);layer.paste(p,(6,6))
        if pid!='print':ld.text((12,h+7),NAMEP[pid],font=FB[34] if w>=190 and w<300 else (FB[40] if w>=300 else FB[28]),fill=WHITE)
        if fade<1:
            r,g,b,a=layer.split();layer=Image.merge('RGBA',(r,g,b,a.point(lambda v:int(v*fade))))
        im.alpha_composite(layer,(x-6,y-6));used.append((x-6,y-6,x+w+6,y+tot+6))
_IMGC={}
def gen_image(name,prog,alpha):
    """AI-generated scene image (Meiji-nishiki-e style) as a full-frame slow zoom; sub-pixel crop via resize(box=)"""
    if name not in _IMGC:_IMGC[name]=Image.open(ROOT/'assets'/'imagen'/f'{name}.webp').convert('RGB')
    im=_IMGC[name];W,H=im.size;z=1.0+.08*prog;cw,ch=W/z,H/z;cx=min(max(W/2+(prog-.5)*W*.03,cw/2),W-cw/2);cy=H/2
    out=im.resize((1920,1080),Image.LANCZOS,box=(cx-cw/2,cy-ch/2,cx+cw/2,cy+ch/2)).convert('RGBA')
    if alpha<1:out.putalpha(int(255*alpha))
    return out
def overlap(a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
def tw(d,t,f):return d.textlength(t,font=f)
def label(d,text,x,y,used,color,font=F[34],draw=True,ymin=165,ymax=840):
    w=math.ceil(font.getlength(text))+30;hgt=52
    for dx,dy in [(0,-66),(0,16),(-w/2-30,-22),(w/2+30,-22),(0,-126),(0,76),(0,-190),(-w/2-30,40),(w/2+30,40)]:
        xx=max(30,min(1890-w,x-w/2+dx));yy=y+dy;box=(int(xx),int(yy),int(xx+w),int(yy+hgt))
        if yy<ymin or yy+hgt>ymax or any(overlap(box,b) for b in used):continue
        if draw:
            d.line([(x,y),(xx+w/2,yy+hgt/2)],fill=color,width=2);d.rounded_rectangle(box,8,fill=BG,outline=color,width=2);d.text((xx+15,yy+4),text,font=font,fill=WHITE)
        used.append(box);return box
    return None
_STABLE={}
COLOR_DUMMY=(255,255,255)
def stable_slot(slot,text,x,y,used,font=F[34]):
    """label box offset is decided ONCE per (scene, item) and then moves rigidly with its anchor -> no flipping/jitter"""
    if slot not in _STABLE:
        box=label(None,text,x,y,[b for b in used],COLOR_DUMMY,font=font,draw=False);_STABLE[slot]=None if box is None else (box[0]-x,box[1]-y,box[2]-box[0],box[3]-box[1])
    o=_STABLE[slot]
    if o is None:return None
    b=(x+o[0],y+o[1],x+o[0]+o[2],y+o[1]+o[3]);used.append((int(b[0]),int(b[1]),int(b[2]),int(b[3])));return b
def ss_label(od,anchor,box,text,color,alpha=255,size=34,line=True):
    k=SS;ax,ay=anchor;cx,cy=(box[0]+box[2])/2,(box[1]+box[3])/2
    if line:od.line([(ax*k,ay*k),(cx*k,cy*k)],fill=color+(alpha,),width=2*k)
    od.rounded_rectangle([box[0]*k,box[1]*k,box[2]*k,box[3]*k],8*k,fill=BG[:3]+(int(240*alpha/255),),outline=color+(alpha,),width=2*k)
    od.text(((box[0]+15)*k,(box[1]+2)*k),text,font=vfont('sans',size*k),fill=WHITE+(alpha,))
def wrap(d,text,font,maxw):
    """greedy wrap; a 2-line result is rebalanced (prefers breaking after 、) so no orphan characters are left."""
    if tw(d,text,font)<=maxw:return [text]
    best=None
    for k in range(1,len(text)):
        l1,l2=text[:k],text[k:]
        w1,w2=tw(d,l1,font),tw(d,l2,font)
        if w1>maxw or w2>maxw or text[k-1] in '（「『' or text[k] in '）」』、':continue
        score=max(w1,w2)+(0 if text[k-1] in '、，。' else (70 if text[k-1] in 'はがをにのでとも' and not ('\u4e00'<=text[k]<='\u9fff' and '\u4e00'<=text[k-1]<='\u9fff') else 160))
        if best is None or score<best[0]:best=(score,[l1,l2])
    if best:return best[1]
    lines=[];cur=''
    for ch in text:
        if tw(d,cur+ch,font)>maxw and cur:lines.append(cur);cur=ch
        else:cur+=ch
    lines.append(cur);return lines
def panel(d,box,title,used):
    used.append(box);d.rounded_rectangle(box,12,fill=BG,outline=EDGE,width=2);d.text((box[0]+22,box[1]+12),title,font=FB[36],fill=GOLD)
def chips_panel(d,spec,seg_t,used,t):
    """auto-height panel; every chip wraps at 30px; chip appears when its sentence starts."""
    x0,y0,w=45,175,930;rows=[];yy=y0+66
    for text,at in spec['lines']:
        ls=wrap(d,text,F[40],w-90);rows.append((ls,at,yy));yy+=len(ls)*58+22
    box=(x0,y0,x0+w,yy+6);panel(d,box,spec['title'],used)
    for ls,at,y in rows:
        if at<len(seg_t) and t>=seg_t[at]:
            a=min(1,(t-seg_t[at])/.5)
            d.ellipse((x0+24,y+18,x0+38,y+32),fill=GOLD+(int(255*a),))
            for j,l in enumerate(ls):d.text((x0+56,y+j*58),l,font=F[40],fill=WHITE+(int(255*a),))
_TOP=None
_TBG={}
def trivia_bg(bgkey):
    """static, blurred and darkened still from the related 3D scene (no motion -> nothing to jitter)"""
    if bgkey in _TBG:return _TBG[bgkey]
    from PIL import ImageFilter,ImageEnhance
    o=OLDI[bgkey];a=round(o['start']*30);b=round(o['end']*30)-1;f=(a+b)//2
    for k in range(0,(b-a)//2+1):
        if f+k in HAVE:f=f+k;break
        if f-k in HAVE:f=f-k;break
    im=Image.open(FR_DIR/f'{f:05}.jpg').convert('RGB').filter(ImageFilter.GaussianBlur(7));im=ImageEnhance.Brightness(im).enhance(.42);_TBG[bgkey]=im.convert('RGBA');return _TBG[bgkey]
def trivia_panel(d,spec,seg_t,used,t):
    d.rounded_rectangle((60,172,250,236),14,fill=GOLD+(255,));d.text((84,176),'豆知識',font=FB[44],fill=(30,22,10))
    d.text((60,250),spec['headline'],font=FB[72],fill=WHITE,stroke_width=5,stroke_fill=(5,10,16))
    y=392;box_top=y-18;rows=[]
    for text,at in spec['lines']:
        ls=wrap(d,text,F[40],1180);rows.append((ls,at,y));y+=len(ls)*54+22
    box=(60,box_top,1290,y+4);used.append(box);d.rounded_rectangle(box,16,fill=BG,outline=EDGE,width=2)
    for ls,at,yy in rows:
        if at<len(seg_t) and t>=seg_t[at]:
            a=min(1,(t-seg_t[at])/.5);d.ellipse((92,yy+17,108,yy+33),fill=GOLD+(int(255*a),))
            for j,l in enumerate(ls):d.text((124,yy+j*54),l,font=F[40],fill=WHITE+(int(255*a),))
_NUM={};_n=0
for _c in timeline:
    if _c['key']=='hook' or _c['key'].startswith('tr_'):continue
    _n+=1;_NUM[_c['key']]=_n
def disp_title(sc):
    import re as _re
    m=_re.match(r'^\d+ / (.*)$',sc['title'])
    return m.group(1) if m else sc['title']
def theory_panel(d,spec,seg_t,used,t):
    tag=spec['tag'];w=int(tw(d,tag,FB[44]))+48
    d.rounded_rectangle((60,150,60+w,214),14,fill=GOLD+(255,));d.text((84,154),tag,font=FB[44],fill=(30,22,10))
    d.text((60,222),spec['name'],font=FB[66] if len(spec['name'])<18 else FB[52],fill=WHITE,stroke_width=5,stroke_fill=(5,10,16))
    rows_in=spec['rows'];slot=spec.get('slot',122);table=len(rows_in)>=5
    def on(at):return at<len(seg_t) and t>=seg_t[at]
    def fa(at):return min(1,(t-seg_t[at])/.5)
    if spec.get('timeline'):
        n=len(rows_in);cw=560;gap=60;x0=60
        for i,(label,text,at) in enumerate(rows_in):
            x=x0+i*(cw+gap);d.rounded_rectangle((x,330,x+cw,560),16,fill=BG,outline=EDGE,width=2)
            d.text((x+24,346),label,font=FB[44],fill=GOLD if on(at) else (215,222,224))
            if i<n-1:d.polygon([(x+cw+10,435-26),(x+cw+10,435+26),(x+cw+gap-10,435)],fill=GOLD)
            if on(at):
                for j,l in enumerate(wrap(d,text,F[38],cw-48)):d.text((x+24,420+j*54),l,font=F[38],fill=WHITE+(int(255*fa(at)),))
        if on(spec['foot_at']):
            d.rounded_rectangle((60,600,1860,680),14,fill=BG,outline=GOLD+(int(255*fa(spec['foot_at'])),),width=2);d.text((90,614),spec['foot'],font=F[38],fill=WHITE+(int(255*fa(spec['foot_at'])),))
        used.append((60,330,1860,680));return
    nl=spec.get('note_lines') or []
    if table:
        top=332;y0=top+52
    else:
        top=424 if nl else 340;y0=top+18
        if nl and on(spec.get('note_at',0)):
            a_=fa(spec['note_at']);bh=len(nl)*42+18;d.rounded_rectangle((60,314,1860,314+bh),12,fill=(7,24,36,int(240*a_)),outline=EDGE+(int(255*a_),),width=2)
            for j,l in enumerate(nl):d.text((84,322+j*42),l,font=F[32],fill=(225,230,232)+(int(255*a_),))
    TW=1330 if table else 1230
    LF=F[40];LH=52
    for FS in (40,34):
        LF=F[FS];LH=FS+12;ok=True
        for label,text,at in rows_in:
            if len(wrap(d,text,LF,TW))*LH>slot-8:ok=False
        if ok:break
    bottom=y0+len(rows_in)*slot+14
    box=(60,top,1860,bottom);used.append(box);d.rounded_rectangle(box,16,fill=BG,outline=EDGE,width=2)
    if table:
        d.text((92,top+8),'説の名前',font=F[30],fill=(200,210,214));d.text((430,top+8),'残る疑問',font=F[30],fill=(200,210,214))
    act=-1
    for i,(label,text,at) in enumerate(rows_in):
        if on(at):act=i
    for i,(label,text,at) in enumerate(rows_in):
        yy=y0+i*slot
        d.text((92,yy+3),label,font=F[36] if not table else F[34],fill=(GOLD if i==act else (170,184,190)))
        if on(at):
            a=fa(at);ls=wrap(d,text,LF,TW)
            if i==act and not table:d.rounded_rectangle((72,yy-6,1848,yy+slot-14),12,outline=GOLD+(int(255*a),),width=3)
            for j,l in enumerate(ls):d.text((430,yy+j*LH),l,font=LF,fill=WHITE+(int(255*a),))
def static_layer(ci,sc,note=True):
    global _TOP
    key=sc['key'];im=Image.new('RGBA',(1920,1080),(0,0,0,0));d=ImageDraw.Draw(im)
    if _TOP is None:  # soft fade (not a band) so outlined titles stay legible over bright terrain
        g=Image.new('L',(1,230));gd=g.load()
        for y in range(230):gd[0,y]=int(150*max(0,1-y/230)**1.6)
        _TOP=Image.new('RGBA',(1920,230),(5,12,20,255));_TOP.putalpha(g.resize((1920,230)))
    im.alpha_composite(_TOP,(0,0));d=ImageDraw.Draw(im)
    ST=dict(stroke_width=5,stroke_fill=(5,10,16))
    TT=disp_title(sc)
    if SC[key].get('theory'):TT={'諸説':'動機を比べる','史料':'史料を読む'}.get(SC[key]['theory']['tag'].split(' ')[0],TT)
    d.text((48,16),TT,font=(FB[40] if SC[key].get('theory') else FB[60] if len(TT)<16 else FB[52]),fill=WHITE,**ST);d.text((48,94 if not SC[key].get('theory') else 70),sc['category'],font=F[28],fill=(200,210,214),stroke_width=4,stroke_fill=(5,10,16))
    date=SC[key].get('date','')
    if date:
        f=FB[56];w=d.textlength(date,font=f);d.text((1872-w,14),date,font=f,fill=GOLD,**ST)
    b='' if (not note or SC[key].get('trivia') or SC[key].get('theory')) else '高さ2倍強調｜現代の地形・写真｜軍勢は模式表現' if SC[key].get('map') is None else '位置は町名レベルの概略｜現代の地図データ';w=d.textlength(b,font=F[26]);d.text((1872-w,98),b,font=F[26],fill=(205,214,218),stroke_width=4,stroke_fill=(5,10,16))
    return im
def profile_chart(d,box,p):
    prof=ana['profile'];D=ana['horizontal_distance_m'];e=prof['elevation_m'];dist=prof['distance_m'];mi,ma=0,300
    x0,y0,x1,y1=box[0]+30,box[1]+124,box[2]-30,box[3]-98
    pts=[(x0+v/D*(x1-x0),y1-(z-mi)/(ma-mi)*(y1-y0)) for v,z in zip(dist,e)]
    d.polygon(pts+[(x1,y1),(x0,y1)],fill=(60,90,100,200));d.line(pts,fill=GOLD,width=4)
    for k,lab in [('oinosaka_zone','老ノ坂'),('katsura','桂'),('honnoji','本能寺')]:
        v=ana['waypoint_dist_m'][k];xx=x0+v/D*(x1-x0);d.line([(xx,y0),(xx,y1)],fill=(120,150,160),width=1);d.text((xx-28 if k!='honnoji' else xx-84,y1+4),lab,font=F[30],fill=DIM)
    d.text((x0-4,y1+4),'亀山城',font=F[30],fill=DIM)
    cx=x0+p*(x1-x0);i=min(range(len(dist)),key=lambda j:abs(dist[j]/D-p));cy=pts[i][1]
    d.line([(cx,y0),(cx,y1)],fill=(150,110,255),width=3);d.ellipse((cx-9,cy-9,cx+9,cy+9),fill=(150,110,255),outline='white')
    d.text((box[0]+22,box[1]+56),f'{p*D/1000:4.1f} / {D/1000:.1f} km　標高 {np.interp(p*D,dist,e):3.0f} m',font=F[42],fill=WHITE)
# ---------------- 2D location map
_MAP={}
def mapbase(name):
    if name not in _MAP:
        meta=json.loads((ROOT/'cache'/f'hn_map_{name}.json').read_text());_MAP[name]=(Image.open(ROOT/'cache'/f'hn_map_{name}.png').convert('RGB'),meta)
    return _MAP[name]
def merc(lon,lat,meta):
    z=meta['z'];x=(lon+180)/360*2**z;y=(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**z
    return (x-meta['x0'])*256,(y-meta['y0'])*256
def ease(x):x=min(1,max(0,x));return x*x*(3-2*x)
_FIT={}
def map_frame(key,t,local,seg_t,used):
    """returns (RGB image 1920x1080, draw-callback for pins/arrows)"""
    spec=SC[key]['map'];img,meta=mapbase(spec['base']);rx0,ry0,rx1,ry1=spec['region']
    names=[p for it in spec['items'] for p in ((it['p'],) if it['t']=='pin' else (it['pts'] if it['t']=='path' else (it['a'],it['b'])))]+spec.get('context',[])
    pts=[merc(PL[n]['lon'],PL[n]['lat'],meta) for n in names]
    if key not in _FIT:
        xs=[p[0] for p in pts];ys=[p[1] for p in pts];bw=max(xs)-min(xs);bh=max(ys)-min(ys);mx,my=(min(xs)+max(xs))/2,(min(ys)+max(ys))/2
        s=min((rx1-rx0)*.74/max(bw,1),(ry1-ry0)*.68/max(bh,1),{'kinki':1.15,'chukyo':1.1,'okayama':1.1,'east':1.2}.get(spec['base'],1.0));s=max(s,1920/img.width,1080/img.height);_FIT[key]=(s,mx,my)
    s,mx,my=_FIT[key];cx,cy=(rx0+rx1)/2,(ry0+ry1)/2+10
    left=mx-cx/s;top=my-cy/s;left=min(max(left,0),max(0,img.width-1920/s));top=min(max(top,0),max(0,img.height-1080/s))
    base=img.transform((1920,1080),Image.AFFINE,(1/s,0,left,0,1/s,top),resample=Image.BICUBIC,fillcolor=(5,10,18))
    scr=lambda n:((merc(PL[n]['lon'],PL[n]['lat'],meta)[0]-left)*s,(merc(PL[n]['lon'],PL[n]['lat'],meta)[1]-top)*s)
    return base,scr,spec
def draw_map_items(od,scr,spec,t,seg_t,used,key):
    k=SS;boxes=[]
    for idx,it in enumerate(spec['items']):
        if it['t']=='pin':
            x,y=scr(it['p']);box=stable_slot((key,idx),it.get('label') or PL[it['p']]['name'],x,y,used);boxes.append((it,box,(x,y)))
        elif it['t']=='path':
            mx_=sum(scr(n)[0] for n in it['pts'])/len(it['pts']);my_=sum(scr(n)[1] for n in it['pts'])/len(it['pts']);boxes.append((it,stable_slot((key,idx,'path'),it.get('label',''),mx_,my_,used,font=F[30]) if it.get('label') else None,(mx_,my_)))
        else:boxes.append((it,None,None))
    for n in spec.get('context',[]):
        x,y=scr(n);od.ellipse([(x-8)*k,(y-8)*k,(x+8)*k,(y+8)*k],fill=(120,135,140,230),outline=(235,235,235,255),width=2*k);bx=stable_slot((key,'ctx',n),PL[n]['name'],x,y,used,font=F[30])
        if bx:ss_label(od,(x,y),bx,PL[n]['name'],COL['dim'],size=30)
    for idx,(it,box,pos) in enumerate(boxes):
        at=it['at'];rt=seg_t[at] if at<len(seg_t) else 1e9
        if t<rt:continue
        a=min(1,(t-rt)/.6);c=COL[it.get('c','gold')];al=int(255*a)
        if it['t']=='pin':
            x,y=pos;od.ellipse([(x-14)*k,(y-14)*k,(x+14)*k,(y+14)*k],fill=c+(al,),outline=(255,255,255,al),width=3*k)
            if box:ss_label(od,(x,y),box,it.get('label') or PL[it['p']]['name'],c,al)
        elif it['t']=='path':
            pts=[scr(n) for n in it['pts']];segl=[math.hypot(b[0]-a_[0],b[1]-a_[1]) for a_,b in zip(pts[:-1],pts[1:])];tot=sum(segl);prog=ease((t-rt)/it.get('dur',3.0))*tot;done=0.0;c=COL[it.get('c','gold')];last=pts[0];ang=0
            for (a_,b),sl in zip(zip(pts[:-1],pts[1:]),segl):
                use=min(sl,max(0.0,prog-done));done+=sl
                if use<=0:break
                e_=(a_[0]+(b[0]-a_[0])*use/sl,a_[1]+(b[1]-a_[1])*use/sl);ang=math.atan2(b[1]-a_[1],b[0]-a_[0])
                if it.get('dash'):
                    n=max(1,int(use/22))
                    for j in range(0,n,2):
                        q0=(a_[0]+(e_[0]-a_[0])*j/n,a_[1]+(e_[1]-a_[1])*j/n);q1=(a_[0]+(e_[0]-a_[0])*(j+1)/n,a_[1]+(e_[1]-a_[1])*(j+1)/n);od.line([(q0[0]*k,q0[1]*k),(q1[0]*k,q1[1]*k)],fill=c+(235,),width=6*k)
                else:od.line([(a_[0]*k,a_[1]*k),(e_[0]*k,e_[1]*k)],fill=c+(235,),width=7*k)
                last=e_
            for q in pts:
                if math.hypot(q[0]-last[0],q[1]-last[1])<1 or prog>=tot-1 or True:pass
            for n_,q in zip(it['pts'],pts):
                if (sum(segl[:it['pts'].index(n_)])<=prog+1):od.ellipse([(q[0]-9)*k,(q[1]-9)*k,(q[0]+9)*k,(q[1]+9)*k],fill=c+(255,),outline=(255,255,255,255),width=2*k)
            if prog>=tot-1:
                hx,hy=last;od.polygon([(hx*k,hy*k),((hx-26*math.cos(ang-.45))*k,(hy-26*math.sin(ang-.45))*k),((hx-26*math.cos(ang+.45))*k,(hy-26*math.sin(ang+.45))*k)],fill=c+(255,))
                if box:ss_label(od,pos,box,it['label'],c,255,size=30,line=False)
        else:
            (x0,y0),(x1,y1)=scr(it['a']),scr(it['b']);p=ease((t-rt)/1.3);xe,ye=x0+(x1-x0)*p,y0+(y1-y0)*p;ang=math.atan2(y1-y0,x1-x0)
            if it.get('dash'):
                L=math.hypot(xe-x0,ye-y0);n=int(L/26)
                for j in range(0,n,2):
                    ax,ay=x0+(xe-x0)*j/max(n,1),y0+(ye-y0)*j/max(n,1);bx_,by_=x0+(xe-x0)*(j+1)/max(n,1),y0+(ye-y0)*(j+1)/max(n,1);od.line([(ax*k,ay*k),(bx_*k,by_*k)],fill=c+(235,),width=6*k)
            else:od.line([(x0*k,y0*k),(xe*k,ye*k)],fill=c+(235,),width=7*k)
            if p>=.98:
                hx,hy=xe,ye;od.polygon([(hx*k,hy*k),((hx-30*math.cos(ang-.45))*k,(hy-30*math.sin(ang-.45))*k),((hx-30*math.cos(ang+.45))*k,(hy-30*math.sin(ang+.45))*k)],fill=c+(255,))
                if it.get('label'):
                    mx_,my_=(x0+x1)/2,(y0+y1)/2;bx=stable_slot((key,idx,'arrow'),it['label'],mx_,my_,used,font=F[30])
                    if bx:ss_label(od,(mx_,my_),bx,it['label'],c,255,size=30,line=False)
# ---------------- hook (scene 0)
S0=[x for x in segs if x['scene']==0];HOOK_END=S0[2]['end']
PRINT=Image.open(ROOT/'assets'/'portraits'/'print.jpg').convert('RGB');PRINT=PRINT.resize((int(1080*PRINT.width/PRINT.height),1080),Image.LANCZOS)
_GRAD=None
def hook_layer(t):
    global _GRAD
    z=1.0+.10*min(1,t/HOOK_END);w=PRINT.width/z;h=PRINT.height/z;cx=PRINT.width*(.62-.12*min(1,t/HOOK_END));x0=max(0,min(PRINT.width-w,cx-w/2));y0=(PRINT.height-h)/2
    base=PRINT.crop((int(x0),int(y0),int(x0+w),int(y0+h))).resize((1920,1080),Image.LANCZOS).convert('RGBA')
    if _GRAD is None:
        g=Image.new('L',(1,1080));gd=g.load()
        for y in range(1080):gd[0,y]=int(120+110*(y/1080)**2)
        _GRAD=Image.new('RGBA',(1920,1080),(6,12,20,255));_GRAD.putalpha(g.resize((1920,1080)))
    base.alpha_composite(_GRAD);d=ImageDraw.Draw(base,'RGBA')
    d.text((60,44),'天正10年6月2日 未明',font=FB[72],fill=GOLD)
    if t>=S0[0]['start']+.4:d.text((60,150),'本能寺の変',font=FB[110],fill=WHITE)
    if t>=S0[1]['start']:
        d.rounded_rectangle((60,430,900,700),14,fill=(7,24,36,225),outline=(255,95,80),width=3)
        d.text((92,448),'信長の側近',font=FB[44],fill=WHITE);d.text((92,520),'20〜30人',font=FB[96],fill=(255,130,110));d.text((92,636),'〜 150〜160人（諸説）',font=F[40],fill=DIM)
    if t>=S0[2]['start']-.2:
        d.rounded_rectangle((960,430,1860,700),14,fill=(7,24,36,225),outline=(150,110,255),width=3)
        d.text((992,448),'光秀の軍勢',font=FB[44],fill=WHITE);d.text((992,520),'約1万3千',font=FB[96],fill=(185,160,255));d.text((992,636),'（一説・史料により異なる）',font=F[40],fill=DIM)
    return base
_SUBP={}
def sub_lines(d,seg,f,t):
    """2-line subtitle pages at a fixed 46px: a long sentence is split into timed pages (by character count) instead of shrinking the font."""
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
def render(a,b):
    reports=[json.loads(Path(p).read_text()) for p in sorted(glob.glob(str(FR_DIR/'report_*.json')),key=os.path.getmtime)];fr={m['frame']:m for r in reports for m in r['frames']}
    fr4={m['frame']:m for r in [json.loads(Path(p).read_text()) for p in glob.glob(str(FR_DIR4/'report_*.json')) if 'meta' not in p] for m in r['frames']}
    statics={ci:static_layer(ci,sc) for ci,sc in enumerate(timeline)};statics_img={ci:static_layer(ci,sc,False) for ci,sc in enumerate(timeline)};scene_segs={ci:[x for x in segs if x['scene']==ci] for ci in range(len(timeline))}
    stills=[int(x) for x in os.environ['STILLS'].split(',')] if os.environ.get('STILLS') else None
    out=ROOT/'cache'/f'hn4_part_{a}_{b}.mp4';log=(ROOT/'logs'/f'hn4_enc_{a}.log').open('wb')
    class _P:
        class stdin:
            write=staticmethod(lambda b:None);close=staticmethod(lambda:None)
        def wait(self):pass
        returncode=0
    proc=_P() if stills else subprocess.Popen(['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','pipe:0','-an','-c:v','h264_nvenc','-preset','p4','-cq','19','-b:v','0','-pix_fmt','yuv420p',str(out)],stdin=subprocess.PIPE,stderr=log)
    omitted=0;layout=[]
    try:
        for i in (stills or range(a,min(b,N))):
            t=i/30;ci=next(k for k,c in enumerate(timeline) if t<c['end']+1e-9);key=KEYS[ci];ch=timeline[ci];local=min(1,max(0,(t-ch['start'])/ch['duration']))
            seg_list=scene_segs[ci];seg_t=[x['start'] for x in seg_list];shown=sum(1 for x in seg_list if t>=x['start']);of=None;m=None
            if key in ROUTE_KEYS:of=old_frame(key,local,OLDI4,HAVE4);m=lerp_labels(fr4.get(of[0]),fr4.get(of[1]),of[2])
            elif not (SC[key].get('map') or SC[key].get('trivia') or SC[key].get('theory')):of=old_frame(key,local);m=lerp_labels(fr.get(of[0]),fr.get(of[1]),of[2])
            hook=0.0
            if key=='hook':hook=1.0 if t<HOOK_END else max(0.0,1-(t-HOOK_END)/1.0)
            used=[(0,0,1920,150),(40,850,1880,1010)]
            mapspec=SC[key].get('map');triv=SC[key].get('trivia');theo=SC[key].get('theory')
            if mapspec:
                base,scr,spec=map_frame(key,t,local,seg_t,used);im=base.convert('RGBA');im.alpha_composite(statics[ci]);d=ImageDraw.Draw(im,'RGBA')
                chips_panel(d,SC[key]['panel'],seg_t,used,t)
                for pid,(x,y,w),after in SC[key].get('cards',[]):used.append((x-6,y-6,x+w+6,y+330))
                d.text((936,812),'1582年当時の地形・海岸線とは異なる',font=F[26],fill=(235,240,242),stroke_width=3,stroke_fill=(5,10,16))
            elif theo:
                im=trivia_bg(theo['bg']).copy();im.alpha_composite(statics[ci]);d=ImageDraw.Draw(im,'RGBA');theory_panel(d,theo,seg_t,used,t)
            elif triv:
                im=trivia_bg(triv['bg']).copy();im.alpha_composite(statics[ci]);d=ImageDraw.Draw(im,'RGBA');trivia_panel(d,triv,seg_t,used,t)
                for pid,(x,y,w),after in SC[key].get('cards',[]):used.append((x-6,y-6,x+w+6,y+330))
            else:
                if hook<1 and key in ROUTE_KEYS:
                    im=Image.open(FR_DIR4/f'{of[0]:05}.jpg').convert('RGBA')
                    if of[2]>0 and of[1]!=of[0]:im=Image.blend(im,Image.open(FR_DIR4/f'{of[1]:05}.jpg').convert('RGBA'),of[2])
                elif hook<1:
                    im=Image.open(FR_DIR/f'{of[0]:05}.jpg').convert('RGBA')
                    if of[2]>0 and of[1]!=of[0]:im=Image.blend(im,Image.open(FR_DIR/f'{of[1]:05}.jpg').convert('RGBA'),of[2])
                else:im=Image.new('RGBA',(1920,1080),(0,0,0,255))
                st=statics[ci]
                if hook>0:
                    hl=hook_layer(t)
                    if hook<1:
                        st=st.copy();r,g,b_,al=st.split();st.putalpha(al.point(lambda v:int(v*(1-hook))));r,g,b_,al=hl.split();hl.putalpha(al.point(lambda v:int(v*hook)));im.alpha_composite(st);im.alpha_composite(hl)
                    else:im=hl
                else:im.alpha_composite(st)
                d=ImageDraw.Draw(im,'RGBA');P=(45,170,905,590)
                if key in ('d_oi','d_katsura','d_time'):
                    panel(d,P,'経路の標高プロファイル（道路に沿った経路）',used);profile_chart(d,P,m['army_progress']);d.text((P[0]+22,P[3]-40),'現代の道路に沿った経路。当時の街道とは限らない',font=F[28],fill=DIM)
                if key=='d_depart':
                    P=(45,170,905,520);panel(d,P,'出発地点',used);d.text((70,232),'亀山城（現・亀岡市）',font=F[40],fill=WHITE);d.text((70,296),f'標高 約{ana["start_elev_m"]:.0f} m（現代DEM）',font=F[40],fill=WHITE);d.text((70,372),'約1万3千は一説。史料により異なる',font=F[32],fill=DIM);d.text((70,424),'（兵数は画面では実数を表さない）',font=F[28],fill=DIM)
                if key=='d_oi':
                    bx=(45,602,905,830);d.rounded_rectangle(bx,12,fill=BG,outline=EDGE,width=2);used.append(bx)
                    d.text((68,610),'峠の標高（出典）　約230 m',font=F[40],fill=WHITE);d.text((68,668),f'経路の最高点（DEM）　{ana["max_elev_m"]:.0f} m',font=F[40],fill=WHITE);d.text((68,726),f'登り {ana["ascent_m"]:.0f} m / 下り {ana["descent_m"]:.0f} m',font=F[40],fill=WHITE);d.text((68,786),'（高低差は現代のDEMによる）',font=F[28],fill=DIM)
                if key=='d_temple':
                    panel(d,(45,170,930,480),'二つの「本能寺」',used);d.ellipse((70,246,94,270),fill=COL['honnoji']);d.text((108,232),'当時：蛸薬師通の北・約120m四方',font=F[36],fill=WHITE)
                    d.ellipse((70,312,94,336),fill=COL['honnoji_now']);d.text((108,298),'現在：寺町御池（1591–92年に移転）',font=F[36],fill=WHITE);d.text((70,382),f'二地点の距離　約{ana["honnoji_old_to_now_m"]/1000:.2f} km',font=FB[44],fill=GOLD)
                if key=='d_attack':
                    panel(d,(45,170,960,450),'6/2 午前4時ごろ（諸説）',used);d.text((70,232),'包囲の配置・炎は説明用の演出',font=F[38],fill=WHITE);d.text((70,298),'側近：20〜30人とも150〜160人とも',font=F[38],fill=WHITE);d.text((70,364),'（諸説あり確定していない）',font=F[30],fill=DIM)
                if key=='d_nijo':
                    panel(d,(45,170,900,440),'本能寺跡 ↔ 二条新御所',used);d.text((70,232),f'距離　約{ana["honnoji_to_nijo_m"]/1000:.1f} km',font=FB[48],fill=GOLD);d.text((70,308),'二条側の位置は仮置き',font=F[38],fill=WHITE);d.text((70,370),'（誤差 数百m）',font=F[32],fill=DIM)
                if key=='d_time':
                    P2=(45,602,905,852);panel(d,P2,'速さによる所要時間の違い（速度は仮定）',used)
                    if shown>=4:
                        for k,v in enumerate(ana['sensitivity']):
                            y=660+k*50;d.text((70,y+4),f'時速{v["assumed_speed_km_h"]}km',font=F[32],fill=WHITE);L=v['minutes']/450*240;d.rectangle((270,y+8,270+L,y+38),fill=(187,165,110));d.text((278+L,y-2),f'約{int(round(v["minutes"]/10)*10)//60}時間{int(round(v["minutes"]/10)*10)%60:02d}分',font=F[42],fill=WHITE)
                    d.text((70,818),'休息・渡河の時間は含まない',font=F[26],fill=DIM)
                if key=='e_end':
                    panel(d,(45,170,1010,580),'この動画で確かめたこと',used);d.text((70,236),'・光秀の立場と、1582年までの経緯',font=F[40],fill=WHITE);d.text((70,304),'・現代の道路に沿った参考経路：約20.7km',font=F[40],fill=WHITE);d.text((70,372),'・動機の諸説は、決め手を欠く',font=F[40],fill=WHITE)
                    if shown>=9:d.text((70,468),'山崎の戦い（6/13）は別の動画で',font=FB[40],fill=GOLD)
                if key=='credits':
                    panel(d,(45,170,1390,840),'出典・制作クレジット',used)
                    cr=['地形・写真：国土地理院 地理院タイル（標高・オルソ・陰影起伏図）を加工','歴史概要：Wikipedia（日本語版）本能寺の変・明智光秀ほか（CC BY-SA 4.0）','座標：国土地理院 住所検索（町名レベルの概略位置を含む）','肖像画・錦絵：Wikimedia Commons（パブリックドメイン）','　長興寺・本徳寺・総見寺・高台寺・大阪城天守閣・名古屋市蔵','経路・軍勢・炎・包囲：模式表現（史実の再現ではない）','一次史料（信長公記など）の直接校訂は未実施','音声：VOICEVOX:四国めたん　制作：Blender・FFmpeg']
                    for k,txt in enumerate(cr):d.text((72,232+k*72),txt,font=F[30],fill=WHITE)
            draw_cards(im,ci,t,local,shown,used,key);d=ImageDraw.Draw(im,'RGBA')
            ov=Image.new('RGBA',(1920*SS,1080*SS),(0,0,0,0));od=ImageDraw.Draw(ov)
            if mapspec:draw_map_items(od,scr,spec,t,seg_t,used,key)
            if key=='hook' and hook<1:
                al=int(255*(1-hook));tx=960-tw(d,'天正10年',FB[72])/2;d.text((tx,330),'天正10年',font=FB[72],fill=GOLD+(al,));tx=960-tw(d,'6月2日',FB[72])/2;d.text((tx,420),'6月2日',font=FB[72],fill=WHITE+(al,))
            if hook<1 and not mapspec and m:
                for L in m['labels']:
                    if not(.04<L['x']<.96 and .22<L['y']<.8 and L['depth']>0):continue
                    ax,ay=L['x']*1920,L['y']*1080;bx=stable_slot((key,'3d',L['id']),NAME[L['id']],ax,ay,used)
                    if bx:ss_label(od,(ax,ay),bx,NAME[L['id']],COL[L['id']])
                    else:omitted+=1
            for nm,sa,sb in SC[key].get('images',[]):
                t0=seg_t[sa];t1=seg_list[sb]['end'];FD=.9
                if t0<=t<t1:
                    al=min(1,(t-t0)/FD,(t1-t)/FD);pr=(t-t0)/(t1-t0);im.alpha_composite(gen_image(nm,pr,max(0,al)))
                    im.alpha_composite(statics_img[ci]);d=ImageDraw.Draw(im,'RGBA');d.text((60,806),'イメージ（生成画像・史実の再現ではありません）',font=F[28],fill=(235,240,242,int(255*max(0,al))),stroke_width=4,stroke_fill=(5,10,16,int(255*max(0,al))))
                    ov=Image.new('RGBA',(1920*SS,1080*SS),(0,0,0,0))
            im.alpha_composite(ov.resize((1920,1080),Image.BOX));d=ImageDraw.Draw(im,'RGBA')
            active=next((x for x in seg_list if x['start']<=t<x['end']),None);sub=None
            if active:
                f=FSUB[46];lines=sub_lines(d,active,f,t)
                sub=(60,860,1860,1008);d.rounded_rectangle(sub,12,fill=(5,18,29,242))
                for j,txt in enumerate(lines):
                    w=tw(d,txt,f);assert w<1760;d.text(((1920-w)/2,872+j*62),txt,font=f,fill='#fffcef')
            d.rectangle((48,1012,48+1824*(i+1)/N,1018),fill=(201,173,112))
            proc.stdin.write(im.convert('RGB').tobytes())
            if stills:im.convert('RGB').save(ROOT/'cache'/f'still4_{i}.png')
            if i%30==0:layout.append(dict(frame=i,scene=key,subtitle_box=sub))
            if i%1200==0:print(a,i,flush=True)
    finally:
        proc.stdin.close();proc.wait();log.close()
    assert proc.returncode==0
    if not stills:(ROOT/'cache'/f'hn4_part_{a}_{b}.json').write_text(json.dumps(dict(range=[a,b],omitted_labels=omitted,layout=layout),ensure_ascii=False),encoding='utf8')
def chk_duration():
    r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(ROOT/'out'/'honnoji.mp4')],capture_output=True,text=True);dur=float(r.stdout.strip())
    assert abs(dur-timeline[-1]['end'])<1.0,f'video {dur:.2f}s != timeline end {timeline[-1]["end"]:.2f}s (truncated parts?)'
def final():
    parts=sorted(ROOT.glob('cache/hn4_part_*.mp4'),key=lambda p:int(p.stem.split('_')[2]))
    lst=ROOT/'cache'/'hn4_parts.txt';lst.write_text(''.join(f"file '{p.as_posix()}'\n" for p in parts))
    wav=str(ROOT/'out'/'hn_narration.wav')
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',wav,'-af','loudnorm=I=-15:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True)
    j=json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}',r.stderr,re.S).group(0))
    af=f"loudnorm=I=-15:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
    subprocess.run(['ffmpeg','-y','-v','warning','-f','concat','-safe','0','-i',str(lst),'-i',wav,'-map','0:v','-map','1:a','-c:v','h264_nvenc','-preset','p5','-cq','25','-b:v','0','-pix_fmt','yuv420p','-af',af,'-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest',str(ROOT/'out'/'honnoji.mp4')],check=True)
    chk_duration()
    print('loudnorm input',j['input_i'],'LUFS')

def remix(bgm_db=-16.0,bgm_file='hn_bgm.wav'):
    """add the synthesised BGM under the narration (sidechain ducking), loudness-normalise, and mux onto the already encoded video (stream copy)."""
    nar=str(ROOT/'out'/'hn_narration.wav');bgm=str(ROOT/'out'/bgm_file);mix=str(ROOT/'cache'/'hn_mix.wav')
    fc=f"[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0,asplit=2[n1][n2];[1:a]volume={bgm_db}dB[bg];[bg][n2]sidechaincompress=threshold=0.02:ratio=4:attack=30:release=900:makeup=1[duck];[n1][duck]amix=inputs=2:normalize=0:duration=first[m]"
    subprocess.run(['ffmpeg','-y','-v','warning','-i',nar,'-i',bgm,'-filter_complex',fc,'-map','[m]','-c:a','pcm_s16le',mix],check=True)
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',mix,'-af','loudnorm=I=-15:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True)
    j=json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}',r.stderr,re.S).group(0))
    af=f"loudnorm=I=-15:TP=-1.5:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
    subprocess.run(['ffmpeg','-y','-v','warning','-i',str(ROOT/'out'/'honnoji_nobgm.mp4'),'-i',mix,'-map','0:v','-map','1:a','-c:v','copy','-af',af,'-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest',str(ROOT/'out'/'honnoji.mp4')],check=True)
    print('mix input',j['input_i'],'LUFS (narration+BGM before normalisation)')
if __name__=='__main__':
    if sys.argv[1]=='part':render(int(sys.argv[2]),int(sys.argv[3]))
    elif sys.argv[1]=='final':final()
    elif sys.argv[1]=='remix':remix(float(sys.argv[2]) if len(sys.argv)>2 else -16.0,sys.argv[3] if len(sys.argv)>3 else 'hn_bgm.wav')
