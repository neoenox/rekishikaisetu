"""Dump the reading (kana) VOICEVOX will actually use for every sentence, after the pronunciation dictionary is applied.
Output: out/nj_kana.txt  (scene key / original / kana). Used to catch misreadings (e.g. 大坂->ダイサカ) before synthesis."""
from pathlib import Path
import json,requests
ROOT=Path(__file__).resolve().parents[1];BASE='http://127.0.0.1:50021'
sp=requests.get(BASE+'/speakers',timeout=60).json();spk=next(x for x in sp if x['name']=='四国めたん');style=next(x['id'] for x in spk['styles'] if x['name']=='ノーマル')
dic=json.loads((ROOT/'data'/'nj_pronunciations.json').read_text(encoding='utf8'));sc=json.loads((ROOT/'data'/'nj_scenes.json').read_text(encoding='utf8'))
out=[]
for s in sc:
    for x in [y.strip()+'。' for y in s['narration'].split('。') if y.strip()]:
        sp_=x
        for k,v in sorted(dic.items(),key=lambda z:-len(z[0])):sp_=sp_.replace(k,v)
        q=requests.post(BASE+'/audio_query',params={'text':sp_,'speaker':style},timeout=60).json()
        out.append(f"[{s['key']}] {x}\n    {q['kana']}")
(ROOT/'out'/'nj_kana.txt').write_text('\n'.join(out),encoding='utf8');print(len(out),'sentences')
