"""Verify actual encoded media, portrait tracking, credits and layout."""
from pathlib import Path
import json,subprocess,hashlib,itertools,sys
import numpy as np
from PIL import Image
from compose_earth import EarthFilm,F,B
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def run(args):
    p=subprocess.run(args,capture_output=True);assert p.returncode==0,p.stderr.decode(errors='replace');return p.stdout
def intersect(a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
def main():
    composition=load('out/earth_composition_report.json');film=EarthFilm();results=[]
    for filename,expected in [('sekigahara_google_earth_portraits.mp4',film.audio['total_seconds']),('earth_portrait_march_preview.mp4',film.scenes[6]['duration'])]:
        path=ROOT/'out'/filename;meta=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]));v=next(s for s in meta['streams'] if s['codec_type']=='video');a=next(s for s in meta['streams'] if s['codec_type']=='audio')
        assert (v['width'],v['height'],v['r_frame_rate'],v['codec_name'],a['codec_name'])==(1920,1080,'30/1','h264','aac')
        assert abs(float(meta['format']['duration'])-expected)<.08;assert int(v['nb_frames'])==round(expected*30)
        run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'])
        pcm=np.frombuffer(run(['ffmpeg','-v','error','-i',str(path),'-vn','-f','f32le','-ac','1','-ar','24000','pipe:1']),np.float32);peak=float(np.max(np.abs(pcm)));rms=float(np.sqrt(np.mean(pcm**2)));assert .003<rms and peak<.999
        results.append({'file':filename,'all_frames_decoded':True,'frames':int(v['nb_frames']),'duration_seconds':float(meta['format']['duration']),'size_bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'audio_peak':peak,'audio_rms':rms})
    # The compositor asserts card bounds and pairwise non-overlap on every
    # produced frame, not just these saved every-second inspection records.
    for sample in composition['layout_samples']:
        boxes=[c['box'] for c in sample['cards']]
        assert not any(intersect(a,b) for a,b in itertools.combinations(boxes,2))
        if sample['subtitle_box']:assert all(not intersect(box,sample['subtitle_box']) for box in boxes)
        assert sample['on_screen_attribution_present'] and 'Google Earth' in sample['source_text']
    motion=[r for r in composition['layout_samples'] if r['scene']==6]
    assert len(motion)>=20
    anchors=np.array([s['moving_anchor'] for s in motion]);portraits=np.array([s['portrait_center'] for s in motion]);assert np.linalg.norm(anchors[-1]-anchors[0])>200
    assert np.max(np.abs(portraits[:,0]-anchors[:,0]-280))<1e-7
    assert np.max(np.abs(portraits[:,1]-np.minimum(720,anchors[:,1]-25)))<1e-7
    assert film.r['holdout_max_error_px']<2
    # Check that the moving face actually appears at its expected location in
    # the encoded MP4, rather than trusting metadata alone.
    encoded_checks=[];path=ROOT/'out'/'sekigahara_google_earth_portraits.mp4'
    for sample in [motion[3],motion[-4]]:
        i=sample['frame'];out=ROOT/'out'/f'earth_verified_march_{i}.png'
        run(['ffmpeg','-y','-v','error','-ss',str(i/30),'-i',str(path),'-frames:v','1',str(out)])
        im=Image.open(out).convert('RGB');x,y=sample['portrait_center'];left,top=int(x-74),int(y-74);actual=np.asarray(im.crop((left,top,left+148,top+148))).astype(float);icon=np.asarray(film.icons['kobaya']);mask=icon[:,:,3]>250
        mae=float(np.abs(actual-icon[:,:,:3])[mask].mean());assert mae<12,mae
        # The compact required provider attribution survives video encoding.
        ref=np.asarray(film.frame(i).crop((0,1040,1920,1080)).convert('RGB')).astype(float);encoded=np.asarray(im.crop((0,1040,1920,1080))).astype(float);credit_error=float(np.abs(ref-encoded).mean());assert credit_error<12
        encoded_checks.append({'frame':i,'portrait_masked_rgb_mae':mae,'required_attribution_rgb_mae':credit_error,'image':str(out.relative_to(ROOT))})
        # Clean presentation: both formerly opaque bands expose real map pixels.
        for box in [(1700,0,1850,120),(50,1010,400,1030)]:
            pixels=np.asarray(im.crop(box)).astype(float);reference=np.asarray(film.maps['overview'].crop(box).convert('RGB')).astype(float)
            assert pixels.std()>10 and np.abs(pixels-reference).mean()<12,'Opaque band or missing map pixels'
    for s in film.scenes:
        assert B[50].getlength(s['title'])<1832
        assert F[28].getlength(s['category'])<1832
        assert set(s['source_ids'])<={s['id'] for s in load('data/earth_sources.json')}
    for p in film.portraits.values():assert hashlib.sha256((ROOT/p['file']).read_bytes()).hexdigest()==p['sha256']
    for color in ['west','east','kobaya']:
        hashes={hashlib.sha256((ROOT/'assets/army'/f'{color}_{i:02}.png').read_bytes()).hexdigest() for i in range(12)};assert len(hashes)==12
    assert film.audio['all_lines_voiced']
    report={'status':'PASS_FOR_EARTH_AND_PORTRAIT_REVISION','scope':'Requested visual revision only; historical completeness and final artistic acceptance are not claimed','videos':results,'native_resolution':[1920,1080],'fps':30,'all_frame_layout_assertions':composition['frames'],'layout_samples':len(composition['layout_samples']),'registration_output_max_error_px':film.r['holdout_max_error_px']*film.view_scale,'registration_held_out_max_error_px':film.r['holdout_max_error_px'],'encoded_portrait_checks':encoded_checks,'motion_displacement_px':float(np.linalg.norm(anchors[-1]-anchors[0])),'presentation':'full-frame imagery, outlined titles and subtitles, compact required map attribution only','production_credits':'out/video_description.txt','subtitle_px':46,'unit_name_px':38,'header_px':50,'blockers':[],'limitations':['Modern Earth imagery has mixed capture dates; it is not a live image or a reconstruction of1600','Location-registration error does not establish the accuracy of historic army positions','Army symbols are rendered in Blender then composited in2D over Earth footage; no Google3D model was exported','The route is illustrative; troop counts, exact paths and timing are not reconstructed','No independent Japanese ASR or exhaustive semantic OCR verification','Primary historical sources and comprehensive alternative battle chronologies remain future work']}
    (ROOT/'out/earth_quality_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print('PASS: two actual MP4s fully decoded; encoded moving portrait, preserved credits, layout, sources and held-out registration verified')
if __name__=='__main__':main()
