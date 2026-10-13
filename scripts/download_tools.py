"""Bounded ranged download of the two official portable distributions."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests, time, json
ROOT=Path(__file__).resolve().parents[1]
def download(url,name,size):
    target=ROOT/'tools'/name
    partdir=ROOT/'tools'/(name+'.parts');partdir.mkdir(exist_ok=True)
    step=16*1024*1024
    def one(i):
        a=i*step;b=min(size,a+step)-1;p=partdir/str(i)
        if p.exists() and p.stat().st_size==b-a+1:return
        for attempt in range(4):
            try:
                r=requests.get(url,headers={'Range':f'bytes={a}-{b}'},timeout=180)
                r.raise_for_status()
                assert r.status_code==206 and len(r.content)==b-a+1,(r.status_code,len(r.content))
                p.write_bytes(r.content);print(name,i,'ok',flush=True);return
            except Exception:
                if attempt==3:raise
                time.sleep(2)
    with ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(one,range((size+step-1)//step)))
    with target.open('wb') as f:
        for i in range((size+step-1)//step):f.write((partdir/str(i)).read_bytes())
if __name__=='__main__':
    import sys
    if sys.argv[1]=='blender':download('https://download.blender.org/release/Blender4.5/blender-4.5.3-windows-x64.zip','blender-portable.zip',400100678)
    else:download('https://github.com/VOICEVOX/voicevox_engine/releases/download/0.25.2/voicevox_engine-windows-cpu-0.25.2.7z.001','voicevox-portable.7z',1802304190)
