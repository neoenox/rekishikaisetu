"""Original BGM, synthesised from scratch (no samples, no third-party music -> no licence to attribute).
Miyako-bushi-like scale (D E♭ G A B♭), koto-like plucks, drone/pad, heartbeat and taiko-like hits.
Intensity follows the narrative (calm profile -> build-up in May -> peak at the attack -> resolve).
usage: python hn_bgm.py [seconds]   -> out/hn_bgm.wav (stereo, 48 kHz, 16-bit)"""
from pathlib import Path
import json,sys,wave
import numpy as np
from scipy.signal import fftconvolve,butter,sosfilt
from scipy.ndimage import uniform_filter1d
ROOT=Path(__file__).resolve().parents[1]
SR=48000
tl=json.loads((ROOT/'data'/'hn_timeline.json').read_text(encoding='utf8'))
TOTAL=tl[-1]['end'] if len(sys.argv)<2 else float(sys.argv[1])
N=int(TOTAL*SR);rng=np.random.default_rng(1582)
# intensity (start,end) per scene key: 0 calm .. 1 peak
PROFILE={'hook':(.55,.8),'a_origin':(.18,.22),'a_retainer':(.22,.26),'a_tanba':(.26,.3),'b_peak':(.34,.38),'b_west':(.4,.46),'c_ieyasu':(.46,.5),'c_atago':(.52,.6),'c_nobunaga':(.5,.42),
         'd_depart':(.58,.64),'d_oi':(.64,.7),'d_katsura':(.7,.76),'d_temple':(.5,.45),'d_attack':(.85,1.0),'d_nijo':(.7,.5),'d_time':(.36,.32),'e_motive':(.38,.42),'e_end':(.3,.08)}
def intensity_curve():
    t=np.arange(N)/SR;I=np.full(N,.2)
    for c in tl:
        a,b=PROFILE.get(c['key'],(.3,.3));m=(t>=c['start'])&(t<c['end']);u=(t[m]-c['start'])/c['duration'];I[m]=a+(b-a)*u
    return uniform_filter1d(I,size=int(3*SR),mode='nearest')  # 3 s smoothing between scenes
I=intensity_curve()
out=np.zeros((2,N),dtype=np.float64)
def add(sig,start,pan=0.0,gain=1.0):
    i=int(start*SR)
    if i>=N:return
    n=min(len(sig),N-i);l=gain*np.cos((pan+1)*np.pi/4);r=gain*np.sin((pan+1)*np.pi/4);out[0,i:i+n]+=sig[:n]*l;out[1,i:i+n]+=sig[:n]*r
def midi(m):return 440*2**((m-69)/12)
SCALE=[50,51,55,57,58,62,63,67]  # D3 E♭3 G3 A3 B♭3 D4 E♭4 G4 (miyako-bushi-ish)
def pluck(freq,dur=3.0):
    t=np.arange(int(dur*SR))/SR;sig=np.zeros_like(t)
    for h,(amp,dec) in enumerate([(1,1.8),(.55,2.6),(.38,3.5),(.2,4.5),(.12,6),(.07,8)],start=1):
        f=freq*h*(1+.0006*h*h);sig+=amp*np.sin(2*np.pi*f*t)*np.exp(-dec*t)
    n=int(.012*SR);sig[:n]+=rng.normal(0,.35,n)*np.linspace(1,0,n)  # fingernail transient
    return sig*np.minimum(1,t*400)
def pad(freq,dur,att=3.0,rel=4.0):
    t=np.arange(int(dur*SR))/SR;s=np.zeros_like(t)
    for h,a in ((1,1),(2,.5),(3,.3),(4,.15)):
        for det in (-1.2,0,1.3):s+=a*np.sin(2*np.pi*(freq*h+det*h*.15)*t+rng.uniform(0,6.28))
    env=np.minimum(1,t/att)*np.minimum(1,(dur-t)/rel);trem=1+.12*np.sin(2*np.pi*.17*t+rng.uniform(0,6));return s*env*trem/12
def heartbeat():
    t=np.arange(int(.9*SR))/SR;lub=np.sin(2*np.pi*52*t)*np.exp(-t*14);dub=np.zeros_like(t);j=int(.24*SR);dub[j:]=np.sin(2*np.pi*46*t[:-j])*np.exp(-t[:-j]*16)*.7;return lub+dub
def taiko(power=1.0):
    t=np.arange(int(2.2*SR))/SR;f=44+60*np.exp(-t*9);ph=2*np.pi*np.cumsum(f)/SR;s=np.sin(ph)*np.exp(-t*2.6)+.35*rng.normal(0,1,len(t))*np.exp(-t*30)
    return s*power
