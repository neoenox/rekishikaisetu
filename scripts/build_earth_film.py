"""Compose the local Earth/portrait revision in three disjoint frame ranges."""
from pathlib import Path
import subprocess,json,sys,time
ROOT=Path(__file__).resolve().parents[1]
def main():
    audio=json.loads((ROOT/'out/earth_audio_report.json').read_text(encoding='utf8'));n=round(audio['total_seconds']*30);edges=[round(i*n/3) for i in range(4)];workers=[];started=time.time()
    for a,b in zip(edges,edges[1:]):workers.append((a,b,subprocess.Popen([sys.executable,str(ROOT/'scripts/compose_earth.py'),str(a),str(b)],cwd=ROOT)))
    for a,b,p in workers:assert p.wait()==0,f'Earth composition {a}:{b} failed'
    concat=ROOT/'cache/earth_concat.txt';concat.write_text('\n'.join(f"file 'earth_part_{a}_{b}.mp4'" for a,b,_ in workers)+'\n',encoding='utf8')
    dest=ROOT/'out/sekigahara_google_earth_portraits.mp4'
    subprocess.run(['ffmpeg','-y','-v','warning','-f','concat','-safe','0','-i',str(concat),'-i',str(ROOT/'out/earth_narration.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest',str(dest)],check=True)
    reports=[json.loads((ROOT/'cache'/f'earth_composition_{a}_{b}.json').read_text(encoding='utf8')) for a,b,_ in workers];r=reports[0];r.update(file=dest.name,frames=n,seconds=n/30,range=[0,n],parallel_workers=3,wall_seconds=time.time()-started,layout_samples=sorted([x for r in reports for x in r['layout_samples']],key=lambda x:x['frame']))
    (ROOT/'out/earth_composition_report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
    timeline=json.loads((ROOT/'data/earth_timeline.json').read_text(encoding='utf8'));scene=timeline[6]
    subprocess.run(['ffmpeg','-y','-v','warning','-ss',str(scene['start']),'-i',str(dest),'-t',str(scene['duration']),'-c:v','h264_nvenc','-cq','19','-preset','p4','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(ROOT/'out/earth_portrait_march_preview.mp4')],check=True)
    print('EARTH FILM AND MARCH PREVIEW READY',n,n/30,flush=True)
if __name__=='__main__':main()
