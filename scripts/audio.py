"""Generate each sentence through local VOICEVOX; timing from decoded PCM."""
from pathlib import Path
import json,re,wave,hashlib,time
import requests,numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE='http://127.0.0.1:50021'
def load(name):return json.loads((ROOT/'data'/name).read_text(encoding='utf8'))
def readwav(p):
    with wave.open(str(p),'rb') as w:
        assert w.getsampwidth()==2 and w.getnchannels()==1
        return np.frombuffer(w.readframes(w.getnframes()),np.int16),w.getframerate()
def writewav(p,a,rate):
    with wave.open(str(p),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(a.astype(np.int16).tobytes())
def main():
    folder=ROOT/'cache'/'audio';folder.mkdir(exist_ok=True)
    speakers=requests.get(BASE+'/speakers',timeout=60);speakers.raise_for_status();(folder/'speakers.json').write_text(speakers.text,encoding='utf8')
    speaker=next(x for x in speakers.json() if x['name']=='四国めたん');style=next(x['id'] for x in speaker['styles'] if x['name']=='ノーマル')
    info=requests.get(BASE+'/speaker_info',params={'speaker_uuid':speaker['speaker_uuid']},timeout=60);info.raise_for_status();(folder/'speaker_policy.json').write_text(info.text,encoding='utf8')
    dictionary=load('pronunciations.json');scenes=load('scenes.json');segments=[];timeline=[];cursor=0;allpcm=[];rate=24000;started=time.time()
    for scene in scenes:
        local=[];sub=[];scene_cursor=0
        sentences=[x.strip()+'。' for x in scene['narration'].split('。') if x.strip()]
        for i,text in enumerate(sentences):
            spoken=text
            for name,kana in sorted(dictionary.items(),key=lambda x:-len(x[0])):spoken=spoken.replace(name,kana)
            p=folder/f'{scene["id"]:02}_{i:02}.wav';key=hashlib.sha256((spoken+'|1.03|'+str(style)).encode()).hexdigest();meta=p.with_suffix('.json')
            if not p.exists() or not meta.exists() or json.loads(meta.read_text())['key']!=key:
                q=requests.post(BASE+'/audio_query',params={'text':spoken,'speaker':style},timeout=120);q.raise_for_status();query=q.json();query['speedScale']=1.03;query['prePhonemeLength']=.12;query['postPhonemeLength']=.15;query['outputSamplingRate']=24000
                r=requests.post(BASE+'/synthesis',params={'speaker':style},json=query,timeout=180);r.raise_for_status();p.write_bytes(r.content);meta.write_text(json.dumps({'key':key,'query':query},ensure_ascii=False),encoding='utf8')
            pcm,rate=readwav(p);duration=len(pcm)/rate;peak=float(np.max(np.abs(pcm.astype(float)))/32768);rms=float(np.sqrt(np.mean((pcm.astype(float)/32768)**2)))
            assert duration>.4 and rms>.003 and peak<.999,'audio empty or clipping'
            item=dict(scene=scene['id'],text=text,spoken=spoken,start=round(cursor+scene_cursor,4),end=round(cursor+scene_cursor+duration,4),duration=duration,path=str(p.relative_to(ROOT)),peak=peak,rms=rms,source_ids=scene['source_ids'],category=scene['category'])
            segments.append(item);sub.append(item);local.append(pcm);scene_cursor+=duration
        # One second per scene for a readable transition; never speed-stretch narration.
        local.append(np.zeros(rate,dtype=np.int16));scene_duration=mathceil(scene_cursor+1,30)
        joined=np.concatenate(local);joined=np.pad(joined,(0,round(scene_duration*rate)-len(joined)));writewav(folder/f'scene_{scene["id"]:02}.wav',joined,rate);allpcm.append(joined)
        timeline.append({**scene,'start':cursor,'duration':scene_duration,'end':cursor+scene_duration,'audio':str((folder/f'scene_{scene["id"]:02}.wav').relative_to(ROOT))});cursor+=scene_duration
        print('scene',scene['id'],'seconds',scene_duration,flush=True)
    if cursor<180:
        # Explicit final credit hold, no repeated speech.
        extra=180-cursor;allpcm.append(np.zeros(round(extra*rate),dtype=np.int16));timeline[-1]['duration']+=extra;timeline[-1]['end']+=extra;cursor=180
    assert 180<=cursor<=300,f'Pilot length {cursor} outside range'
    writewav(ROOT/'out'/'narration.wav',np.concatenate(allpcm),rate)
    def stamp(t):
        ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
    (ROOT/'out'/'subtitles.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(x["start"])} --> {stamp(x["end"])}\n{x["text"]}' for i,x in enumerate(segments))+'\n',encoding='utf8')
    report={'engine':requests.get(BASE+'/version').json(),'speaker':'VOICEVOX:四国めたん','style':style,'segments':segments,'total_seconds':cursor,'generation_seconds':time.time()-started,'all_lines_voiced':len(segments)==sum(len([s for s in x['narration'].split('。') if s.strip()]) for x in scenes),'pronunciation_method':'longest-match replacement with checked katakana dictionary before audio_query; original text retained for subtitles','semantic_asr_verified':False}
    (ROOT/'data'/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2),encoding='utf8');(ROOT/'out'/'audio_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print('total',cursor)
def mathceil(value,fps):
    import math
    return math.ceil(value*fps)/fps
if __name__=='__main__':main()