sos=butter(2,2200,'low',fs=SR,output='sos')
# ---- layers
# 1) drone D2+A2, level follows intensity
t=np.arange(N)/SR;dr=(np.sin(2*np.pi*73.42*t)+.6*np.sin(2*np.pi*110*t+1)+.25*np.sin(2*np.pi*146.8*t))*(.05+.17*I)*(1+.08*np.sin(2*np.pi*.05*t))
out+=dr*np.array([[1.0],[.94]])
# 2) pad chords (D / A / B♭ colours), changes every ~14 s
bars=np.arange(0,TOTAL,14.0);chords=[[50,57],[46,53,57],[48,55],[50,57,62],[46,53],[51,58]]
for k,s0 in enumerate(bars):
    for m in chords[k%len(chords)]:
        lv=.35+.9*I[min(N-1,int((s0+7)*SR))];add(pad(midi(m),min(18,TOTAL-s0+4)),s0,pan=rng.uniform(-.5,.5),gain=lv*.9)
# 3) koto-like plucks: calm=more melodic, tense=sparse; minor-second (E♭) colour grows with intensity
tt=1.0;prev=3
while tt<TOTAL-3:
    i_=I[int(tt*SR)];rate=.55-.32*i_  # events per second
    tt+=rng.exponential(1/max(rate,.12))*(1.0 if i_<.8 else 1.6)
    if tt>=TOTAL-3:break
    step=rng.choice([-2,-1,0,1,1,2]);prev=int(np.clip(prev+step,0,len(SCALE)-1));note=SCALE[prev]+(12 if rng.random()<.25 and i_<.6 else 0)
    if i_>.62 and rng.random()<.3:note=SCALE[rng.integers(0,3)]+(0 if rng.random()<.5 else 12)
    add(pluck(midi(note),3.2),tt,pan=rng.uniform(-.55,.55),gain=.30+.12*rng.random())
    if i_<.45 and rng.random()<.25:add(pluck(midi(note+7 if note+7 in SCALE else note+12),2.6),tt+.18,pan=rng.uniform(-.55,.55),gain=.2)  # echoed pair (calm)
# 4) heartbeat while tense (intensity > .55)
b=2.0
while b<TOTAL-2:
    i_=I[int(b*SR)]
    if i_>.55:add(heartbeat(),b,pan=0,gain=(i_-.5)*1.7)
    b+=60/(54+30*i_)
# 5) taiko hits at story beats
def hits(key,offs,power):
    for c in tl:
        if c['key']==key:
            for o in offs:
                if c['start']+o<TOTAL-3:add(taiko(power),c['start']+o,gain=.9)
hits('hook',[0.0,10.0],1.0);hits('d_depart',[0.0],.8);hits('d_katsura',[c['duration']-3 for c in tl if c['key']=='d_katsura'],.8)
hits('d_attack',[0.0,4.0,8.0,12.0,15.0,18.0,21.0,24.0,27.0,30.0],1.2);hits('d_nijo',[0.0,8.0],.7);hits('e_motive',[0.0],.5)
# 6) quiet wind/noise bed (stronger around the attack)
nz=rng.normal(0,1,N);nz=sosfilt(butter(2,[200,900],'band',fs=SR,output='sos'),nz);out+=nz*(.004+.03*np.clip(I-.5,0,1)**2)*np.array([[1.0],[.9]])
# 7) light reverb on the whole mix (synthetic decaying noise IR)
irn=int(1.8*SR);ir=rng.normal(0,1,irn)*np.exp(-np.arange(irn)/SR*3.2);ir/=np.abs(ir).sum()*.45
wet=np.stack([fftconvolve(out[0],ir)[:N],fftconvolve(out[1],ir[::-1])[:N]]);out=out*.72+wet*.55
# 8) master: fade in/out, low-pass to keep it soft, peak -3 dBFS
fi=int(2.5*SR);fo=int(8*SR);env=np.ones(N);env[:fi]=np.linspace(0,1,fi);env[-fo:]=np.minimum(env[-fo:],np.linspace(1,0,fo)**1.5);out*=env
out=np.stack([sosfilt(sos,out[0]),sosfilt(sos,out[1])]);out*=10**(-3/20)/np.abs(out).max()
pcm=(out.T*32767).astype(np.int16)
p=ROOT/'out'/('hn_bgm.wav' if len(sys.argv)<2 else 'hn_bgm_test.wav')
with wave.open(str(p),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())
rms=np.sqrt(np.mean(out**2));print('wrote',p.name,round(TOTAL),'s  rms dBFS',round(20*np.log10(rms),1),' peak',round(20*np.log10(np.abs(out).max()),1))
