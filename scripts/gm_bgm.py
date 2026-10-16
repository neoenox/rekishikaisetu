"""BGM from 魔王魂 free tracks (credit: 音楽：魔王魂), arranged per scene with crossfades.
Tracks live in assets/bgm_maou/ (downloaded from maou.audio with the user's approval; not committed).
usage: python hn_bgm_maou.py   -> out/gm_bgm.wav (stereo 48 kHz 16-bit), each track pre-levelled to one loudness"""
from pathlib import Path
import json,subprocess,wave
import numpy as np
ROOT=Path(__file__).resolve().parents[1];SR=48000;D=ROOT/'assets'/'bgm_maou'
tl=json.loads((ROOT/'data'/'gm_timeline.json').read_text(encoding='utf8'));T={c['key']:c for c in tl};TOTAL=tl[-1]['end']
# (first scene key, last scene key, track) -- chosen from the site's descriptions/tags (not auditioned by the author)
PLAN=[('intro','intro','piano36'),('why','mercator','piano12'),('measure','others','piano40'),('webmap','end','piano36')]
XF=3.0;TARGET_LUFS=-24.0
def load(name):
    raw=subprocess.run(['ffmpeg','-v','error','-i',str(D/f'maou_bgm_{name}.mp3'),'-ar',str(SR),'-ac','2','-f','f32le','-'],capture_output=True).stdout
    x=np.frombuffer(raw,np.float32).reshape(-1,2).T.astype(np.float64)
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(D/f'maou_bgm_{name}.mp3'),'-af','ebur128','-f','null','-'],capture_output=True,text=True,encoding='utf8',errors='replace').stderr
    lufs=float(r.split('Integrated loudness:')[1].split('I:')[1].split('LUFS')[0]);return x*10**((TARGET_LUFS-lufs)/20)
def fade(n,kind):
    u=np.linspace(0,1,n);return np.sin(u*np.pi/2) if kind=='in' else np.cos(u*np.pi/2)
def fill(x,length):
    """loop x (with equal-power crossfade at the seam) to the requested length"""
    xf=int(XF*SR);out=x.copy()
    while out.shape[1]<length:
        a,b=out,x;out=np.concatenate([a[:,:-xf],a[:,-xf:]*fade(xf,'out')+b[:,:xf]*fade(xf,'in'),b[:,xf:]],axis=1)
    return out[:,:length]
N=int(TOTAL*SR);mix=np.zeros((2,N));cache={}
for a,b,name in PLAN:
    s=T[a]['start'];e=T[b]['end'];xf=XF/2
    s0=max(0,s-xf);e0=min(TOTAL,e+xf);n=int((e0-s0)*SR)
    if name not in cache:cache[name]=load(name)
    seg=fill(cache[name],n).copy();fi=int(XF*SR) if s0>0 else 0;fo=int(XF*SR) if e0<TOTAL else 0
    if fi:seg[:,:fi]*=fade(fi,'in')
    if fo:seg[:,-fo:]*=fade(fo,'out')
    i=int(s0*SR);mix[:,i:i+n]+=seg[:,:N-i]
    print(f'{s:6.1f}-{e:6.1f}s  {a}..{b}  <- {name} ({cache[name].shape[1]/SR:.0f}s track)')
fi=int(2*SR);fo=int(6*SR);env=np.ones(N);env[:fi]=np.linspace(0,1,fi);env[-fo:]=np.minimum(env[-fo:],np.linspace(1,0,fo)**1.5);mix*=env
peak=np.abs(mix).max()
if peak>.9:mix*=.9/peak
pcm=(mix.T*32767).astype(np.int16)
with wave.open(str(ROOT/'out'/'gm_bgm.wav'),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())
print('wrote out/gm_bgm.wav  rms dBFS',round(20*np.log10(np.sqrt(np.mean(mix**2))),1),' peak',round(20*np.log10(np.abs(mix).max()),1))
