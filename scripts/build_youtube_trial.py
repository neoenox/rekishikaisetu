"""Editorial trial: focused two-unit story with short captions and controlled motion."""
from pathlib import Path
import json,sys,subprocess,math,time,textwrap,re
import numpy as np
from PIL import Image,ImageDraw
from compose_earth import EarthFilm,F,B,COLORS
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
class Trial(EarthFilm):
 def __init__(self):
  super().__init__();self.scenes=load('data/trial_timeline.json');self.audio=load('out/trial_audio_report.json');self.layout=[];self.captions=[]
  for seg in self.audio['segments']:
   pieces=re.split(r'(?<=[、。])',seg['text']);chunks=[];current=''
   for piece in pieces:
    if len(current+piece)>28:
     if current:chunks.append(current);current=''
     while len(piece)>28:chunks.append(piece[:28]);piece=piece[28:]
    current+=piece
   if current:chunks.append(current)
   cursor=seg['start'];total=sum(map(len,chunks))
   for chunk in chunks:
    duration=(seg['end']-seg['start'])*len(chunk)/total;self.captions.append(dict(text=chunk,start=cursor,end=cursor+duration));cursor+=duration
  self.sprites={k:[im.resize((150,120)) for im in v] for k,v in self.sprites.items()}
 def frame(self,i):
  t=i/30;s=next(s for s in self.scenes if s['start']<=t<s['end']+.00001);sid=s['id'];phase=(t-s['start'])/s['duration'];view='oblique' if sid==2 else 'overview';zoom=1.10 if sid in [3,4] else 1.;cx,cy=(900,580) if zoom>1 else (960,540)
  image=self.maps[view].transform((1920,1080),Image.Transform.AFFINE,(1/zoom,0,cx-960/zoom,0,1/zoom,cy-540/zoom),resample=Image.Resampling.BICUBIC)
  def screen(p):return (np.asarray(p)-[cx,cy])*zoom+[960,540]
  draw=ImageDraw.Draw(image);draw.text((42,20),s['title'],font=B[50],fill='#fff8e5',stroke_width=4,stroke_fill='#06131f');draw.text((44,88),s['category'],font=F[28],fill='#ffd16d',stroke_width=3,stroke_fill='#06131f')
  rects=[];progress=(.12+.48*phase if sid==0 else (min(.70,phase*.82) if sid==3 else (.70 if sid in [4,5] else 0)))
  if sid!=2:
   a=self.units['otani'];blue=screen(self.at(a['x_m'],a['y_m']));gold=screen(self.route_point(progress))
   if sid in [0,3,4,5]:
    route=[tuple(screen(p)) for p in self.route];draw.line(route,fill='#071925',width=13);draw.line(route,fill='#ffd16d',width=6)
   for k,point,color in [('otani',blue,'west'),('kobaya',gold,'kobaya')]:
    x,y=point;draw=ImageDraw.Draw(image);draw.ellipse((x-22,y-13,x+22,y+13),fill='#071925',outline=COLORS[k],width=3)
    walking=k=='kobaya' and sid in [0,3] and (sid==0 or progress<.70);sprite=self.sprites[color][int(t*12)%12 if walking else 0];image.alpha_composite(sprite,(round(x-75),round(y-85)))
   self.card(image,'otani',blue,blue+[-185,70],rects)
   portrait=gold+[280,-30];portrait[1]=min(700,portrait[1]);self.card(image,'kobaya',gold,portrait,rects)
   if sid==1:
    image.alpha_composite(self.panels['kobaya'],(1480,175));draw=ImageDraw.Draw(image);draw.text((45,160),'陣跡の配置を確認',font=B[34],fill='white',stroke_width=3,stroke_fill='#06131f')
   if sid==4:
    draw=ImageDraw.Draw(image);draw.rounded_rectangle((1290,600,1875,835),14,fill='#071925',outline='#ffd16d',width=2)
    for j,(text,font) in enumerate([('試験経路の水平距離',B[34]),('約1.45 km',B[50]),('上り91m ／ 下り211m',F[30])]):draw.text((1315,618+j*68),text,font=font,fill='#fff8e5')
   if sid==5:
    draw=ImageDraw.Draw(image);draw.text((1200,680),'近い距離にも、起伏がある',font=B[34],fill='#ffd16d',stroke_width=3,stroke_fill='#06131f')
  else:
   draw.text((70,210),'丘陵と盆地のつながりを見る',font=B[38],fill='white',stroke_width=3,stroke_fill='#06131f')
  draw=ImageDraw.Draw(image);caption=next((c for c in self.captions if c['start']<=t<c['end']),None)
  if caption:
   w=draw.textlength(caption['text'],font=B[46]);assert w<1500;draw.text(((1920-w)/2,958),caption['text'],font=B[46],fill='#fffcef',stroke_width=4,stroke_fill='#06131f')
  source='Google Earth / Airbus';w=draw.textlength(source,font=F[20]);draw.text((1892-w,1046),source,font=F[20],fill='white',stroke_width=2,stroke_fill='#06131f')
  for r in rects:
   x0,y0,x1,y1=r['box'];assert 0<=x0<x1<=1920 and 130<=y0<y1<=900,r
  if rects:
   p,q=[r['box'] for r in rects];assert not(p[0]<q[2] and p[2]>q[0] and p[1]<q[3] and p[3]>q[1])
  if i%30==0:self.layout.append(dict(frame=i,scene=sid,progress=progress,view=view,zoom=zoom,cards=rects,caption=caption['text'] if caption else None,explicit_reset=sid==1))
  return image

