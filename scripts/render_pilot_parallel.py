"""Three independent Blender processes, disjoint frame ranges, no agents."""
from pathlib import Path
import subprocess,json,time,sys
ROOT=Path(__file__).resolve().parents[1]
def main():
    timeline=json.loads((ROOT/'data'/'timeline.json').read_text(encoding='utf8'));n=round(timeline[-1]['end']*30);boundaries=[round(i*n/3) for i in range(4)];procs=[];started=time.time()
    for a,b in zip(boundaries,boundaries[1:]):
        log=(ROOT/'logs'/f'pilot_{a}_{b}.log').open('wb');args=[str(ROOT/'tools'/'blender-4.5.3-windows-x64'/'blender.exe'),'-b','-t','4','--python',str(ROOT/'scripts'/'render_blender.py'),'--','2','pilot',str(a),str(b)]
        p=subprocess.Popen(args,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT);procs.append((a,b,p,log));print('started',a,b,'pid',p.pid,flush=True)
    for a,b,p,log in procs:
        assert p.wait()==0,f'Blender chunk {a}:{b} failed; inspect log';log.close()
    folder=ROOT/'cache'/'render_l2_pilot';chunks=[json.loads((folder/f'render_report_{a}_{b}.json').read_text()) for a,b,_,_ in procs];result=dict(chunks[0]);result['frames']=sorted([frame for c in chunks for frame in c['frames']],key=lambda x:x['frame']);assert [f['frame'] for f in result['frames']]==list(range(n))
    result['max_foot_contact_error_m']=max(c['max_foot_contact_error_m'] for c in chunks);result['total_render_seconds']=sum(c['total_render_seconds'] for c in chunks);result['wall_clock_render_seconds']=time.time()-started;result['parallel_workers']=3;result['worker_ranges']=[c['worker_range'] for c in chunks];result['epoch_finished']=time.time();result.pop('worker_range',None)
    (folder/'render_report.json').write_text(json.dumps(result,indent=2),encoding='utf8');print('pilot rendered',n,'frames, wall seconds',result['wall_clock_render_seconds'],flush=True)
if __name__=='__main__':main()
