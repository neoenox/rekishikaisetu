from pathlib import Path
import subprocess,json,time,sys
ROOT=Path(__file__).resolve().parents[1]
def main():
    render=json.loads((ROOT/'cache'/'render_l2_pilot'/'render_report.json').read_text());n=len(render['frames']);edges=[round(i*n/3) for i in range(4)];workers=[];started=time.perf_counter()
    for a,b in zip(edges,edges[1:]):
        p=subprocess.Popen([sys.executable,str(ROOT/'scripts'/'compose.py'),'pilot','2',str(a),str(b)],cwd=ROOT);workers.append((a,b,p))
    for a,b,p in workers:assert p.wait()==0,f'Compose chunk {a}:{b} failed'
    concat=ROOT/'cache'/'pilot_concat.txt';concat.write_text('\n'.join(f"file 'pilot_part_{a}_{b}.mp4'" for a,b,_ in workers)+'\n',encoding='utf8')
    result=subprocess.run(['ffmpeg','-y','-v','warning','-f','concat','-safe','0','-i',str(concat),'-i',str(ROOT/'out'/'narration.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart','-shortest',str(ROOT/'out'/'pilot_3to5min.mp4')]);assert result.returncode==0
    parts=[json.loads((ROOT/'cache'/f'composition_pilot_2_{a}_{b}.json').read_text(encoding='utf8')) for a,b,_ in workers];report=dict(parts[0]);report.update(file='pilot_3to5min.mp4',frame_count=n,duration=n/30,encode_composite_seconds=time.perf_counter()-started,parallel_workers=3,layout_samples=sorted([s for r in parts for s in r['layout_samples']],key=lambda x:x['frame']),omitted_label_instances=sum(r['omitted_label_instances'] for r in parts));report.pop('range_start',None);report.pop('range_end',None)
    (ROOT/'out'/'composition_pilot_2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print('DONE pilot_3to5min.mp4 parallel composition',report['encode_composite_seconds'],flush=True)
if __name__=='__main__':main()
