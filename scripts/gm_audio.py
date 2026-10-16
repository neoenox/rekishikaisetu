"""VOICEVOX narration, per sentence. Timeline from decoded PCM length."""
from pathlib import Path
import json,wave,hashlib,math,time
import sys,requests,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from hn_text import display   # subtitles use arabic numerals; narration stays in kanji numerals
ROOT=Path(__file__).resolve().parents[1];BASE='http://127.0.0.1:50021';SPEED=0.95
def readwav(p):
    with wave.open(str(p),'rb') as w:return np.frombuffer(w.readframes(w.getnframes()),np.int16),w.getframerate()
def writewav(p,a,rate):
    with wave.open(str(p),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(a.astype(np.int16).tobytes())
def main():
    folder=ROOT/'cache'/'gm_audio';folder.mkdir(exist_ok=True,parents=True)
    sp=requests.get(BASE+'/speakers',timeout=60).json();speaker=next(x for x in sp if x['name']=='四国めたん');style=next(x['id'] for x in speaker['styles'] if x['name']=='ノーマル')
    (folder/'speaker_policy.json').write_text(requests.get(BASE+'/speaker_info',params={'speaker_uuid':speaker['speaker_uuid']},timeout=60).text,encoding='utf8')
    dic=json.loads((ROOT/'data'/'gm_pronunciations.json').read_text(encoding='utf8'));scenes=json.loads((ROOT/'data'/'gm_scenes.json').read_text(encoding='utf8'))
    segs=[];timeline=[];cursor=0;allpcm=[];rate=24000
    for sc in scenes:
        local=[];t=0
        for i,text in enumerate([x.strip()+'。' for x in sc['narration'].split('。') if x.strip()]):
            spoken=text
            for k,v in sorted(dic.items(),key=lambda x:-len(x[0])):spoken=spoken.replace(k,v)
            p=folder/f'{sc["id"]:02}_{i:02}.wav';key=hashlib.sha256((spoken+f'|{SPEED}|1.08|'+str(style)).encode()).hexdigest();meta=p.with_suffix('.json')
            if not p.exists() or not meta.exists() or json.loads(meta.read_text())['key']!=key:
                q=requests.post(BASE+'/audio_query',params={'text':spoken,'speaker':style},timeout=120).json();q.update(speedScale=SPEED,intonationScale=1.08,prePhonemeLength=.15,postPhonemeLength=.35,outputSamplingRate=24000)
                r=requests.post(BASE+'/synthesis',params={'speaker':style},json=q,timeout=180);r.raise_for_status();p.write_bytes(r.content);meta.write_text(json.dumps({'key':key}),encoding='utf8')
            pcm,rate=readwav(p);dur=len(pcm)/rate;rms=float(np.sqrt(np.mean((pcm.astype(float)/32768)**2)));peak=float(np.abs(pcm).max()/32768)
            assert dur>.4 and rms>.003 and peak<.999
            segs.append(dict(scene=sc['id'],text=text,spoken=spoken,start=round(cursor+t,4),end=round(cursor+t+dur,4),duration=dur,rms=rms,peak=peak));local.append(pcm);t+=dur
        sd=math.ceil((t+1.6)*30)/30;j=np.concatenate(local);j=np.pad(j,(0,round(sd*rate)-len(j)));writewav(folder/f'scene_{sc["id"]:02}.wav',j,rate);allpcm.append(j)
        timeline.append({**sc,'start':cursor,'duration':sd,'end':cursor+sd});cursor+=sd;print('scene',sc['id'],round(sd,2),flush=True)
    writewav(ROOT/'out'/'gm_narration.wav',np.concatenate(allpcm),rate)
    st=lambda t:(lambda ms:f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}')(round(t*1000))
    (ROOT/'out'/'gm_subtitles.srt').write_text('\n\n'.join(f'{i+1}\n{st(x["start"])} --> {st(x["end"])}\n{display(x["text"])}' for i,x in enumerate(segs))+'\n',encoding='utf8')
    s0=[x for x in segs if x['scene']==0]
    if len(s0)>=3:timeline[0]['hook_end']=round(s0[2]['end'],2)   # end of the opening hook (3rd sentence); used by hn_compose4
    (ROOT/'data'/'gm_timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=1),encoding='utf8')
    (ROOT/'out'/'gm_audio_report.json').write_text(json.dumps(dict(engine=requests.get(BASE+'/version').json(),speaker='VOICEVOX:四国めたん',style=style,segments=segs,total_seconds=cursor,all_lines_voiced=True,semantic_asr_verified=False),ensure_ascii=False,indent=1),encoding='utf8');print('total',cursor)
if __name__=='__main__':main()
