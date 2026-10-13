"""Composite real Remotion cards, DEM frames, labels, measured charts and PCM."""
from pathlib import Path
import json,subprocess,sys,time,math,textwrap,wave
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.interpolate import RegularGridInterpolator
ROOT=Path(__file__).resolve().parents[1]
FONT='C:/Windows/Fonts/YuGothM.ttc';BOLD='C:/Windows/Fonts/YuGothB.ttc'
F={n:ImageFont.truetype(FONT,n) for n in [18,21,24,28,32,34,40,46]};FB=ImageFont.truetype(BOLD,28)
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def overlap(a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
def label(draw,text,x,y,used,color):
    width=math.ceil(draw.textlength(text,font=F[40]))+32;height=64
    for dx,dy in [(0,-70),(0,16),(0,-145),(-width/2,16),(width/2,-70),(0,90),(0,-215)]:
        xx=max(35,min(1885-width,x-width/2+dx));yy=y+dy
        box=(int(xx),int(yy),int(xx+width),int(yy+height))
        if yy<205 or yy+height>855 or any(overlap(box,b) for b in used):continue
        draw.line([(x,y),(xx+width/2,yy+height/2)],fill=color,width=2);draw.rounded_rectangle(box,radius=5,fill=(7,24,36,238),outline=color,width=2);draw.text((xx+16,yy+5),text,font=F[40],fill=(245,245,235));used.append(box);return box
    return None
def drawchart(draw,analysis,scene_id,used):
    box=(1000,475,1445,805);used.append(box);draw.rounded_rectangle(box,12,fill=(7,24,36,235),outline=(176,153,100),width=2)
    draw.text((1020,490),'仮説経路 / 現代DEM解析',font=FB,fill='#efc976')
    d=analysis['horizontal_distance_m'];up=analysis['ascent_m'];down=analysis['descent_m']
    draw.text((1020,540),f'水平距離 {d/1000:.2f} km',font=F[24],fill='white')
    if scene_id==8:
        for i,v in enumerate(analysis['sensitivity']):
            y=590+i*53;draw.text((1020,y),f'{v["assumed_speed_m_s"]:.1f} m/s',font=F[21],fill='white');length=v['minutes']/50*205;draw.rectangle((1120,y+6,1120+length,y+25),fill='#bba56e');draw.text((1120+length+7,y),f'{v["minutes"]:.1f}分',font=F[18],fill='white')
    else:
        draw.text((1020,577),f'累積上り {up:.0f}m / 下り {down:.0f}m',font=F[21],fill='white');profile=analysis['profile'];e=profile['elevation_m'];mi,ma=min(e),max(e)
        pts=[(1020+v/d*395,745-(z-mi)/max(1,ma-mi)*100) for v,z in zip(profile['distance_m'],e)];draw.line(pts,fill='#efc976',width=4)
        draw.text((1020,755),'直線経路。道路・戦闘を考慮せず',font=F[18],fill='#b8c8cb')
def main(mode,level,range_start=None,range_end=None):
    folder=ROOT/'cache'/f'render_l{level}_{mode}';report=load(str(folder.relative_to(ROOT)/'render_report.json'));frames=report['frames'];units=load('data/units.json');names={u['id']:u['name']+'（推定）' for u in units};analysis=load('out/analysis.json');audio=load('out/audio_report.json');timeline=load('data/timeline.json');cards={}
    grid=np.load(ROOT/'data'/'terrain.npz');interp=RegularGridInterpolator((grid['ys'],grid['xs']),grid['h']);a=next(u for u in units if u['id']=='kobaya');b=next(u for u in units if u['id']=='otani')
    def project(point,fr):
        camera=np.array(fr['camera']);forward=np.array(fr['target'])-camera;forward/=np.linalg.norm(forward);right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,forward);delta=np.array(point)-camera;scale=fr.get('ortho_scale',9200)
        return np.array([960+np.dot(delta,right)*1920/scale,540-np.dot(delta,up)*1920/scale])
    if mode=='comparison':
        card=Image.open(ROOT/'cache'/'cards'/f'level_{level}.png').convert('RGBA');pcm=[]
        from audio import readwav,writewav
        pcm,rate=readwav(ROOT/'cache'/'audio'/'scene_06.wav');pcm=np.pad(pcm,(0,25*rate-len(pcm)));audiofile=ROOT/'cache'/'audio'/'comparison.wav';writewav(audiofile,pcm,rate)
        segments=[{**x,'start':x['start']-timeline[6]['start'],'end':x['end']-timeline[6]['start']} for x in audio['segments'] if x['scene']==6]
        filename=['','level1_terrain_markers.mp4','level2_terrain_troops.mp4','level3_cinematic.mp4'][level]
    else:
        audiofile=ROOT/'out'/'narration.wav';segments=audio['segments'];filename='pilot_3to5min.mp4'
        cards={c['id']:Image.open(ROOT/'cache'/'cards'/f'scene_{c["id"]:02}.png').convert('RGBA') for c in timeline}
    is_chunk=range_start is not None
    if is_chunk:
        assert mode=='pilot';frames=frames[range_start:range_end];filename=f'pilot_part_{range_start}_{range_end}.mp4'
    output=(ROOT/'cache'/filename) if is_chunk else ROOT/'out'/filename;started=time.perf_counter();log=(ROOT/'logs'/f'encode_{mode}_{level}_{range_start}.log').open('wb')
    cmd=['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','pipe:0','-i',str(audiofile),'-map','0:v:0','-map','1:a:0','-c:v','h264_nvenc','-preset','p4','-cq','20','-b:v','0','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest',str(output)]
    if is_chunk:
        cmd=['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','pipe:0','-an','-c:v','h264_nvenc','-preset','p4','-cq','20','-b:v','0','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log);layout=[];missing=0
    try:
        for fr in frames:
            i=fr['frame']
            t=i/30;scene_id=fr.get('chapter') if mode=='pilot' else 6
            image=Image.open(folder/f'{i:04}.jpg' if mode=='pilot' else folder/f'{i:04}.png').convert('RGBA');image.alpha_composite(cards[scene_id] if mode=='pilot' else card);draw=ImageDraw.Draw(image)
            if mode=='comparison' or scene_id in [4,6,7,8]:
                p=i/(len(frames)-1) if mode=='comparison' else ((t-timeline[6]['start'])/timeline[6]['duration'] if scene_id==6 else (.5 if scene_id in [7,8] else 0))
                xx=a['x_m']*(1-p)+b['x_m']*p;yy=a['y_m']*(1-p)+b['y_m']*p;zz=float(interp([[yy,xx]])[0])+19
                tip=project((xx,yy,zz),fr);ahead=project((xx+(b['x_m']-a['x_m'])*.01,yy+(b['y_m']-a['y_m'])*.01,zz),fr);direction=ahead-tip;direction/=np.linalg.norm(direction);normal=np.array([-direction[1],direction[0]])
                draw.polygon([tuple(tip+direction*15),tuple(tip-direction*12+normal*10),tuple(tip-direction*12-normal*10)],fill='#f3c66b',outline='#795b20')
            used=[(0,0,1920,200),(0,1015,1920,1080),(1485,220,1875,530),(60,860,1860,1008)]
            if mode=='pilot' and scene_id==11:used.append((70,245,1310,640))
            if mode=='pilot' and scene_id in [7,8]:drawchart(draw,analysis,scene_id,used)
            labels=[]
            for p in fr['labels']:
                if not (.025<p['x']<.975 and .15<p['y']<.80 and p['depth']>0):continue
                color={'ishida':'#4e9bff','otani':'#4e9bff','ieyasu':'#ff6255','kobaya':'#efc976'}[p['id']]
                box=label(draw,names[p['id']],p['x']*1920,p['y']*1080,used,color)
                if box:labels.append({'id':p['id'],'box':box})
                else:missing+=1
            active=next((x for x in segments if x['start']<=t<x['end']),None)
            subbox=None
            if active:
                lines=textwrap.wrap(active['text'],width=36);assert len(lines)<=2,(active['text'],lines)
                subbox=(60,860,1860,1008);draw.rounded_rectangle(subbox,12,fill=(5,18,29,240))
                for j,text in enumerate(lines):
                    w=draw.textlength(text,font=F[46]);assert w<1760
                    draw.text(((1920-w)/2,871+j*62),text,font=F[46],fill='#fffcef')
            # Model clock is explicitly separate from historical time.
            if mode=='comparison' or scene_id==6:
                val=(i/len(frames) if mode=='comparison' else (t-timeline[6]['start'])/timeline[6]['duration'])*60
                draw.rounded_rectangle((48,211,870,265),7,fill=(7,24,36,238));draw.text((62,219),f'模式モデル時刻 {val:04.1f} / 60分（史実時刻ではない）',font=F[28],fill='#efc976')
            if mode=='pilot' and scene_id==11:
                box=(70,245,1310,640);draw.rounded_rectangle(box,12,fill=(7,24,36,235))
                credit=['地形：国土地理院 地理院タイル（標高）を加工','歴史参照：岐阜関ケ原古戦場記念館 / 関ケ原町歴史民俗学習館','位置：株式会社CCL 大垣支社 / 関ヶ原位置情報リスト2013年度','CC BY 3.0 / 座標変換・説明用配置に加工','音声：VOICEVOX:四国めたん','モデル・材質・図表：本PoC自作 / Blender + Remotion + FFmpeg','出典URL・取得日・仮定・検証結果は同梱ファイルに記録']
                for j,text in enumerate(credit):draw.text((95,265+j*48),text,font=F[24],fill='white')
            # Exact scene/clip progress.
            draw.rectangle((48,1015,48+1824*(i+1)/len(report['frames']),1020),fill='#c9ad70')
            proc.stdin.write(image.convert('RGB').tobytes())
            if i%30==0:layout.append({'frame':i,'labels':labels,'subtitle_box':subbox,'category_visible':True})
            if i%300==0:print(filename,i,'/',len(frames),flush=True)
    finally:
        proc.stdin.close();proc.wait();log.close()
    assert proc.returncode==0,'FFmpeg encoding failed; inspect encode log'
    result={'file':filename,'frame_count':len(frames),'duration':len(frames)/30,'encode_composite_seconds':time.perf_counter()-started,'renderer':'Blender 4.5.3 Eevee','compositor':'Remotion real rendered RGBA cards + Pillow per-frame label/subtitle/charts + FFmpeg NVENC','layout_samples':layout,'omitted_label_instances':missing,'all_visible_claim_categories':True,'native_resolution':[1920,1080],'native_fps':30}
    result.update(range_start=range_start,range_end=range_end)
    path=(ROOT/'cache'/f'composition_{mode}_{level}_{range_start}_{range_end}.json') if is_chunk else (ROOT/'out'/f'composition_{mode}_{level}.json')
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print('DONE',filename,result['encode_composite_seconds'])
if __name__=='__main__':
    if sys.argv[1]=='pilot' and len(sys.argv)==3:
        from compose_pilot_parallel import main as parallel_main
        parallel_main()
    else:main(sys.argv[1],int(sys.argv[2]),int(sys.argv[3]) if len(sys.argv)>3 else None,int(sys.argv[4]) if len(sys.argv)>4 else None)