def render(a,b):
 f=Trial();dest=ROOT/'cache'/f'trial_part_{a}_{b}.mp4';p=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','pipe:0','-an','-c:v','h264_nvenc','-cq','19','-preset','p4','-pix_fmt','yuv420p',str(dest)],stdin=subprocess.PIPE)
 try:
  for i in range(a,b):p.stdin.write(f.frame(i).convert('RGB').tobytes())
 finally:p.stdin.close();p.wait()
 assert p.returncode==0
 (ROOT/'cache'/f'trial_layout_{a}_{b}.json').write_text(json.dumps(f.layout,ensure_ascii=False),encoding='utf8');print('trial range complete',a,b,flush=True)
def main():
 f=Trial();n=round(f.audio['total_seconds']*30);edges=[round(i*n/3) for i in range(4)];workers=[]
 for a,b in zip(edges,edges[1:]):workers.append((a,b,subprocess.Popen([sys.executable,__file__,str(a),str(b)])))
 for a,b,p in workers:assert p.wait()==0
 concat=ROOT/'cache/trial_concat.txt';concat.write_text('\n'.join(f"file 'trial_part_{a}_{b}.mp4'" for a,b,_ in workers),encoding='utf8')
 dest=ROOT/'out/sekigahara_youtube_trial.mp4'
 subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(concat),'-i',str(ROOT/'out/trial_narration.wav'),'-c:v','copy','-af','loudnorm=I=-18:TP=-1.5:LRA=7','-c:a','aac','-b:a','192k','-ar','48000','-shortest','-movflags','+faststart',str(dest)],check=True)
 layouts=sorted([r for a,b,_ in workers for r in load(f'cache/trial_layout_{a}_{b}.json')],key=lambda r:r['frame']);(ROOT/'out/trial_layout.json').write_text(json.dumps(layouts,ensure_ascii=False,indent=2),encoding='utf8')
 def stamp(t):
  ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
 (ROOT/'out/trial_subtitles.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(f.captions))+'\n',encoding='utf8')
 for s in f.scenes:f.frame(round((s['start']+s['duration']/2)*30)).save(ROOT/'out'/f'trial_scene_{s["id"]}.png')
 print('TRIAL VIDEO READY',n,n/30,flush=True)
if __name__=='__main__':
 if len(sys.argv)>1:render(int(sys.argv[1]),int(sys.argv[2]))
 else:main()
