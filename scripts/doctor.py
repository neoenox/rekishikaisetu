import json,platform,shutil,subprocess,sys,time
from pathlib import Path
import psutil
ROOT=Path(__file__).resolve().parents[1]
def command(args):
    r=subprocess.run(args,capture_output=True,text=True,encoding='utf8',errors='replace');return {'returncode':r.returncode,'output':r.stdout+r.stderr}
def doctor():
    d={'at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'python':sys.version,'platform':platform.platform(),'ram_total':psutil.virtual_memory().total,'disk':{str(p):shutil.disk_usage(p)._asdict() for p in ['C:\\','E:\\']},'gpu':command(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader']),'ffmpeg':command(['ffmpeg','-version'])['output'].splitlines()[0],'node':command(['node','--version'])['output'].strip(),'blender':str(ROOT/'tools'/'blender-4.5.3-windows-x64'/'blender.exe'),'constraints':{'paid':False,'published':False,'requires_human_visual_check':False}}
    (ROOT/'out'/'doctor.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(d,ensure_ascii=False,indent=2))
def monitor():
    out=ROOT/'logs'/'resources.jsonl'
    while not (ROOT/'out'/'monitor.stop').exists():
        processes=[]
        for p in psutil.process_iter(['pid','name','memory_info','cmdline']):
            try:
                if any(x in ' '.join(p.info['cmdline'] or []).lower() for x in ['rekishikaisetu','render_blender','voicevox']):
                    processes.append({'pid':p.pid,'name':p.name(),'rss':p.memory_info().rss,'cpu_seconds':sum(p.cpu_times()[:2])})
            except (psutil.NoSuchProcess,psutil.AccessDenied):pass
        r=command(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'])
        with out.open('a',encoding='utf8') as f:f.write(json.dumps({'epoch':time.time(),'system_ram_used':psutil.virtual_memory().used,'processes':processes,'gpu':r['output'].strip()})+'\n')
        time.sleep(5)
if __name__=='__main__':monitor() if '--monitor' in sys.argv else doctor()
