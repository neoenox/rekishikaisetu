"""Educational Google Earth captures with coordinate-registered animated symbols.

The captures stay as 2D footage. No Google imagery is extracted into a 3D model.
Army sprites are original Blender artwork; historic paths and troop counts are
not asserted. Google and the view-specific data providers remain on every frame.
"""
from pathlib import Path
import json, math, subprocess, sys, time, textwrap, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pyproj import Transformer
from scipy.interpolate import RegularGridInterpolator

ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
FONT='C:/Windows/Fonts/YuGothM.ttc';BOLD='C:/Windows/Fonts/YuGothB.ttc'
F={n:ImageFont.truetype(FONT,n) for n in [20,22,24,26,28,30,34,38,40,46,50]}
B={n:ImageFont.truetype(BOLD,n) for n in [28,30,34,38,40,46,50]}
COLORS={'ishida':'#71b5ff','otani':'#71b5ff','ieyasu':'#ff8777','kobaya':'#ffd16d'}

class EarthFilm:
    def __init__(self):
        self.scenes=load('data/earth_timeline.json');self.audio=load('out/earth_audio_report.json')
        self.units={u['id']:u for u in load('data/units.json')};self.portraits={p['id']:p for p in load('data/portraits.json')}
        self.maps={k:Image.open(ROOT/'assets'/'earth'/f'{k}.png').convert('RGBA') for k in ['overview','regional','oblique']}
        self.sprites={k:[Image.open(ROOT/'assets'/'army'/f'{k}_{i:02}.png').convert('RGBA').resize((210,168),Image.Resampling.LANCZOS) for i in range(12)] for k in ['west','east','kobaya']}
        self.r=load('data/earth_registration.json');self.tf=Transformer.from_crs(4979,4978,always_xy=True)
        self.xy_to_ll=Transformer.from_crs('+proj=aeqd +lat_0=35.355 +lon_0=136.472 +datum=WGS84 +units=m',4326,always_xy=True)
        lat,lon=np.radians([self.r['origin_lat'],self.r['origin_lon']])
        self.east=np.array([-np.sin(lon),np.cos(lon),0]);self.north=np.array([-np.sin(lat)*np.cos(lon),-np.sin(lat)*np.sin(lon),np.cos(lat)])
        self.up=np.array([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)])
        self.origin=np.array(self.tf.transform(self.r['origin_lon'],self.r['origin_lat'],0))
        grid=np.load(ROOT/'data'/'terrain.npz');self.heights=RegularGridInterpolator((grid['ys'],grid['xs']),grid['h'])
        self.icons={};self.panels={};self.layout=[]
        crops={'kobaya':(.19,.06,.71,.41),'ishida':(.27,.14,.69,.45),'ieyasu':(.32,.30,.62,.59)}
        for k,p in self.portraits.items():
            im=Image.open(ROOT/p['file']).convert('RGBA');w,h=im.size;box=tuple(round(v*(w if i%2==0 else h)) for i,v in enumerate(crops[k]));face=ImageOps.fit(im.crop(box),(136,136),method=Image.Resampling.LANCZOS)
            icon=Image.new('RGBA',(148,148));d=ImageDraw.Draw(icon);d.ellipse((1,1,146,146),fill=COLORS[k]);mask=Image.new('L',(136,136));ImageDraw.Draw(mask).ellipse((0,0,135,135),fill=255);icon.paste(face,(6,6),mask);self.icons[k]=icon
            panel=Image.new('RGBA',(380,646));d=ImageDraw.Draw(panel);d.rounded_rectangle((0,0,379,645),18,fill=(7,19,30,247),outline=COLORS[k],width=3)
            d.text((22,16),self.units[k]['name'],font=B[46],fill='white')
            portrait=ImageOps.contain(im,(332,420),Image.Resampling.LANCZOS);panel.alpha_composite(portrait,((380-portrait.width)//2,86))
            lines={'kobaya':['小早川秀秋像（一部）','高台寺蔵／17世紀前半','作者不詳'],'ishida':['石田三成像（模本）','東京大学史料編纂所蔵','作者不詳'],'ieyasu':['徳川家康像','大阪城天守閣','狩野探幽']}[k]
            for j,line in enumerate(lines):d.text((20,520+j*31),line,font=F[24],fill='#e9e1ce')
            d.text((20,615),'Wikimedia Commons / 肖像は識別用',font=F[20],fill='#c5d0d6')
            self.panels[k]=panel
        self.route=[self.route_point(p) for p in np.linspace(0,1,100)]

    def at(self,x,y):
        lon,lat=self.xy_to_ll.transform(x,y);h=float(self.heights([[y,x]])[0]);p=np.array(self.tf.transform(lon,lat,h))-self.origin
        cx,cy,f,alt=self.r['parameters'];return np.array([cx+f*(p@self.east)/(alt-p@self.up),cy-f*(p@self.north)/(alt-p@self.up)])

    def route_point(self,p):
        a,b=self.units['kobaya'],self.units['otani'];return self.at(a['x_m']*(1-p)+b['x_m']*p,a['y_m']*(1-p)+b['y_m']*p)

    def card(self,image,key,anchor,center,rects):
        d=ImageDraw.Draw(image);color=COLORS[key];x,y=map(float,center);ax,ay=map(float,anchor)
        if key=='otani':
            box=(int(x-150),int(y-38),int(x+150),int(y+52));d.line([(ax,ay),(x,y)],fill=color,width=4);d.rounded_rectangle(box,12,fill='#071925',outline=color,width=3);d.text((x-120,y-31),'大谷吉継',font=B[38],fill='white');d.text((x-120,y+13),'陣跡（位置推定）',font=F[24],fill='#cbd8e2')
        else:
            box=(int(x-160),int(y-74),int(x+160),int(y+132));d.line([(ax,ay),(x,y+45)],fill=color,width=4);image.alpha_composite(self.icons[key],(int(x-74),int(y-74)));d=ImageDraw.Draw(image)
            text=self.units[key]['name'];w=d.textlength(text,font=B[38]);d.rounded_rectangle((x-160,y+80,x+160,y+132),9,fill='#071925',outline=color,width=3);d.text((x-w/2,y+82),text,font=B[38],fill='white')
        rects.append({'id':key,'box':box,'anchor':[ax,ay],'portrait':key!='otani'})

    def frame(self,i,preview=False):
        t=i/30;scene=next(c for c in self.scenes if c['start']<=t<c['end']+.00001);sid=scene['id'];local=t-scene['start'];phase=local/scene['duration']
        # Actual Earth oblique footage is used for the terrain explanation.
        view='regional' if sid==0 and local<4 else ('oblique' if sid==1 else 'overview')
        image=self.maps[view].copy();draw=ImageDraw.Draw(image);rects=[]
        draw.rectangle((0,0,1920,161),fill='#081b29');draw.text((44,13),scene['title'],font=B[50],fill='#fff9e9');draw.text((46,84),scene['category'],font=F[28],fill='#ffd16d')
        draw.text((46,124),'現代の景観に、陣跡の記念地点と説明用の軍勢を重ねています',font=F[24],fill='#bed0dc')
        # Credit line is retyped legibly; the native Google attribution strip at
        # y=1050..1079 is also left untouched, pixel for pixel.
        source='Google Earth / Airbus' if view!='regional' else 'Google Earth / Landsat / Copernicus / Data SIO, NOAA, U.S. Navy, NGA, GEBCO'
        draw.rectangle((0,1008,1920,1049),fill='#081b29');draw.text((25,1015),source,font=F[22],fill='white');draw.text((1510,1015),'VOICEVOX:四国めたん',font=F[22],fill='white')
        active_key={3:'ishida',4:'kobaya',5:'ieyasu',9:'kobaya'}.get(sid)
        if active_key:image.alpha_composite(self.panels[active_key],(30,187))
        if view=='regional':
            draw=ImageDraw.Draw(image);draw.ellipse((946,526,974,554),outline='#ffd16d',width=5);draw.rounded_rectangle((1000,487,1310,555),12,fill='#071925');draw.text((1025,495),'関ヶ原',font=B[46],fill='#ffd16d')
        elif view=='oblique':
            draw=ImageDraw.Draw(image);draw.rounded_rectangle((48,220,665,380),15,fill=(7,25,37,240));draw.text((73,240),'Google Earthの3D表示',font=B[38],fill='white');draw.text((73,303),'山並みと盆地の位置関係を見る',font=F[30],fill='#ffd16d')
        else:
            progress=min(.92,max(0,(phase-.07)/.86)) if sid==6 else (0.92 if sid in [7,8] else 0)
            pos={k:self.at(u['x_m'],u['y_m']) for k,u in self.units.items()};pos['kobaya']=self.route_point(progress)
            draw=ImageDraw.Draw(image)
            if sid in [4,6,7,8]:
                route=[tuple(p) for p in self.route];draw.line(route,fill='#13222d',width=15);draw.line(route,fill='#ffd16d',width=7)
                if sid==6:
                    direction=pos['otani']-pos['kobaya'];direction/=np.linalg.norm(direction);normal=np.array([-direction[1],direction[0]]);tip=pos['kobaya']
                    draw.polygon([tuple(tip+direction*26),tuple(tip-direction*12+normal*18),tuple(tip-direction*12-normal*18)],fill='#fff1b0')
            for k in ['ishida','ieyasu','otani','kobaya']:
                point=pos[k];draw=ImageDraw.Draw(image);x,y=point;draw.ellipse((x-29,y-18,x+29,y+18),fill=(7,25,37,180),outline=COLORS[k],width=3)
                spr=self.sprites[{'ishida':'west','ieyasu':'east','otani':'west','kobaya':'kobaya'}[k]][int(t*12)%12 if k=='kobaya' and sid==6 and progress<.92 else 0]
                image.alpha_composite(spr,(round(x-105),round(y-110)))
            centers={'ishida':pos['ishida']+np.array([210,5]),'ieyasu':pos['ieyasu']+np.array([220,-25]),'otani':np.array([600,560]),'kobaya':pos['kobaya']+np.array([280,-25])}
            centers['kobaya'][1]=min(720,centers['kobaya'][1])
            for k in ['ishida','ieyasu','otani','kobaya']:self.card(image,k,pos[k],centers[k],rects)
            draw=ImageDraw.Draw(image)
            if sid in [6,7,8]:
                draw.rounded_rectangle((38,174,568,230),10,fill='#071925');draw.text((55,182),'模式経路／兵数・時刻は再現しない',font=F[28],fill='#ffd16d')
            if sid in [7,8]:
                a=load('out/analysis.json');draw.rounded_rectangle((1250,650,1875,843),15,fill='#071925',outline='#ffd16d',width=2)
                draw.text((1270,662),'現代DEMで試験経路を測る',font=B[34],fill='#ffd16d')
                if sid==7:
                    draw.text((1270,716),f'水平距離 {a["horizontal_distance_m"]/1000:.2f} km',font=F[34],fill='white');draw.text((1270,771),f'上り {a["ascent_m"]:.0f}m ／ 下り {a["descent_m"]:.0f}m',font=F[30],fill='white')
                else:
                    draw.text((1270,717),'仮定 0.5 / 1.0 / 1.5 m/s',font=F[34],fill='white');draw.text((1270,772),'所要時間 48.2 / 24.1 / 16.1分',font=F[30],fill='white')
            if sid==11:
                image.alpha_composite(self.maps['overview'].crop((0,162,1920,865)),(0,162));rects=[]
                for key,x in [('kobaya',620),('ishida',1020),('ieyasu',1420)]:image.alpha_composite(self.panels[key],(x,187))
                draw=ImageDraw.Draw(image)
                draw.rounded_rectangle((35,184,590,835),15,fill='#071925');lines=['背景：Google Earth','画像提供元：Airbus ほか','肖像：Wikimedia Commons','小早川秀秋像：高台寺蔵','石田三成像（模本）：','東京大学史料編纂所蔵','徳川家康像：大阪城天守閣','地形解析：国土地理院DEM','陣跡座標：株式会社CCL','音声：VOICEVOX:四国めたん','軍勢：自作3D記号（実数でない）']
                for j,line in enumerate(lines):draw.text((55,205+j*53),line,font=F[26],fill='white')
        draw=ImageDraw.Draw(image)
        for record in rects:
            x0,y0,x1,y1=record['box'];assert 0<=x0<x1<=1920 and 162<=y0<y1<=865,record
        for a in range(len(rects)):
            for b in range(a+1,len(rects)):
                p,q=rects[a]['box'],rects[b]['box']
                assert not (p[0]<q[2] and p[2]>q[0] and p[1]<q[3] and p[3]>q[1]),(sid,rects[a],rects[b])
        active=next((s for s in self.audio['segments'] if s['start']<=t<s['end']),None)
        subtitle_box=None
        if active:
            lines=textwrap.wrap(active['text'],width=36);assert len(lines)<=2,active['text'];subtitle_box=(50,865,1870,1000);draw.rounded_rectangle(subtitle_box,13,fill='#06131f')
            for j,line in enumerate(lines):
                w=draw.textlength(line,font=B[46]);assert w<=1770,(line,w);draw.text(((1920-w)/2,873+j*60),line,font=B[46],fill='#fffcef')
        if i%30==0:self.layout.append({'frame':i,'scene':sid,'view':view,'cards':rects,'subtitle_box':subtitle_box,'native_credit_strip_preserved':True,'source_text':source})
        if sid==6 and i%30==0:self.layout[-1]['moving_anchor']=pos['kobaya'].tolist();self.layout[-1]['portrait_center']=centers['kobaya'].tolist()
        return image

def main(start=None,end=None):
    film=EarthFilm();n=round(film.audio['total_seconds']*30);a=int(start or 0);b=int(end or n);chunk=start is not None
    dest=ROOT/'cache'/f'earth_part_{a}_{b}.mp4' if chunk else ROOT/'out'/'sekigahara_google_earth_portraits.mp4'
    cmd=['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','pipe:0']
    if not chunk:cmd+=['-i',str(ROOT/'out'/'earth_narration.wav')]
    cmd+=['-c:v','h264_nvenc','-preset','p4','-cq','19','-b:v','0','-pix_fmt','yuv420p']
    cmd+=['-an'] if chunk else ['-c:a','aac','-b:a','192k','-ar','48000','-shortest']
    cmd+=['-movflags','+faststart',str(dest)]
    log=(ROOT/'logs'/f'earth_encode_{a}.log').open('wb');p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log);started=time.time()
    try:
        for i in range(a,b):
            im=film.frame(i);p.stdin.write(im.convert('RGB').tobytes())
            if i%300==0:print('earth frame',i,'/',n,flush=True)
    finally:p.stdin.close();p.wait();log.close()
    assert p.returncode==0
    report={'file':dest.name,'range':[a,b],'frames':b-a,'seconds':(b-a)/30,'composite_seconds':time.time()-started,'layout_samples':film.layout,'background':'actual Google Earth UI captures','army':'original articulated Blender 3D symbol sprites composited in 2D','portrait_motion':'fixed horizontal +280 px; vertical -25 px clamped to720 for subtitle clearance','registration':film.r,'limits':['Modern imagery, not a reconstruction of 1600','Symbolic straight route and enlarged troop symbols, not historical troop counts or exact paths','2D compositing over Earth footage; no Google 3D assets exported','This visual revision does not establish historical completeness']}
    (ROOT/'cache'/f'earth_composition_{a}_{b}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print('EARTH DONE',dest,flush=True)
if __name__=='__main__':main(*(sys.argv[1:]))
